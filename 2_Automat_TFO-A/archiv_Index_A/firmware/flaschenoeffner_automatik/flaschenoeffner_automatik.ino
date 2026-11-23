// ============================================================================
//  Flaschenöffner Automatik TFO-A – Ablaufsteuerung für ESP32
//
//  Hardware : ESP32-DevKit (WROOM-32), 2× TMC2209 (Standalone, 1/8 Schritt),
//             H-Brücke für Linearantrieb 24 V, Servo 6 V, 24-V-Sensorik über
//             Optokoppler, Signalsäule über Relais.
//  Software : Arduino-Core für ESP32 ab 3.0, Bibliothek FastAccelStepper
//             (gin66/FastAccelStepper), optional SinricPro (Alexa).
//
//  WICHTIG – Sicherheit: Haube (Türschalter) und Not-Halt wirken über ein
//  Sicherheitsrelais direkt auf die Leistungsversorgung der Antriebe. Dieses
//  Programm ist KEINE Sicherheitssteuerung. Es liest die Rückmeldung des
//  Sicherheitsrelais nur, um den Ablauf sauber anzuhalten.
//
//  Schrittkette (je Flasche):
//    S1 Sternrad taktet in die Vorposition (3 mm vor der Station)
//    S2 Z-Achse tastet ab, bis der Magnetstempel den Kronkorken berührt
//    S3 Sternrad fährt die letzten 3 mm (Kronkorkenrand gleitet über die Lippe)
//    S4 Linearantrieb hebelt den Kronkorken ab
//    S5 Hebel zurück in Grundstellung, Kronkorken haftet am Magnet
//    S6 Kopf fährt in sichere Höhe
//    S7 Servo schiebt den Kronkorken in den Trichter
//    S8 Gabellichtschranke bestätigt den Kronkorken
//    S9 Behälter prüfen, nächste Tasche
//
//  Status ungetestet: Das Programm ist für die Konstruktion TFO-A geschrieben,
//  aber noch nicht auf echter Hardware in Betrieb genommen.
// ============================================================================
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include "FastAccelStepper.h"
#include "konfiguration.h"
#include "zugang.h"            // aus zugang_beispiel.h anlegen (nicht im Repository)
#if ALEXA_AKTIV
#include <SinricPro.h>
#include <SinricProSwitch.h>
#endif

// ---------------------------------------------------------------- Eingänge
struct Eingang {
  int pin;
  bool invertiert;
  bool zustand = false, roh = false, flanke = false;
  uint32_t seit = 0;
  void lesen() {
    bool r = digitalRead(pin) ^ invertiert;
    if (r != roh) { roh = r; seit = millis(); }
    flanke = false;
    if (roh != zustand && millis() - seit >= T_ENTPRELL) { zustand = roh; flanke = zustand; }
  }
};

Eingang eStart{PIN_START, false}, eStopp{PIN_STOP, true}, eReset{PIN_RESET, false},
        eSicher{PIN_SICHERHEIT_OK, false}, eZRef{PIN_Z_REFERENZ, false},
        eStempel{PIN_STEMPEL, false}, eSternRef{PIN_STERN_REFERENZ, false},
        eFlasche{PIN_FLASCHE_DA, false}, eKorken{PIN_KORKEN_ZAEHLER, false},
        eVoll{PIN_BEHAELTER_VOLL, false}, eHebel{PIN_HEBEL_GRUND, false};
Eingang* alleEingaenge[] = {&eStart, &eStopp, &eReset, &eSicher, &eZRef, &eStempel, &eSternRef,
                            &eFlasche, &eKorken, &eVoll, &eHebel};

