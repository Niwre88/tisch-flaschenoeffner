# 3 · Flaschenöffner-Automat TFO-A, Index C (Greifkopf)

> **Nachfolger: [Index D](../4_Automat_TFO-A_Index_D/)** mit Magnetbahn und Orbital-Entbördler.
> Index C bleibt als Greifer-Variante erhalten.

**Status: Entwurf. Kollisionsprüfung 0 Befunde, Firmware ungetestet.**
Zur Übersicht aller Stände: [zurück zur Hauptseite](../README.md) ·
**3D-Vorschau:** [niwre88.github.io/tisch-flaschenoeffner/3_Automat_TFO-A_Index_C/vorschau_automatik.html](https://niwre88.github.io/tisch-flaschenoeffner/3_Automat_TFO-A_Index_C/vorschau_automatik.html)

Neue Revision des Automaten. Das Bedienkonzept von [Index B](../2_Automat_TFO-A/) bleibt
(Ausgabeautomat mit Magazin für 8 Flaschen, Bedienfach, Kronkorken-Schublade, ESP32).
Neu sind der Öffnungsmechanismus und die Größe:

| | Index B | Index C |
|---|---|---|
| Öffnen | langer Hebel (245 mm) mit Hakenleiste, Linearantrieb, Flasche fährt seitlich unter den Haken | **Greifkopf von oben**: zwei Backen greifen den Kronkorken, die Schwinge kippt 25° |
| Kronkorken halten | Elektro-Haftmagnet, Schwenkarm zum Trichter | Greifer hält ihn, **Fangrinne** schwenkt unter den Kopf |
| Flaschen | Ø 59,5 … 79 mm, Höhe bis 270 mm | **Ø 59,5 … 100 mm, Höhe bis 350 mm** (z. B. 0,66 l, 0,75 l) |
| Sternrad / Geländer | R 175, Stellweg 28 mm | R 178, Taschenscheitel R 110, **Stellweg 49 mm** |
| Antriebe | 2 Schrittmotoren, Linearantrieb, 1 Servo | 2 Schrittmotoren, 3 Servos |
| Maße B × T × H | 603 × 618 × 802 mm | 683 × 698 × 872 mm |

## Wie der Greifkopf öffnet

Das Prinzip ist das eines Handöffners: ein Haken unter dem Rand, ein Drehpunkt oben auf
dem Kronkorken. Der Kopf macht daraus zwei kurze Bewegungen von oben:

1. **Aufsetzen:** Die Z-Achse fährt ab, bis die gefederte Tastleiste den Kronkorken berührt (-B3).
   -B8 prüft, ob Metall darunter ist.
2. **Greifen:** Servo -M5 schließt die Backen über Zahnstangen. Die Lippe der *Hubbacke* liegt
   0,5 mm unter dem Kronkorkenrand und 0,25 mm neben dem Glas. Die Nase der *Druckbacke* liegt
   oben auf dem Kronkorken.
3. **Kippen:** Servo -M6 kippt die ganze Greiferschwinge um 25°. Die Kippachse liegt genau unter
   der Nase. Die Nase ist damit der Drehpunkt und drückt nach unten, die Lippe hebt den Rand an.
   Weil beide Kräfte ein Kräftepaar bilden, wird die Flasche nicht hochgezogen.
4. **Abwurf:** Der Greifer hält den Kronkorken, der Kopf fährt hoch, die Fangrinne schwenkt
   darunter, die Backen öffnen. Der Kronkorken rutscht über Trichter und Rutsche in die Schublade.

Die Backen sind 54 mm lang. Je nach Durchmesser steht der Hals bis ±14,3 mm radial woanders
(V-Tasche), die Backen greifen trotzdem jede Sorte, ohne dass am Kopf etwas verstellt wird.

## Bedienung

| Was | Wie |
|---|---|
| **Bier holen** | Taste *Öffnen* (grün). Nach ca. 20 s blinkt die Säule grün und das Fachlicht leuchtet. Klappe öffnen, Flasche nehmen, Klappe schließen. |
| **Befüllen** | Taste *Laden* (blau). Die nächste leere Tasche fährt ins Fach. Klappe öffnen, Flasche einsetzen, schließen. |
| **Kronkorken leeren** | Tür links hinten öffnen, Schublade ziehen. Das Fach ist durch eine Trennwand von allen bewegten Teilen getrennt. |
| **Format wechseln** | Servicedeckel öffnen, die 3 Stellarme des Geländerrings auf den Skalenwert der Sorte schieben (Tabelle im PDF). Höhe und Halslage findet die Maschine selbst. |
| **Störung** | Säule rot blinkt, Text in der Weboberfläche, quittieren mit *Reset*. |

Nur Flaschen mit **26-mm-Kronkorken**. Manche 0,75-l-Sektformen haben einen 29-mm-Kronkorken,
die passen nicht.

## Dateien

| Datei | Inhalt |
|---|---|
| [`modell_c.py`](modell_c.py) | **einzige Geometriequelle** (CadQuery): 158 Teile in 10 Unterbaugruppen, Bewegungen, Formatberechnung, 12 Flaschensorten |
| [`pruefe_kollisionen.py`](pruefe_kollisionen.py) | Kollisionsprüfung K1–K10 mit exakten Volumenkörpern für jede Stellung und alle Sorten. Stand: 0 Befunde |
| [`TFO-A_Flaschenoeffner_Automatik.step`](TFO-A_Flaschenoeffner_Automatik.step) | **STEP AP214** mit Namen und Farben, öffnet in FreeCAD, Fusion, SolidWorks, Inventor |
| [`Technische_Dokumentation_TFO-A.pdf`](Technische_Dokumentation_TFO-A.pdf) | 14 Seiten: Daten, Bedienung, Formattabelle, Schrittkette, GRAFCET, Sicherheit, Betriebsmittel, I/O-Liste, Stromlaufplan (3 Blätter), Zusammenbau, Stückliste, Inbetriebnahme |
| [`vorschau_automatik.html`](vorschau_automatik.html) | interaktive 3D-Vorschau mit animiertem Ablauf (Greifen, Kippen, Abwurf, Ausgabe), alle 12 Sorten wählbar |
| [`PRUEFBERICHT.md`](PRUEFBERICHT.md) | Prüfungen K1–K10, Abstände, offene Punkte |
| `TFO-A_*.stl` | Gesamtmodelle, **1:4-Druckmodell** (171 × 175 × 218 mm, passt auf den P1S) |
| `teile/` | Eigenfertigungsteile als STL (Dateiname = Teilename im STEP) |
| [`firmware/flaschenoeffner_automatik/`](firmware/flaschenoeffner_automatik/) | ESP32-Programm (Arduino): Schrittkette, Belegung, Weboberfläche, optional Alexa |

## Neu erzeugen

Benötigt Python 3 mit `cadquery` und `numpy`. Flaschenmaße, Menschmodell und
PDF-Funktionen kommen aus [`../gemeinsam/`](../gemeinsam/).

```
python pruefe_kollisionen.py
python erzeuge_step.py
python erzeuge_automatik.py
python doku_automatik.py
```

`doku_automatik.py` liest die STEP-Datei für die Ansichten, deshalb zuerst `erzeuge_step.py`.

## Firmware

- Arduino IDE 2, ESP32-Core ab 3.0, Bibliothek
  [FastAccelStepper](https://github.com/gin66/FastAccelStepper), optional
  [SinricPro](https://github.com/sinricpro/esp8266-esp32-sdk) für Alexa (`ALEXA_AKTIV 1`).
- `zugang_beispiel.h` nach `zugang.h` kopieren und die WLAN-Daten eintragen (per `.gitignore` ausgeschlossen).
- Die Servowinkel in `konfiguration.h` sind Startwerte und werden beim Einrichten angepasst (PDF, Kap. 7.2).
- **Status: ungetestet.** Ohne Hardware geschrieben und nicht kompiliert.

## Sicherheit

Wie Index B: Not-Halt zweikanalig auf ein Not-Halt-Relais mit manuellem Start, Bedienklappe
und Servicedeckel zweikanalig auf einen Schutztürwächter. Beide schalten die 24-V-Leistung
für Schrittmotoren und Servo-Wandler ab. Der ESP32 ist keine Sicherheitssteuerung.
Risikobeurteilung und PL-Nachweis muss eine Fachkraft durchführen.
