// ============================================================================
//  Flaschenöffner Automatik TFO-A – Konfiguration
//  Alle anlagenspezifischen Werte stehen hier. Maße in mm, Zeiten in ms.
// ============================================================================
#pragma once

// ---------------------------------------------------------------- Eingänge
// 24-V-Signale über Optokoppler-Platine (aktiv = HIGH am ESP32).
// GPIO 34/35/36/39 sind reine Eingänge ohne internen Pull-up: Pull-ups sitzen
// auf der Optokoppler-Platine.
constexpr int PIN_START          = 34;  // E1  Taster Start (Schließer)
constexpr int PIN_STOP           = 35;  // E2  Taster Stopp (Öffner -> aktiv = nicht gedrückt)
constexpr int PIN_RESET          = 36;  // E3  Taster Reset / Quittieren
constexpr int PIN_SICHERHEIT_OK  = 39;  // E4  Rückmeldung Sicherheitsrelais (Haube zu, Not-Halt frei)
constexpr int PIN_Z_REFERENZ     = 32;  // E5  Induktiv M8, Z-Achse oben
constexpr int PIN_STEMPEL        = 33;  // E6  Induktiv M8, Magnetstempel berührt Kronkorken
constexpr int PIN_STERN_REFERENZ = 25;  // E7  Induktiv M12, Referenzfahne Sternrad
constexpr int PIN_FLASCHE_DA     = 26;  // E8  Reflexlichttaster M18, Flasche in Station
constexpr int PIN_KORKEN_ZAEHLER = 27;  // E9  Gabellichtschranke im Trichter
constexpr int PIN_BEHAELTER_VOLL = 14;  // E10 Einweglichtschranke (aktiv = unterbrochen = voll)
constexpr int PIN_HEBEL_GRUND    = 13;  // E11 Induktiv M8, Hebel in Grundstellung

// ---------------------------------------------------------------- Ausgänge
constexpr int PIN_Z_STEP      = 16;     // A1  TMC2209 Z-Achse
constexpr int PIN_Z_DIR       = 17;
constexpr int PIN_STERN_STEP  = 18;     // A2  TMC2209 Sternrad
constexpr int PIN_STERN_DIR   = 19;
constexpr int PIN_TREIBER_EN  = 21;     // A3  Enable beider Treiber (LOW = aktiv)
constexpr int PIN_AKTOR_A     = 22;     // A4  H-Brücke Linearantrieb, Eingang A
constexpr int PIN_AKTOR_B     = 23;     // A5  H-Brücke Linearantrieb, Eingang B
constexpr int PIN_SERVO       = 15;     // A6  Servo-Abstreifer (PWM 50 Hz)
constexpr int PIN_LAMPE_GRUEN = 4;      // A7  Signalsäule grün  (über Relais/Transistor 24 V)
constexpr int PIN_LAMPE_GELB  = 5;      // A8  Signalsäule gelb
constexpr int PIN_LAMPE_ROT   = 2;      // A9  Signalsäule rot
constexpr int PIN_START_LED   = 12;     // A10 Leuchtmelder im Starttaster (nach dem Booten schalten)

// ---------------------------------------------------------------- Mechanik
// Z-Achse: Schrittmotor 200 Schritte/U, 1/8 Mikroschritt, Trapezspindel TR8x2
constexpr float Z_SCHRITTE_PRO_MM   = 200.0f * 8.0f / 2.0f;     // 800
// Sternrad: 200 Schritte/U, 1/8, Zahnriemen 20 -> 100 Zähne (5:1)
constexpr long  STERN_SCHRITTE_U    = 200L * 8L * 5L;           // 8000
constexpr int   TASCHEN             = 8;
constexpr long  STERN_TAKT          = STERN_SCHRITTE_U / TASCHEN; // 1000 = 45°
constexpr float STERN_RADIUS        = 150.0f;                   // Teilkreis Flaschenmitte
constexpr float FEIN_MM             = 3.0f;                     // Feinpositionierung
constexpr long  STERN_FEIN          = (long)(FEIN_MM / (2.0f * 3.14159265f * STERN_RADIUS)
                                             * STERN_SCHRITTE_U + 0.5f);   // ca. 25

// Z-Positionen als Höhe der Hebel-Drehachse über Tisch (Modellmaße TFO-A)
constexpr float Z_REFERENZ_MM   = 430.0f;   // Lage des Referenzschalters
constexpr float Z_SICHER_MM     = 395.0f;   // Hakenlippe über allen Kronkorken, Abstreifhöhe
constexpr float Z_MIN_MM        = 268.0f;   // tiefster Punkt (Euro 0,25 l: 274,5 minus Reserve)
constexpr float Z_ANHEBEN_MM    = 0.5f;     // nach Stempelkontakt wieder anheben

// Geschwindigkeiten (Schritte/s) und Beschleunigungen (Schritte/s²)
constexpr uint32_t Z_FAHRT_HZ      = 16000;  // 20 mm/s
constexpr uint32_t Z_ANTAST_HZ     = 2400;   //  3 mm/s
constexpr uint32_t Z_BESCHL        = 40000;
constexpr uint32_t STERN_HZ        = 6000;
constexpr uint32_t STERN_FEIN_HZ   = 800;
constexpr uint32_t STERN_BESCHL    = 12000;

// Linearantrieb (24 V, Hub 50, interne Endschalter)
constexpr uint32_t T_HEBELN        = 1400;   // Zeit für Abhebeln (Antrieb fährt ein)
constexpr uint32_t T_HEBEL_ZURUECK = 2500;   // Zeitgrenze bis "Hebel Grundstellung"

// Servo-Abstreifer
constexpr int      SERVO_GRUND_GRAD   = 0;
constexpr int      SERVO_ABSTREIF_GRAD = 130;
constexpr uint32_t T_SERVO            = 600;

// Zeitgrenzen (Störung, wenn überschritten)
constexpr uint32_t T_MAX_REFERENZ   = 30000;
constexpr uint32_t T_MAX_FAHRT      = 15000;
constexpr uint32_t T_MAX_KORKEN     = 1500;   // Kronkorken muss den Trichter passieren
constexpr uint32_t T_ENTPRELL       = 20;

// ---------------------------------------------------------------- Funktionen
#define ALEXA_AKTIV 0     // 1 = Start per Alexa über Sinric Pro (Zugangsdaten in zugang.h)