// ---------------------------------------------------------------- Zustände
enum Zustand {
  Z_INIT, Z_REF_Z, Z_REF_STERN, Z_BEREIT,
  S1_TAKTEN, S2_ANTASTEN, S3_FEIN, S4_HEBELN, S5_ZURUECK, S6_HOCH,
  S7_ABSTREIFEN, S8_KONTROLLE, S9_NAECHSTE,
  Z_FERTIG, Z_BEHAELTER_VOLL, Z_STOERUNG, Z_SCHUTZ_OFFEN
};
const char* ZUSTANDSNAME[] = {
  "Init", "Referenz Z", "Referenz Sternrad", "Bereit",
  "S1 Takten", "S2 Antasten", "S3 Feinposition", "S4 Abhebeln", "S5 Hebel zurück", "S6 Kopf hoch",
  "S7 Abstreifen", "S8 Kontrolle", "S9 Nächste",
  "Fertig – entladen", "Behälter voll", "Störung", "Haube offen / Not-Halt"
};

Zustand zustand = Z_INIT;
uint32_t schrittStart = 0;
int tasche = 0;                   // aktuelle Tasche 0..7 in diesem Durchlauf
int geoeffnet = 0, uebersprungen = 0;
uint32_t korkenGesamt = 0;
String stoerung = "", warnung = "";
bool startAnforderung = false, stoppAnforderung = false, resetAnforderung = false;
bool referenziert = false;
long sternBasis = 0;              // Sternrad-Position der ersten Tasche dieser Charge
void taktStarten();

FastAccelStepperEngine engine;
FastAccelStepper *zAchse = nullptr, *stern = nullptr;
WebServer server(80);

// ---------------------------------------------------------------- Hilfen
long zSchritte(float mm) { return lround((mm - Z_REFERENZ_MM) * Z_SCHRITTE_PRO_MM); }
float zMm() { return Z_REFERENZ_MM + zAchse->getCurrentPosition() / Z_SCHRITTE_PRO_MM; }
uint32_t imSchritt() { return millis() - schrittStart; }

void weiter(Zustand z) {
  zustand = z;
  schrittStart = millis();
  Serial.printf("[%8lu] -> %s\n", millis(), ZUSTANDSNAME[z]);
}

void treiber(bool an) { digitalWrite(PIN_TREIBER_EN, an ? LOW : HIGH); }

void aktor(int richtung) {         // +1 ausfahren (Grundstellung), -1 einfahren (abhebeln), 0 aus
  digitalWrite(PIN_AKTOR_A, richtung > 0);
  digitalWrite(PIN_AKTOR_B, richtung < 0);
}

void servoGrad(int grad) {         // 50 Hz, 0,5 … 2,5 ms
  uint32_t us = 500 + (uint32_t)grad * 2000 / 180;
  ledcWrite(PIN_SERVO, us * 16383UL / 20000UL);
}

void alleStopp() {
  if (zAchse) zAchse->forceStop();
  if (stern) stern->forceStop();
  aktor(0);
}

void stoeren(const String& text) {
  alleStopp();
  stoerung = text;
  Serial.println("STÖRUNG: " + text);
  weiter(Z_STOERUNG);
}

bool laeuft(FastAccelStepper* s) { return s->isRunning(); }

// ---------------------------------------------------------------- Signalsäule
void lampen() {
  bool blink = (millis() / 400) % 2;
  bool gruen = false, gelb = false, rot = false, startLed = false;
  switch (zustand) {
    case Z_BEREIT:         gruen = blink; startLed = true; break;
    case Z_FERTIG:         gruen = blink; gelb = true; startLed = true; break;
    case Z_BEHAELTER_VOLL: gelb = blink; break;
    case Z_STOERUNG:       rot = blink; break;
    case Z_SCHUTZ_OFFEN:   rot = true; break;
    case Z_INIT: case Z_REF_Z: case Z_REF_STERN: gelb = true; break;
    default:               gruen = true; gelb = warnung.length() > 0; break;
  }
  digitalWrite(PIN_LAMPE_GRUEN, gruen);
  digitalWrite(PIN_LAMPE_GELB, gelb);
  digitalWrite(PIN_LAMPE_ROT, rot);
  digitalWrite(PIN_START_LED, startLed);
}

