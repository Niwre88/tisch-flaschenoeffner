// ============================================================================
//  Flaschenöffner-Automat TFO-A (Index B) – Konfiguration
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
  E_STEMPEL,           // -B3 Stempel berührt Kronkorken
  E_KRONKORKEN,        // -B8 induktiv im Stempel: Metall = Kronkorken vorhanden
  E_STERN_REF,         // -B4 Referenzfahne Sternrad (Tasche 1 in der Station)
  E_FLASCHE_STATION,   // -B6 Reflexlichttaster Station
  E_FLASCHE_FACH,      // -B7 Reflexlichttaster Bedienfach
  E_HEBEL_GRUND,       // -B10 Hebel in Grundstellung
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
constexpr int PIN_AKTOR_A = 25, PIN_AKTOR_B = 26;       // -A5 H-Brücke Linearantrieb -M3
constexpr int PIN_SERVO = 27;                           // -M4 Servo Schwenkarm (PWM 50 Hz)
constexpr int PIN_MAGNET = 32;                          // -Y2 Elektro-Haftmagnet (MOSFET)
constexpr int PIN_FACHLICHT = 33;                       // LED-Leiste Bedienfach (MOSFET)
constexpr int PIN_GRUEN = 4, PIN_GELB = 5, PIN_ROT = 2; // -P1 Signalsäule über -A6 (GPIO 2/5 = Strapping-Pins)
constexpr int PIN_LED_OEFFNEN = 13, PIN_LED_LADEN = 14; // Leuchtmelder in -S1 / -S2

// ---------------------------------------------------------------- Mechanik
constexpr float Z_SCHRITTE_PRO_MM = 200.0f * 8.0f / 2.0f;     // TR8x2, 1/8 Schritt: 800
constexpr long  STERN_SCHRITTE_U  = 200L * 8L * 5L;           // 1/8 Schritt, Riemen 5:1: 8000
constexpr int   TASCHEN           = 8;
constexpr long  STERN_TAKT        = STERN_SCHRITTE_U / TASCHEN; // 1000 = 45°
constexpr int   FACH_ABSTAND      = 4;                          // Bedienfach 4 Taschen nach der Station
constexpr float STERN_RADIUS      = 150.0f;
constexpr long  STERN_FEIN        = (long)(3.0f / (2.0f * 3.14159265f * STERN_RADIUS) * STERN_SCHRITTE_U + 0.5f);

// Z-Positionen als Höhe der Hebel-Drehachse über Tisch (Maße aus modell_a.py)
constexpr float Z_REFERENZ_MM = 455.0f;
constexpr float Z_SICHER_MM   = 400.0f;   // Takten, Schwenken, Abwurf
constexpr float Z_MIN_MM      = 251.0f;   // unter Euro 0,25 l (257,5) -> darunter: kein Kronkorken
constexpr float Z_ANHEBEN_MM  = 0.5f;
constexpr float Z_VORLAUF_MM  = 15.0f;    // Eilgang bis 15 mm über die zuletzt ertastete Höhe

constexpr uint32_t Z_FAHRT_HZ   = 16000, Z_ANTAST_HZ = 8000, Z_BESCHL = 40000;   // Antasten 10 mm/s (Stempelfeder 5 mm)
constexpr uint32_t STERN_HZ     = 6000,  STERN_FEIN_HZ = 800, STERN_BESCHL = 12000;

constexpr uint32_t T_HEBELN        = 1400;   // Linearantrieb fährt aus (Hebel drücken)
constexpr uint32_t T_HEBEL_ZURUECK = 2500;
constexpr int      SERVO_GRUND_GRAD = 0, SERVO_TRICHTER_GRAD = 90;
constexpr uint32_t T_SCHWENK       = 700;
constexpr uint32_t T_ABWURF        = 1500;   // Kronkorken muss B11 passieren
constexpr uint32_t T_MAX_REFERENZ  = 30000, T_MAX_FAHRT = 15000, T_ENTPRELL = 20;

#define ALEXA_AKTIV 0     // 1 = "Öffnen" per Alexa über Sinric Pro (Zugangsdaten in zugang.h)
