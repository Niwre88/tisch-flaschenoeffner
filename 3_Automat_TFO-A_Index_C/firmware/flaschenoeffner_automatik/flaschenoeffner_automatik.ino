// ============================================================================
//  Flaschenöffner-Automat TFO-A (Index C, Greifkopf) – Ablaufsteuerung für ESP32
//
//  Bedienkonzept (Ausgabeautomat):
//    "Öffnen"  nächste verschlossene Flasche zur Station, von oben öffnen,
//              Kronkorken abwerfen, geöffnete Flasche ins Bedienfach fahren.
//    "Laden"   nächste leere Tasche ins Bedienfach fahren (zum Befüllen).
//    Bedienfach: Klappe öffnen (Antriebe stromlos über -K1/-K2), Flasche entnehmen
//              oder einsetzen, Klappe schließen -> Belegung wird über -B7 erfasst.
//
//  Schrittkette je Flasche:
//    S1 Takten      Sternrad: volle Tasche in die Station, -B6 prüfen
//    S2 Antasten    Z ab bis -B3 (Tastleiste berührt), unterste Lage -> kein Kronkorken
//    S3 Prüfen      -B8 meldet Metall -> Kronkorken vorhanden (sonst ohne Öffnen ausgeben)
//    S4 Greifen     Servo -M5 schließt die Backen (Lippe unter den Rand)
//    S5 Kippen      Servo -M6 kippt die Schwinge 25° (Kronkorken springt ab)
//    S6 Hoch        Backen nachgreifen, Z in Abwurfhöhe
//    S7 Zurück      Schwinge 0° bis -B10, -B8 muss den Kronkorken im Greifer melden
//    S8 Rinne ein   Servo -M4 schwenkt die Fangrinne unter den Greifer
//    S9 Abwurf      Backen auf, -B11 muss den Kronkorken melden
//    S10 Rinne aus  Fangrinne in Parkstellung
//    S11 Ausgabe    Sternrad 4 Taschen weiter ins Bedienfach, Fachlicht an
//
//  Hardware : ESP32-DevKit, MCP23017 (16 Eingänge über Optokoppler), 2× TMC2209
//             (Standalone, 1/8), 3 Servos (-M4 270°, -M5, -M6), MOSFET-Platine -A6
//             für Fachlicht, Signalsäule und Leuchtmelder.
//  Software : Arduino-Core ESP32 ab 3.0, Bibliothek FastAccelStepper (gin66),
//             optional SinricPro. Wire, WebServer und Preferences sind im Core enthalten.
//
//  SICHERHEIT: Not-Halt (-K1, manueller Start mit -S4) sowie Bedienklappe und
//  Servicedeckel (-K2, Autostart) schalten zweikanalig die 24-V-Leistung ab
//  (Schrittmotoren und Servo-Wandler). Nach dem Schließen startet das Programm
//  keine Bewegung von selbst. Dieses Programm ist KEINE Sicherheitssteuerung.
//  STATUS: ungetestet (ohne Hardware geschrieben, nicht kompiliert).
// ============================================================================
#include <Wire.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <Preferences.h>
#include "FastAccelStepper.h"
#include "konfiguration.h"
#include "zugang.h"            // aus zugang_beispiel.h anlegen (nicht im Repository)
#if ALEXA_AKTIV
#include <SinricPro.h>
#include <SinricProSwitch.h>
#endif

// ---------------------------------------------------------------- Eingänge (MCP23017)
uint16_t roh = 0, stabil = 0, flankeAuf = 0;
uint32_t seit[ANZAHL_EINGAENGE];

