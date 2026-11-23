# Flaschenöffner Automatik TFO-A

Automatisierte Variante des Tisch-Flaschenöffners. Sie öffnet bis zu 8 Flaschen
nacheinander und führt die Kronkorken selbsttätig in einen Sammelbehälter ab.
Das Prinzip mit Hebel und Hakenleiste stammt vom Handgerät, Handkraft und Kurbel
übernehmen Antriebe. Die Steuerung ist ein ESP32.

## Ablauf

1. Haube öffnen, bis zu 8 Flaschen in die Taschen des Sternrads setzen, Haube schließen, Reset, Start.
2. Je Flasche:
   - Das Sternrad taktet die Flasche in die Vorposition.
   - Die Z-Achse fährt den Kopf ab, bis der Magnetstempel den Kronkorken berührt. So findet sie die Höhe automatisch.
   - Das Sternrad fährt die letzten 3 mm, dabei gleitet der Kronkorkenrand über die Hakenlippe.
   - Der Linearantrieb hebelt den Kronkorken ab.
   - Der Kopf fährt hoch, der Servo streift den Kronkorken in den Trichter ab, von dort fällt er durch den Schlauch in den Behälter.
3. Leere Taschen, fehlende Kronkorken, ein voller Behälter und Zeitüberschreitungen werden erkannt und an der Signalsäule und in der Weboberfläche gemeldet.

## Dateien

| Datei | Inhalt |
|---|---|
| [`TFO-A_Flaschenoeffner_Automatik.step`](TFO-A_Flaschenoeffner_Automatik.step) | **STEP AP214, exakte Geometrie**, 10 Unterbaugruppen, 145 benannte Teile mit Farben, Bohrungen und Senkungen. Öffnet in FreeCAD, Fusion, SolidWorks und Inventor. |
| [`Technische_Dokumentation_TFO-A.pdf`](Technische_Dokumentation_TFO-A.pdf) | 12 Seiten: Daten, Funktion, Schrittkette, GRAFCET, Sicherheitskonzept, Betriebsmittel- und I/O-Liste, Stromlaufplan (3 Blätter), Zusammenbau, Stückliste, Inbetriebnahme |
| [`vorschau_automatik.html`](vorschau_automatik.html) | interaktive 3D-Vorschau mit animiertem Ablauf (Flaschensorte wählbar) |
| `TFO-A_*.stl` | Gesamtmodelle als STL, 1:4-Druckmodell für den P1S |
| `teile/` | Eigenfertigungsteile als STL |
| [`firmware/flaschenoeffner_automatik/`](firmware/flaschenoeffner_automatik/) | ESP32-Programm (Arduino): Schrittkette, Weboberfläche, optional Alexa |
| `erzeuge_automatik.py` | erzeugt STL und Vorschau (Python + numpy) |
| `erzeuge_step.py` | erzeugt die STEP-Baugruppe (Python + CadQuery) |
| `doku_automatik.py` | erzeugt das PDF (nutzt `../zeichnungen.py`, liest die STEP-Datei) |

## Neu erzeugen

```
python erzeuge_automatik.py
python erzeuge_step.py
python doku_automatik.py
```

## Firmware

- Benötigt: Arduino IDE 2, ESP32-Core ab 3.0, Bibliothek
  [FastAccelStepper](https://github.com/gin66/FastAccelStepper) (529 Sterne, letztes Update 2026-11-08).
- Optional Alexa: [SinricPro](https://github.com/sinricpro/esp8266-esp32-sdk) (280 Sterne,
  letztes Update 2026-11-12), dazu `ALEXA_AKTIV 1` setzen.
- `zugang_beispiel.h` nach `zugang.h` kopieren und die WLAN-Daten eintragen. `zugang.h` ist
  per `.gitignore` ausgeschlossen.
- **Status:** ungetestet. Das Programm ist ohne Hardware geschrieben, Kompilieren und
  Inbetriebnahme stehen aus.

## Sicherheit

Haube (Sicherheits-Türschalter Typ 2) und Not-Halt wirken zweikanalig auf ein
Sicherheitsrelais. Es schaltet die 24-V-Leistung der Antriebe ab. Der ESP32 ist keine
Sicherheitssteuerung. Die Einschätzung im PDF ist ein Entwurf. Risikobeurteilung und
PL-Nachweis muss eine Fachkraft durchführen.
