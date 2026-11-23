# Flaschenöffner-Projekt

Kronkorken-Öffner für Bierflaschen, vom einfachen Handgerät für den Tisch bis zum
Automaten mit Magazin und ESP32-Steuerung. Konstruiert mit Python (numpy, CadQuery),
gebaut fast nur aus Normteilen.

## Übersicht der Stände

| Ordner | Was | Status | 3D-Vorschau |
|---|---|---|---|
| [`1_Handgeraet_TFO/`](1_Handgeraet_TFO/) | **Handgerät TFO**: manueller Tisch-Flaschenöffner, Flasche wird eingespannt, Hebel mit Kugelknopf | fertig konstruiert, Zeichnungssatz (PDF, 16 Seiten) | [öffnen](https://niwre88.github.io/tisch-flaschenoeffner/1_Handgeraet_TFO/vorschau.html) |
| [`2_Automat_TFO-A/`](2_Automat_TFO-A/) | **Automat TFO-A, Index B** (aktuell): Ausgabeautomat mit Magazin für 8 Flaschen, Bedienfach, Kronkorken-Schublade, ESP32 | Entwurf, Kollisionsprüfung 0 Befunde, Firmware ungetestet | [öffnen](https://niwre88.github.io/tisch-flaschenoeffner/2_Automat_TFO-A/vorschau_automatik.html) |
| [`2_Automat_TFO-A/archiv_Index_A/`](2_Automat_TFO-A/archiv_Index_A/) | **Automat TFO-A, Index A**: erster Automatik-Entwurf im Chargenbetrieb | **verworfen**, nicht bauen (32 Kollisionen, 9 Logikfehler) | [öffnen](https://niwre88.github.io/tisch-flaschenoeffner/2_Automat_TFO-A/archiv_Index_A/vorschau_automatik.html) |
| [`gemeinsam/`](gemeinsam/) | Werkzeuge: Generator des Handgeräts, Zeichnungs- und PDF-Funktionen, Flaschenmaße | wird von 1 und 2 benutzt | – |

**Was heißt „Index“?** Wie bei Zeichnungen in der Fertigung kennzeichnet der Index den
Änderungsstand eines Produkts. TFO-A ist der Automat, Index A sein erster Stand, Index B
die überarbeitete Fassung. Warum Index A verworfen wurde, steht im
[Prüfbericht](2_Automat_TFO-A/PRUEFBERICHT.md).

## Entwicklung

1. **Handgerät TFO:** Tischgerät aus Normteilen, höhenverstellbar für alle gängigen
   Mehrwegflaschen, Bedienung durch eine Person.
2. **Automat TFO-A Index A:** Hebel und Hakenleiste des Handgeräts, angetrieben. Er
   öffnet eine Charge von 8 Flaschen nacheinander. Bei der Prüfung fielen Kollisionen
   (Trichter, Schlauch und Aktorhalter in der Flaschenbahn) und Logikfehler auf (keine
   Ausgabe der Flaschen, keine Erkennung des Kronkorkens, Beladen nur bei offener Haube).
3. **Automat TFO-A Index B:** neu aufgebaut als Ausgabeautomat. Befüllen und Entnehmen
   über ein verriegeltes Fach, Öffnen auf Knopfdruck oder per Alexa, Kronkorken in eine
   Schublade. Jede Bewegungsstellung ist auf Kollisionen gerechnet.

Feste Stände lassen sich auch über Git-Tags abrufen:
`TFO-1.0` (Handgerät), `TFO-A-Index-A` und `TFO-A-Index-B`.

## Alles neu erzeugen

Benötigt Python 3 mit `numpy`; für den Automaten zusätzlich `cadquery`.

```
python gemeinsam/erzeuge_stl.py
python gemeinsam/zeichnungen.py
python 2_Automat_TFO-A/pruefe_kollisionen.py
python 2_Automat_TFO-A/erzeuge_step.py
python 2_Automat_TFO-A/erzeuge_automatik.py
python 2_Automat_TFO-A/doku_automatik.py
```

## Alte Links

Die früheren Vorschau-Adressen (`/vorschau.html` und `/automatik/vorschau_automatik.html`)
leiten automatisch auf die neuen Ordner weiter.
