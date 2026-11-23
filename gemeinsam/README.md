# Gemeinsame Werkzeuge

Zur Übersicht aller Stände: [zurück zur Hauptseite](../README.md)

| Datei | Inhalt | Benutzt von |
|---|---|---|
| `erzeuge_stl.py` | Generator des Handgeräts (STL, Vorschau), dazu Flaschenmaße aller Sorten, Flaschenprofil und Menschmodell | Handgerät, Automat |
| `zeichnungen.py` | PDF-Funktionen (Blatt, Schriftfeld, Ansichten, Bemaßung, Tabellen) und der Zeichnungssatz des Handgeräts | Handgerät, Automat |
| `vorschau_vorlage_TFO.html` | Vorlage der 3D-Vorschau des Handgeräts | Handgerät |

Die Ergebnisse des Handgeräts landen im Ordner [`../1_Handgeraet_TFO/`](../1_Handgeraet_TFO/).
Die Skripte des Automaten liegen in [`../2_Automat_TFO-A/`](../2_Automat_TFO-A/) und laden diese
Module von hier.
