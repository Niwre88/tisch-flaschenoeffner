// ============================================================================
//  Flaschenöffner-Automat TFO-A (Index C, Greifkopf) – Konfiguration
//  Alle anlagenspezifischen Werte stehen hier. Maße in mm, Zeiten in ms.
// ============================================================================
#pragma once

// ---------------------------------------------------------------- Eingänge über MCP23017 (I2C 0x20)
// 24-V-Signale über Optokoppler-Platine auf den MCP23017, Bit = 1 bedeutet "aktiv".
constexpr uint8_t MCP_ADRESSE = 0x20;
constexpr int PIN_SDA = 21, PIN_SCL = 22;
enum Eingang : uint8_t {
  E_OEFFNEN = 0,       // -S1 Leuchttaster "Öffnen" (Schließer)
  E_LADEN,             // -S2 Leuchttaster "Laden" (Schließer)
  E_STOPP,             // -S3 Stopp (Öffner -> 1 = nicht gedrückt)
  E_RESET,             // -S4 Reset / Quittieren
  E_SICHER_OK,         // -K1/-K2 Hilfsschließer in Reihe (Not-Halt, Klappe, Deckel in Ordnung)
  E_Z_REF,             // -B2 Z-Achse oben
  E_TASTLEISTE,        // -B3 Tastleiste berührt den Kronkorken (1,5 mm eingefedert)
  E_KRONKORKEN,        // -B8 induktiv über der Tastleiste: Metall = Kronkorken vorhanden / im Greifer
  E_STERN_REF,         // -B4 Referenzfahne Sternrad (Tasche 1 in der Station)
  E_FLASCHE_STATION,   // -B6 Reflexlichttaster Station
  E_FLASCHE_FACH,      // -B7 Reflexlichttaster Bedienfach
  E_KIPP_GRUND,        // -B10 Greiferschwinge in Grundstellung (0°)
  E_KK_RUTSCHE,        // -B11 Gabellichtschranke Rutsche (Impuls je Kronkorken)
  E_SCHUBLADE_VOLL,    // -B12 Einweglichtschranke unterbrochen
  E_SCHUBLADE_DA,      // -B13 Reedkontakt Schublade eingesetzt
  E_KLAPPE_ZU,         // -B1a Meldekontakt Bedienklappe geschlossen
  ANZAHL_EINGAENGE
};

// ---------------------------------------------------------------- Ausgänge direkt am ESP32
constexpr int PIN_Z_STEP = 16, PIN_Z_DIR = 17;          // -A3 TMC2209 Z-Achse
constexpr int PIN_S_STEP = 18, PIN_S_DIR = 19;          // -A4 TMC2209 Sternrad
constexpr int PIN_TREIBER_EN = 23;                      // LOW = Treiber aktiv
constexpr int PIN_SERVO_BACKEN = 25;                    // -M5 Greiferbacken (MG996R, 180°)
constexpr int PIN_SERVO_KIPPEN = 26;                    // -M6 Kippen (DS5160, 180°, Zahnräder 2 : 1)
constexpr int PIN_SERVO_RINNE  = 27;                    // -M4 Fangrinne (DS3218, 270°, Zahnräder 2 : 1)
constexpr int PIN_FACHLICHT = 33;                       // LED-Leiste Bedienfach (MOSFET)
constexpr int PIN_GRUEN = 4, PIN_GELB = 5, PIN_ROT = 2; // -P1 Signalsäule über -A6 (GPIO 2/5 = Strapping-Pins)
constexpr int PIN_LED_OEFFNEN = 13, PIN_LED_LADEN = 14; // Leuchtmelder in -S1 / -S2

// ---------------------------------------------------------------- Mechanik
constexpr float Z_SCHRITTE_PRO_MM = 200.0f * 8.0f / 2.0f;     // TR8x2, 1/8 Schritt: 800
constexpr long  STERN_SCHRITTE_U  = 200L * 8L * 5L;           // 1/8 Schritt, Riemen 5:1: 8000
constexpr int   TASCHEN           = 8;
constexpr long  STERN_TAKT        = STERN_SCHRITTE_U / TASCHEN; // 1000 = 45°
constexpr int   FACH_ABSTAND      = 4;                          // Bedienfach 4 Taschen nach der Station

// Z-Positionen als Höhe der Kippachse über Tisch (Maße aus modell_c.py)
constexpr float Z_REFERENZ_MM = 522.0f;
constexpr float Z_SICHER_MM   = 515.0f;   // Takten und Abwurf (Kopf über allen Flaschen bis 350 mm)
constexpr float Z_MIN_MM      = 262.0f;   // unter Euro 0,25 l (267,5) -> darunter: kein Kronkorken
constexpr float Z_VORLAUF_MM  = 15.0f;    // Eilgang bis 15 mm über die zuletzt ertastete Höhe

constexpr uint32_t Z_FAHRT_HZ   = 20000, Z_ANTAST_HZ = 8000, Z_BESCHL = 40000;   // 25 mm/s, Antasten 10 mm/s
constexpr uint32_t STERN_HZ     = 6000, STERN_BESCHL = 12000;

// Servowinkel (am Servo, nicht an der Mechanik). Beim Einrichten anpassen (PDF Kap. 7.2).
constexpr int SERVO_BEREICH_STANDARD = 180, SERVO_BEREICH_RINNE = 270;   // Winkel bei 0,5 … 2,5 ms
constexpr int BACKEN_AUF_GRAD   = 30;     // Backen offen (je 8,6 mm außen)
constexpr int BACKEN_ZU_GRAD    = 92;     // Lippe 0,25 mm neben dem Glas, 0,5 mm unter dem Rand
constexpr int BACKEN_FEST_GRAD  = 98;     // nachgreifen: Kronkorken nach dem Abheben festhalten
constexpr int KIPP_GRUND_GRAD   = 20;     // Schwinge 0° (-B10 bedämpft)
constexpr int KIPP_AB_GRAD      = 70;     // Schwinge 25° (2 : 1 -> 50° am Servo)
constexpr int RINNE_PARK_GRAD   = 10;     // Fangrinne über dem Trichter, außerhalb des Kopfes
constexpr int RINNE_ARBEIT_GRAD = 249;    // 119,5° an der Rinne (2 : 1 -> 239° am Servo)

constexpr uint32_t T_GREIFEN       = 600;
constexpr uint32_t T_KIPPEN        = 900;    // langsam fahren: Servo in Schritten über diese Zeit
constexpr uint32_t T_KIPP_ZURUECK  = 1500;
constexpr uint32_t T_RINNE         = 800;
constexpr uint32_t T_ABWURF        = 1500;   // Kronkorken muss B11 passieren
constexpr uint32_t T_MAX_REFERENZ  = 30000, T_MAX_FAHRT = 15000, T_ENTPRELL = 20;

#define ALEXA_AKTIV 0     // 1 = "Öffnen" per Alexa über Sinric Pro (Zugangsdaten in zugang.h)