uint16_t mcpLesen() {
  Wire.beginTransmission(MCP_ADRESSE); Wire.write(0x12); Wire.endTransmission();   // GPIOA
  Wire.requestFrom((int)MCP_ADRESSE, 2);
  uint16_t a = Wire.read(), b = Wire.read();
  return a | (b << 8);
}
void mcpRegister(uint8_t reg, uint8_t a, uint8_t b) {      // A und B nacheinander (Adressen fortlaufend)
  Wire.beginTransmission(MCP_ADRESSE); Wire.write(reg); Wire.write(a); Wire.write(b); Wire.endTransmission();
}
void mcpStart() {
  Wire.begin(PIN_SDA, PIN_SCL, 400000);
  mcpRegister(0x00, 0xFF, 0xFF);   // IODIR: alle 16 Pins Eingang
  mcpRegister(0x0C, 0xFF, 0xFF);   // GPPU: interne Pull-ups (Optokoppler-Transistor zieht gegen GND)
  mcpRegister(0x02, 0xFF, 0xFF);   // IPOL: invertieren -> Signal aktiv = Bit 1
}
void eingaengeLesen() {
  uint16_t r = mcpLesen();
  uint32_t jetzt = millis();
  flankeAuf = 0;
  for (int i = 0; i < ANZAHL_EINGAENGE; i++) {
    bool bit = r & (1 << i);
    if (bit != (bool)(roh & (1 << i))) seit[i] = jetzt;
    if (bit != (bool)(stabil & (1 << i)) && jetzt - seit[i] >= T_ENTPRELL) {
      if (bit) { stabil |= (1 << i); flankeAuf |= (1 << i); } else stabil &= ~(1 << i);
    }
  }
  roh = r;
}
inline bool ein(Eingang e) { return stabil & (1 << e); }
inline bool auf(Eingang e) { return flankeAuf & (1 << e); }

// ---------------------------------------------------------------- Taschenbelegung (überdauert Stromausfall)
enum Belegung : uint8_t { LEER = 0, VOLL = 1, OFFEN = 2, UNBEKANNT = 3 };
const char* BELEGNAME[] = {"leer", "voll", "offen", "?"};
Belegung tasche[TASCHEN];
Preferences speicher;
void belegungSichern() { speicher.putBytes("tasche", tasche, sizeof(tasche)); }

// ---------------------------------------------------------------- Zustände
enum Zustand {
  Z_INIT, Z_REF_Z, Z_REF_STERN, Z_BEREIT,
  S1_TAKTEN, S2_ANTASTEN, S3_PRUEFEN, S4_GREIFEN, S5_KIPPEN, S6_HOCH, S7_ZURUECKKIPPEN,
  S8_RINNE_EIN, S9_ABWURF, S10_RINNE_AUS, S11_AUSGABE,
  L1_LADEN, Z_FLASCHE_BEREIT, Z_STOERUNG, Z_SCHUTZ_OFFEN
};
const char* ZUSTANDSNAME[] = {
  "Init", "Referenz Z", "Referenz Sternrad", "Bereit",
  "S1 Takten", "S2 Antasten", "S3 Kronkorken prüfen", "S4 Greifen", "S5 Kippen", "S6 Kopf hoch",
  "S7 Zurückkippen", "S8 Fangrinne ein", "S9 Abwurf", "S10 Fangrinne aus", "S11 Ausgabe ins Fach",
  "Laden: leere Tasche ins Fach", "Flasche im Fach bereit", "Störung", "Klappe/Deckel offen oder Not-Halt"
};
Zustand zustand = Z_INIT;
uint32_t schrittStart = 0;
int aktiv = -1;                    // bearbeitete Tasche
bool hatteKronkorken = false;
uint32_t geoeffnetGesamt = 0, kronkorkenGesamt = 0;
String meldung = "", stoerung = "";
bool anfOeffnen = false, anfLaden = false, anfReset = false, anfStopp = false;
bool referenziert = false;
bool antastLangsam = false;
float letzterKontaktMm = 0;        // zuletzt ertastete Höhe (gleiche Sorte -> kurzer Antastweg)

FastAccelStepperEngine engine;
FastAccelStepper *zAchse = nullptr, *stern = nullptr;
WebServer server(80);