// ---------------------------------------------------------------- Schrittkette
void schrittkette() {
  bool reset = resetAnforderung;
  resetAnforderung = false;
  // Sicherheitskreis offen: Leistung ist bereits hardwareseitig abgeschaltet.
  if (!eSicher.zustand && zustand != Z_SCHUTZ_OFFEN) {
    alleStopp();
    referenziert = false;          // Schrittmotoren könnten Schritte verloren haben
    weiter(Z_SCHUTZ_OFFEN);
    return;
  }
  if (stoppAnforderung && zustand >= S1_TAKTEN && zustand <= S9_NAECHSTE) {
    stoppAnforderung = false;
    stoeren("Stopp durch Bediener");
    return;
  }
  stoppAnforderung = false;

  switch (zustand) {
    case Z_INIT:
      treiber(true);
      aktor(+1);                   // Hebel in Grundstellung
      servoGrad(SERVO_GRUND_GRAD);
      zAchse->setSpeedInHz(Z_FAHRT_HZ / 2);
      zAchse->runForward();        // nach oben zum Referenzschalter
      weiter(Z_REF_Z);
      break;

    case Z_REF_Z:
      if (eZRef.zustand) {
        zAchse->forceStop();
        zAchse->setCurrentPosition(0);           // 0 Schritte = Z_REFERENZ_MM
        zAchse->setSpeedInHz(Z_FAHRT_HZ);
        zAchse->moveTo(zSchritte(Z_SICHER_MM));
        stern->setSpeedInHz(STERN_HZ / 4);
        stern->runForward();
        weiter(Z_REF_STERN);
      } else if (imSchritt() > T_MAX_REFERENZ) stoeren("Referenz Z nicht gefunden");
      break;

    case Z_REF_STERN:
      if (eSternRef.zustand) {
        stern->forceStop();
        stern->setCurrentPosition(0);            // Tasche 0 in der Station
        referenziert = true;
        aktor(0);
        weiter(Z_BEREIT);
      } else if (imSchritt() > T_MAX_REFERENZ) stoeren("Referenz Sternrad nicht gefunden");
      break;

    case Z_BEREIT:
    case Z_FERTIG:
      if (startAnforderung) {
        startAnforderung = false;
        tasche = 0; geoeffnet = 0; uebersprungen = 0; warnung = "";
        // Die Tasche, die gerade in der Station steht, ist die erste dieser Charge.
        long p = stern->getCurrentPosition() % STERN_SCHRITTE_U;
        stern->setCurrentPosition(p);
        sternBasis = lround((double)p / STERN_TAKT) * STERN_TAKT;
        taktStarten();
      }
      break;

    case S1_TAKTEN:                // Sternrad in Vorposition (3 mm vor der Station)
      if (!laeuft(stern) && imSchritt() > 50) {
        if (!eFlasche.zustand) {                 // leere Tasche überspringen
          uebersprungen++;
          weiter(S9_NAECHSTE);
        } else {
          zAchse->setSpeedInHz(Z_FAHRT_HZ);
          zAchse->moveTo(zSchritte(Z_MIN_MM));
          weiter(S2_ANTASTEN);
        }
      } else if (imSchritt() > T_MAX_FAHRT) stoeren("Sternrad erreicht Position nicht");
      break;

    case S2_ANTASTEN:              // Z ab, bis Stempel den Kronkorken berührt
      if (zMm() < Z_SICHER_MM - 20) zAchse->setSpeedInHz(Z_ANTAST_HZ);
      if (eStempel.zustand) {
        zAchse->forceStop();
        zAchse->moveTo(zAchse->getCurrentPosition() + lround(Z_ANHEBEN_MM * Z_SCHRITTE_PRO_MM));
        stern->setSpeedInHz(STERN_FEIN_HZ);
        stern->moveTo(sternBasis - (long)tasche * STERN_TAKT);   // Station genau
        weiter(S3_FEIN);
      } else if (!laeuft(zAchse)) {              // ganz unten ohne Kontakt: kein Kronkorken
        warnung = "Tasche " + String(tasche + 1) + ": kein Kronkorken erkannt";
        uebersprungen++;
        zAchse->setSpeedInHz(Z_FAHRT_HZ);
        zAchse->moveTo(zSchritte(Z_SICHER_MM));
        weiter(S6_HOCH);
      }
      break;

    case S3_FEIN:
      if (!laeuft(stern) && !laeuft(zAchse)) { aktor(-1); weiter(S4_HEBELN); }
      break;

    case S4_HEBELN:
      if (imSchritt() >= T_HEBELN) { aktor(+1); weiter(S5_ZURUECK); }
      break;

    case S5_ZURUECK:
      if (eHebel.zustand && imSchritt() > 200) {
        aktor(0);
        geoeffnet++;
        zAchse->setSpeedInHz(Z_FAHRT_HZ);
        zAchse->moveTo(zSchritte(Z_SICHER_MM));
        weiter(S6_HOCH);
      } else if (imSchritt() > T_HEBEL_ZURUECK) stoeren("Hebel nicht in Grundstellung");
      break;

    case S6_HOCH:
      if (!laeuft(zAchse)) {
        servoGrad(SERVO_ABSTREIF_GRAD);
        weiter(S7_ABSTREIFEN);
      } else if (imSchritt() > T_MAX_FAHRT) stoeren("Z-Achse erreicht sichere Höhe nicht");
      break;

    case S7_ABSTREIFEN:
      if (imSchritt() >= T_SERVO) { servoGrad(SERVO_GRUND_GRAD); weiter(S8_KONTROLLE); }
      break;

    case S8_KONTROLLE:             // Kronkorken muss den Trichter passieren
      if (eKorken.flanke) { korkenGesamt++; weiter(S9_NAECHSTE); }
      else if (imSchritt() > T_MAX_KORKEN) {
        warnung = "Tasche " + String(tasche + 1) + ": Kronkorken nicht im Trichter erkannt";
        weiter(S9_NAECHSTE);
      }
      break;

    case S9_NAECHSTE:
      if (eVoll.zustand) { weiter(Z_BEHAELTER_VOLL); break; }
      tasche++;
      if (tasche >= TASCHEN) weiter(Z_FERTIG);
      else taktStarten();
      break;

    case Z_BEHAELTER_VOLL:         // Behälter leeren (Haube auf = Leistung aus), dann Reset
      if (!eVoll.zustand && reset) weiter(S9_NAECHSTE);
      break;

    case Z_STOERUNG:
      if (reset) { stoerung = ""; weiter(referenziert ? Z_BEREIT : Z_INIT); }
      break;

    case Z_SCHUTZ_OFFEN:
      if (eSicher.zustand && reset) { stoerung = ""; weiter(Z_INIT); }   // neu referenzieren
      break;
  }
}