// ---------------------------------------------------------------- Hilfen
long zSchritte(float mm) { return lround((mm - Z_REFERENZ_MM) * Z_SCHRITTE_PRO_MM); }
float zMm() { return Z_REFERENZ_MM + zAchse->getCurrentPosition() / Z_SCHRITTE_PRO_MM; }
uint32_t imSchritt() { return millis() - schrittStart; }
void weiter(Zustand z) { zustand = z; schrittStart = millis(); Serial.printf("[%8lu] -> %s\n", millis(), ZUSTANDSNAME[z]); }
void treiber(bool an) { digitalWrite(PIN_TREIBER_EN, an ? LOW : HIGH); }
// Servo: 0,5 … 2,5 ms über den Winkelbereich des Servos (14 Bit bei 50 Hz)
void servoGrad(int pin, int grad, int bereich = SERVO_BEREICH_STANDARD) {
  grad = constrain(grad, 0, bereich);
  ledcWrite(pin, (500 + (uint32_t)grad * 2000 / bereich) * 16383UL / 20000UL);
}
void backen(int g) { servoGrad(PIN_SERVO_BACKEN, g); }
void rinne(int g) { servoGrad(PIN_SERVO_RINNE, g, SERVO_BEREICH_RINNE); }
int kippIst = KIPP_GRUND_GRAD, kippZiel = KIPP_GRUND_GRAD;   // Kippen wird in kleinen Schritten gefahren
void kippen(int g) { kippZiel = g; }
void kippFuehren() {                                          // aus loop(): ca. 1° je 15 ms
  static uint32_t t = 0;
  if (kippIst == kippZiel || millis() - t < 15) return;
  t = millis(); kippIst += (kippZiel > kippIst) ? 1 : -1;
  servoGrad(PIN_SERVO_KIPPEN, kippIst);
}
void alleStopp() { if (zAchse) zAchse->forceStop(); if (stern) stern->forceStop(); }
void stoeren(const String& t) { alleStopp(); stoerung = t; weiter(Z_STOERUNG); }
void zFahren(float mm, uint32_t hz = Z_FAHRT_HZ) { zAchse->setSpeedInHz(hz); zAchse->moveTo(zSchritte(mm)); }

// Sternrad: Position 0 = Tasche 0 in der Station. Drehung nur im Uhrzeigersinn (negativ).
long sternLage() { return ((stern->getCurrentPosition() % STERN_SCHRITTE_U) + STERN_SCHRITTE_U) % STERN_SCHRITTE_U; }
long stationsLage(int i) { return ((-(long)i * STERN_TAKT) % STERN_SCHRITTE_U + STERN_SCHRITTE_U) % STERN_SCHRITTE_U; }
long fachLage(int i) { return ((stationsLage(i) - FACH_ABSTAND * STERN_TAKT) % STERN_SCHRITTE_U + STERN_SCHRITTE_U) % STERN_SCHRITTE_U; }
long wegUhrzeiger(long ziel) { return ((sternLage() - ziel) % STERN_SCHRITTE_U + STERN_SCHRITTE_U) % STERN_SCHRITTE_U; }
void sternUm(long schritte, uint32_t hz) { stern->setSpeedInHz(hz); stern->move(-schritte); }
int tascheImFach() {
  for (int i = 0; i < TASCHEN; i++) if (wegUhrzeiger(fachLage(i)) == 0) return i;
  return -1;
}

int naechsteZumOeffnen() {         // volle oder unbekannte Tasche mit dem kürzesten Weg zur Station
  int best = -1; long bw = 1L << 30;
  for (int i = 0; i < TASCHEN; i++) if (tasche[i] == VOLL || tasche[i] == UNBEKANNT) {
    long w = wegUhrzeiger(stationsLage(i));
    if (w < bw) { bw = w; best = i; }
  }
  return best;
}
int offeneTasche() {               // geöffnete Flasche, die noch nicht im Fach steht (z. B. nach Stopp)
  for (int i = 0; i < TASCHEN; i++) if (tasche[i] == OFFEN) return i;
  return -1;
}
bool lagePlausibel() {             // in jeder Taktlage muss -B4 genau bei Tasche 1 in der Station melden
  return (sternLage() == 0) == ein(E_STERN_REF);
}
int naechsteLeereZumFach() {
  int best = -1; long bw = 1L << 30;
  for (int i = 0; i < TASCHEN; i++) if (tasche[i] == LEER) { long w = wegUhrzeiger(fachLage(i)); if (w < bw) { bw = w; best = i; } }
  return best;
}

// ---------------------------------------------------------------- Signalsäule und Leuchtmelder
void anzeigen() {
  bool blink = (millis() / 400) % 2;
  bool gruen = false, gelb = meldung.length() > 0, rot = false, ledO = false, ledL = false, licht = false;
  switch (zustand) {
    case Z_BEREIT:         gruen = true; ledO = naechsteZumOeffnen() >= 0; ledL = naechsteLeereZumFach() >= 0; break;
    case Z_FLASCHE_BEREIT: gruen = blink; licht = true; break;
    case L1_LADEN:         ledL = blink; licht = true; break;
    case Z_STOERUNG:       rot = blink; break;
    case Z_SCHUTZ_OFFEN:   rot = true; licht = true; break;
    case Z_INIT: case Z_REF_Z: case Z_REF_STERN: gelb = blink; break;
    default:               gruen = true; break;
  }
  digitalWrite(PIN_GRUEN, gruen); digitalWrite(PIN_GELB, gelb); digitalWrite(PIN_ROT, rot);
  digitalWrite(PIN_LED_OEFFNEN, ledO); digitalWrite(PIN_LED_LADEN, ledL); digitalWrite(PIN_FACHLICHT, licht);
}

// ---------------------------------------------------------------- Bedienfach auswerten (Klappe geschlossen)
void fachErfassen() {
  int i = tascheImFach();
  if (i < 0) return;
  bool da = ein(E_FLASCHE_FACH);
  Belegung alt = tasche[i];
  if (!da) tasche[i] = LEER;                         // entnommen oder leer geblieben
  else if (alt == LEER || alt == UNBEKANNT) tasche[i] = VOLL;   // neu eingesetzt
  if (tasche[i] != alt) { belegungSichern(); Serial.printf("Tasche %d: %s -> %s\n", i + 1, BELEGNAME[alt], BELEGNAME[tasche[i]]); }
}