void taktStarten() {               // S1: Sternrad auf Vorposition der aktuellen Tasche
  stern->setSpeedInHz(STERN_HZ);
  stern->moveTo(sternBasis - (long)tasche * STERN_TAKT + STERN_FEIN);   // Uhrzeigersinn = negativ
  weiter(S1_TAKTEN);
}

// ---------------------------------------------------------------- Weboberfläche
const char SEITE[] PROGMEM = R"HTML(<!doctype html><html lang="de"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Flaschenöffner</title>
<style>body{font-family:system-ui,sans-serif;margin:16px;max-width:520px}button{font-size:18px;
padding:10px 18px;margin:4px;border-radius:8px;border:1px solid #888}td{padding:3px 8px}
#z{font-size:22px;font-weight:600}</style>
<h2>Flaschenöffner Automatik</h2><div id="z">…</div><p id="m"></p>
<button onclick="f('start')">Start</button><button onclick="f('stopp')">Stopp</button>
<button onclick="f('reset')">Reset</button><table id="t"></table>
<script>
function f(c){fetch('/'+c,{method:'POST'}).then(l)}
function l(){fetch('/status').then(r=>r.json()).then(s=>{z.textContent=s.zustand;
m.textContent=(s.stoerung||'')+' '+(s.warnung||'');t.innerHTML=Object.entries(s.werte)
.map(([k,v])=>'<tr><td>'+k+'</td><td>'+v+'</td></tr>').join('')})}
setInterval(l,500);l();</script></html>)HTML";