// ---------------------------------------------------------------- Schrittkette
void schrittkette() {
  bool reset = anfReset; anfReset = false;
  if (!ein(E_SICHER_OK) && zustand != Z_SCHUTZ_OFFEN) {   // Leistung ist bereits hart abgeschaltet
    alleStopp();
    if (zustand >= S1_TAKTEN && zustand <= S11_AUSGABE) referenziert = false;   // Lage unsicher
    weiter(Z_SCHUTZ_OFFEN); return;
  }
  if (anfStopp && zustand >= S1_TAKTEN && zustand <= L1_LADEN) { anfStopp = false; stoeren("Stopp durch Bediener"); return; }
  anfStopp = false;

  switch (zustand) {
    case Z_INIT:                                              // erst Greifer sichern, dann fahren
      treiber(true); backen(BACKEN_AUF_GRAD); kippen(KIPP_GRUND_GRAD); rinne(RINNE_PARK_GRAD);
      zAchse->setSpeedInHz(Z_FAHRT_HZ / 2); zAchse->runForward();
      weiter(Z_REF_Z); break;

    case Z_REF_Z:
      if (ein(E_Z_REF)) {
        zAchse->forceStop(); zAchse->setCurrentPosition(zSchritte(Z_REFERENZ_MM));
        zFahren(Z_SICHER_MM);
        stern->setSpeedInHz(STERN_HZ / 4); stern->runBackward();       // im Uhrzeigersinn
        weiter(Z_REF_STERN);
      } else if (imSchritt() > T_MAX_REFERENZ) stoeren("Referenz Z nicht gefunden");
      break;

    case Z_REF_STERN:
      if (ein(E_STERN_REF)) {
        stern->forceStop(); stern->setCurrentPosition(0);
        if (!ein(E_KIPP_GRUND)) { stoeren("Greiferschwinge nicht in Grundstellung (-B10)"); break; }
        referenziert = true; weiter(Z_BEREIT);
      } else if (imSchritt() > T_MAX_REFERENZ) stoeren("Referenz Sternrad nicht gefunden");
      break;

    case Z_BEREIT:
      if (stern->isRunning() || zAchse->isRunning()) break;   // Restbewegung abwarten
      if (anfOeffnen) {
        anfOeffnen = false; meldung = "";
        int f = tascheImFach();
        if (f >= 0 && tasche[f] == OFFEN) { meldung = "Bitte zuerst die geöffnete Flasche entnehmen"; break; }
        int o = offeneTasche();
        if (o >= 0) {                                        // erst die schon geöffnete Flasche ausgeben
          aktiv = o; sternUm(wegUhrzeiger(fachLage(o)), STERN_HZ); weiter(S11_AUSGABE); break;
        }
        if (!ein(E_SCHUBLADE_DA)) { meldung = "Kronkorken-Schublade fehlt"; break; }
        if (ein(E_SCHUBLADE_VOLL)) { meldung = "Kronkorken-Schublade voll – bitte leeren"; break; }
        aktiv = naechsteZumOeffnen();
        if (aktiv < 0) { meldung = "Magazin leer – bitte laden"; break; }
        sternUm(wegUhrzeiger(stationsLage(aktiv)), STERN_HZ);   // Kopf steht in Abwurfhöhe über allen Flaschen
        weiter(S1_TAKTEN);
      } else if (anfLaden) {
        anfLaden = false; meldung = "";
        int f = tascheImFach();
        if (f >= 0 && tasche[f] == OFFEN) { meldung = "Bitte zuerst die geöffnete Flasche entnehmen"; break; }
        int i = naechsteLeereZumFach();
        if (i < 0) { meldung = "Keine leere Tasche"; break; }
        aktiv = i; sternUm(wegUhrzeiger(fachLage(i)), STERN_HZ);
        weiter(L1_LADEN);
      }
      break;

    case S1_TAKTEN:
      if (!stern->isRunning() && imSchritt() > 50) {
        if (!ein(E_FLASCHE_STATION)) {                       // Tasche doch leer
          tasche[aktiv] = LEER; belegungSichern(); weiter(Z_BEREIT); anfOeffnen = true;   // nächste versuchen
        } else {                                             // Eilgang bis kurz über die zuletzt ertastete Höhe
          antastLangsam = false;
          zFahren(letzterKontaktMm > 0 ? min(Z_SICHER_MM, letzterKontaktMm + Z_VORLAUF_MM) : Z_SICHER_MM);
          weiter(S2_ANTASTEN);
        }
      } else if (imSchritt() > T_MAX_FAHRT) stoeren("Sternrad erreicht Position nicht");
      break;

    case S2_ANTASTEN:
      if (ein(E_TASTLEISTE)) {                                // Tastleiste federt bis 6 mm ein -> Sofortstopp zulässig
        zAchse->forceStop(); letzterKontaktMm = zMm(); weiter(S3_PRUEFEN);
      } else if (!zAchse->isRunning() && !antastLangsam) {   // Eilgang beendet -> langsam weiter
        antastLangsam = true; zFahren(Z_MIN_MM, Z_ANTAST_HZ);
      } else if (!zAchse->isRunning()) {                     // unten ohne Kontakt
        hatteKronkorken = false; letzterKontaktMm = 0;
        meldung = "Tasche " + String(aktiv + 1) + ": keine Flasche/kein Kronkorken ertastet";
        zFahren(Z_SICHER_MM); weiter(S6_HOCH);
      }
      break;

    case S3_PRUEFEN:                                          // Metall unter der Tastleiste?
      if (!zAchse->isRunning() && imSchritt() > 100) {
        hatteKronkorken = ein(E_KRONKORKEN);
        if (hatteKronkorken) { backen(BACKEN_ZU_GRAD); weiter(S4_GREIFEN); }
        else {                                                // schon offen / Bügelverschluss: nicht greifen
          meldung = "Tasche " + String(aktiv + 1) + ": kein Kronkorken – Flasche wird ohne Öffnen ausgegeben";
          zFahren(Z_SICHER_MM); weiter(S6_HOCH);
        }
      }
      break;

    case S4_GREIFEN:
      if (imSchritt() >= T_GREIFEN) { kippen(KIPP_AB_GRAD); weiter(S5_KIPPEN); }
      break;

    case S5_KIPPEN:
      if (imSchritt() >= T_KIPPEN && kippIst == kippZiel) {
        backen(BACKEN_FEST_GRAD); zFahren(Z_SICHER_MM); weiter(S6_HOCH);   // gekippt nach oben fahren
      }
      break;

    case S6_HOCH:
      if (!zAchse->isRunning() && !stern->isRunning()) {
        if (hatteKronkorken) { kippen(KIPP_GRUND_GRAD); weiter(S7_ZURUECKKIPPEN); }
        else { tasche[aktiv] = OFFEN; belegungSichern(); sternUm(FACH_ABSTAND * STERN_TAKT, STERN_HZ); weiter(S11_AUSGABE); }
      } else if (imSchritt() > T_MAX_FAHRT) stoeren("Z-Achse erreicht die Abwurfhöhe nicht");
      break;

    case S7_ZURUECKKIPPEN:
      if (kippIst == kippZiel && ein(E_KIPP_GRUND) && imSchritt() > 200) {
        if (!ein(E_KRONKORKEN)) meldung = "Kronkorken nach dem Kippen nicht im Greifer – Station prüfen";
        rinne(RINNE_ARBEIT_GRAD); weiter(S8_RINNE_EIN);
      } else if (imSchritt() > T_KIPP_ZURUECK + T_KIPPEN) stoeren("Greiferschwinge nicht in Grundstellung (-B10)");
      break;

    case S8_RINNE_EIN:
      if (imSchritt() >= T_RINNE) { backen(BACKEN_AUF_GRAD); weiter(S9_ABWURF); }
      break;

    case S9_ABWURF:
      if (auf(E_KK_RUTSCHE)) { kronkorkenGesamt++; rinne(RINNE_PARK_GRAD); weiter(S10_RINNE_AUS); }
      else if (imSchritt() > T_ABWURF) {
        meldung = "Kronkorken nicht in der Rutsche erkannt – Greifer/Rinne prüfen";
        rinne(RINNE_PARK_GRAD); weiter(S10_RINNE_AUS);
      }
      break;

    case S10_RINNE_AUS:
      if (imSchritt() >= T_RINNE) {
        tasche[aktiv] = OFFEN; geoeffnetGesamt++; belegungSichern();
        sternUm(FACH_ABSTAND * STERN_TAKT, STERN_HZ); weiter(S11_AUSGABE);
      }
      break;

    case S11_AUSGABE:
      if (!stern->isRunning() && imSchritt() > 50) {
        if (!lagePlausibel()) { referenziert = false; stoeren("Sternrad verdreht – Reset für neue Referenzfahrt"); }
        else weiter(Z_FLASCHE_BEREIT);
      } else if (imSchritt() > T_MAX_FAHRT) stoeren("Ausgabe ins Fach nicht erreicht");
      break;

    case L1_LADEN:
      if (!stern->isRunning() && imSchritt() > 50) {
        if (!lagePlausibel()) { referenziert = false; stoeren("Sternrad verdreht – Reset für neue Referenzfahrt"); break; }
        meldung = "Tasche " + String(aktiv + 1) + " im Fach: Klappe öffnen und Flasche einsetzen"; weiter(Z_BEREIT);
      } else if (imSchritt() > T_MAX_FAHRT) stoeren("Sternrad erreicht das Fach nicht");
      break;

    case Z_FLASCHE_BEREIT:                                    // wartet, bis die Klappe geöffnet wird (-> Z_SCHUTZ_OFFEN)
      if (anfOeffnen || anfLaden) { anfOeffnen = anfLaden = false; meldung = "Bitte zuerst die geöffnete Flasche entnehmen"; }
      break;

    case Z_STOERUNG:
      if (reset) { stoerung = ""; weiter(referenziert ? Z_BEREIT : Z_INIT); }
      break;

    case Z_SCHUTZ_OFFEN:                                      // Klappe/Deckel offen: Bediener entnimmt oder lädt
      // Nach dem Schließen bewegt sich nichts von selbst: Bewegung erst auf "Öffnen"/"Laden".
      // War eine Bewegung unterbrochen (nicht referenziert), startet die Referenzfahrt nur mit Reset.
      if (ein(E_SICHER_OK) && ein(E_KLAPPE_ZU) && imSchritt() > 300) {
        if (referenziert) { treiber(true); fachErfassen(); stoerung = ""; meldung = ""; weiter(Z_BEREIT); }
        else if (reset) { stoerung = ""; meldung = ""; weiter(Z_INIT); }
        else stoerung = "Bewegung unterbrochen – Reset drücken (Referenzfahrt)";
      }
      break;
  }
}

// ---------------------------------------------------------------- Weboberfläche
const char SEITE[] PROGMEM = R"HTML(<!doctype html><html lang="de"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Flaschenöffner</title>
<style>body{font-family:system-ui,sans-serif;margin:16px;max-width:560px}button{font-size:18px;padding:10px 16px;
margin:4px;border-radius:8px;border:1px solid #888}td{padding:3px 8px}#z{font-size:22px;font-weight:600}
.t{display:inline-block;width:56px;text-align:center;border:1px solid #888;border-radius:6px;margin:2px;padding:4px 0}</style>
<h2>Flaschenöffner-Automat</h2><div id="z">…</div><p id="m"></p><div id="b"></div>
<button onclick="f('oeffnen')">Öffnen</button><button onclick="f('laden')">Laden</button>
<button onclick="f('stopp')">Stopp</button><button onclick="f('reset')">Reset</button><table id="t"></table>
<script>
function f(c){fetch('/'+c,{method:'POST'}).then(l)}
function l(){fetch('/status').then(r=>r.json()).then(s=>{z.textContent=s.zustand;m.textContent=(s.stoerung||'')+' '+(s.meldung||'');
b.innerHTML=s.taschen.map((x,i)=>'<span class=t>'+(i+1)+'<br>'+x+'</span>').join('');
t.innerHTML=Object.entries(s.werte).map(([k,v])=>'<tr><td>'+k+'</td><td>'+v+'</td></tr>').join('')})}
setInterval(l,500);l();</script></html>)HTML";

void webEinrichten() {
  server.on("/", [] { server.send_P(200, "text/html", SEITE); });
  server.on("/status", [] {
    String t = "[";
    for (int i = 0; i < TASCHEN; i++) { t += "\"" + String(BELEGNAME[tasche[i]]) + "\""; if (i < TASCHEN - 1) t += ","; }
    t += "]";
    String j = "{\"zustand\":\"" + String(ZUSTANDSNAME[zustand]) + "\",\"stoerung\":\"" + stoerung + "\",\"meldung\":\"" + meldung +
               "\",\"taschen\":" + t + ",\"werte\":{\"Geöffnet gesamt\":" + String(geoeffnetGesamt) +
               ",\"Kronkorken gesamt\":" + String(kronkorkenGesamt) + ",\"Z-Achse\":\"" + String(zMm(), 1) + " mm\"" +
               ",\"Schublade\":\"" + String(!ein(E_SCHUBLADE_DA) ? "fehlt" : ein(E_SCHUBLADE_VOLL) ? "voll" : "bereit") + "\"" +
               ",\"Klappe/Deckel/Not-Halt\":\"" + String(ein(E_SICHER_OK) ? "geschlossen" : "offen") + "\"}}";
    server.send(200, "application/json", j);
  });
  server.on("/oeffnen", HTTP_POST, [] { anfOeffnen = true; server.send(204); });
  server.on("/laden", HTTP_POST, [] { anfLaden = true; server.send(204); });
  server.on("/stopp", HTTP_POST, [] { anfStopp = true; server.send(204); });
  server.on("/reset", HTTP_POST, [] { anfReset = true; server.send(204); });
  server.begin();
}

#if ALEXA_AKTIV
bool alexaSchalten(const String& id, bool& an) { if (an) anfOeffnen = true; return true; }   // "Alexa, Bier öffnen"
#endif

// ---------------------------------------------------------------- setup / loop
void setup() {
  Serial.begin(115200);
  for (int p : {PIN_TREIBER_EN, PIN_FACHLICHT, PIN_GRUEN, PIN_GELB, PIN_ROT,
                PIN_LED_OEFFNEN, PIN_LED_LADEN}) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
  treiber(false);
  for (int p : {PIN_SERVO_BACKEN, PIN_SERVO_KIPPEN, PIN_SERVO_RINNE}) ledcAttach(p, 50, 14);
  backen(BACKEN_AUF_GRAD); servoGrad(PIN_SERVO_KIPPEN, KIPP_GRUND_GRAD); rinne(RINNE_PARK_GRAD);
  mcpStart();
  speicher.begin("tfo-a-c", false);
  if (speicher.getBytes("tasche", tasche, sizeof(tasche)) != sizeof(tasche))
    for (int i = 0; i < TASCHEN; i++) tasche[i] = UNBEKANNT;
  engine.init();
  zAchse = engine.stepperConnectToPin(PIN_Z_STEP);
  stern = engine.stepperConnectToPin(PIN_S_STEP);
  if (!zAchse || !stern) { Serial.println("Schrittmotoren nicht verfügbar"); while (true) delay(1000); }
  zAchse->setDirectionPin(PIN_Z_DIR); stern->setDirectionPin(PIN_S_DIR);
  zAchse->setAcceleration(Z_BESCHL); stern->setAcceleration(STERN_BESCHL);
  WiFi.mode(WIFI_STA); WiFi.setHostname(GERAETENAME); WiFi.begin(WLAN_SSID, WLAN_PASS);
  MDNS.begin(GERAETENAME);
  webEinrichten();
#if ALEXA_AKTIV
  SinricProSwitch& sw = SinricPro[SINRIC_SWITCH_ID]; sw.onPowerState(alexaSchalten);
  SinricPro.begin(SINRIC_APP_KEY, SINRIC_APP_SECRET);
#endif
  eingaengeLesen(); stabil = roh;
  weiter(ein(E_SICHER_OK) ? Z_INIT : Z_SCHUTZ_OFFEN);
}

void loop() {
  eingaengeLesen();
  if (auf(E_OEFFNEN)) anfOeffnen = true;
  if (auf(E_LADEN)) anfLaden = true;
  if (auf(E_RESET)) anfReset = true;
  if (!ein(E_STOPP)) anfStopp = true;                  // Stopptaster ist ein Öffner
  schrittkette();
  kippFuehren();
  anzeigen();
  server.handleClient();
#if ALEXA_AKTIV
  SinricPro.handle();
#endif
}