void webEinrichten() {
  server.on("/", [] { server.send_P(200, "text/html", SEITE); });
  server.on("/status", [] {
    String j = "{\"zustand\":\"" + String(ZUSTANDSNAME[zustand]) + "\",\"stoerung\":\"" + stoerung +
               "\",\"warnung\":\"" + warnung + "\",\"werte\":{" +
               "\"Tasche\":\"" + String(tasche + 1) + " / " + String(TASCHEN) + "\"," +
               "\"Geöffnet\":" + String(geoeffnet) + ",\"Übersprungen\":" + String(uebersprungen) + "," +
               "\"Kronkorken gesamt\":" + String(korkenGesamt) + "," +
               "\"Z-Achse\":\"" + String(zMm(), 1) + " mm\"," +
               "\"Haube/Not-Halt\":\"" + String(eSicher.zustand ? "OK" : "offen") + "\"," +
               "\"Behälter\":\"" + String(eVoll.zustand ? "voll" : "frei") + "\"}}";
    server.send(200, "application/json", j);
  });
  server.on("/start", HTTP_POST, [] { startAnforderung = true; server.send(204); });
  server.on("/stopp", HTTP_POST, [] { stoppAnforderung = true; server.send(204); });
  server.on("/reset", HTTP_POST, [] { resetAnforderung = true; server.send(204); });
  server.begin();
}

#if ALEXA_AKTIV
bool alexaSchalten(const String& id, bool& an) {
  if (an && (zustand == Z_BEREIT || zustand == Z_FERTIG)) startAnforderung = true;
  if (!an) stoppAnforderung = true;
  return true;
}
#endif

// ---------------------------------------------------------------- setup / loop
void setup() {
  Serial.begin(115200);
  for (Eingang* e : alleEingaenge) pinMode(e->pin, INPUT);
  for (int p : {PIN_TREIBER_EN, PIN_AKTOR_A, PIN_AKTOR_B, PIN_LAMPE_GRUEN, PIN_LAMPE_GELB,
                PIN_LAMPE_ROT, PIN_START_LED}) { pinMode(p, OUTPUT); digitalWrite(p, LOW); }
  treiber(false);
  ledcAttach(PIN_SERVO, 50, 14);
  servoGrad(SERVO_GRUND_GRAD);

  engine.init();
  zAchse = engine.stepperConnectToPin(PIN_Z_STEP);
  stern = engine.stepperConnectToPin(PIN_STERN_STEP);
  if (!zAchse || !stern) { Serial.println("Schrittmotoren nicht verfügbar"); while (true) delay(1000); }
  zAchse->setDirectionPin(PIN_Z_DIR);
  stern->setDirectionPin(PIN_STERN_DIR);
  zAchse->setAcceleration(Z_BESCHL);
  stern->setAcceleration(STERN_BESCHL);

  WiFi.mode(WIFI_STA);
  WiFi.setHostname(GERAETENAME);
  WiFi.begin(WLAN_SSID, WLAN_PASS);      // Verbindung läuft im Hintergrund, Ablauf wartet nicht
  MDNS.begin(GERAETENAME);
  webEinrichten();
#if ALEXA_AKTIV
  SinricProSwitch& sw = SinricPro[SINRIC_SWITCH_ID];
  sw.onPowerState(alexaSchalten);
  SinricPro.begin(SINRIC_APP_KEY, SINRIC_APP_SECRET);
#endif
  for (Eingang* e : alleEingaenge) { e->lesen(); e->zustand = e->roh; }
  weiter(eSicher.zustand ? Z_INIT : Z_SCHUTZ_OFFEN);
}

void loop() {
  for (Eingang* e : alleEingaenge) e->lesen();
  if (eStart.flanke) startAnforderung = true;
  if (eReset.flanke) resetAnforderung = true;
  if (!eStopp.zustand) stoppAnforderung = true;        // Stopptaster ist ein Öffner
  schrittkette();
  lampen();
  server.handleClient();
#if ALEXA_AKTIV
  SinricPro.handle();
#endif
}
