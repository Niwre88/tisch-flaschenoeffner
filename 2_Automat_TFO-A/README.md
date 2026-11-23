# 2 · Flaschenöffner-Automat TFO-A (Index B, aktueller Stand)

**Status: Entwurf. Kollisionsprüfung 0 Befunde, Firmware ungetestet.**
Zur Übersicht aller Stände: [zurück zur Hauptseite](../README.md) ·
**3D-Vorschau:** [niwre88.github.io/tisch-flaschenoeffner/2_Automat_TFO-A/vorschau_automatik.html](https://niwre88.github.io/tisch-flaschenoeffner/2_Automat_TFO-A/vorschau_automatik.html)

Automatische Variante des Tisch-Flaschenöffners. Sie arbeitet wie ein
Getränkeautomat: Im Magazin stehen bis zu 8 verschlossene Flaschen. Auf Knopfdruck
(oder per Weboberfläche bzw. Alexa) öffnet die Maschine eine Flasche, wirft den
Kronkorken in eine Schublade und stellt die offene Flasche ins Bedienfach.
Hebel und Hakenleiste stammen vom Handgerät, Antriebe ersetzen Hand und Kurbel.
Die Steuerung ist ein ESP32.

> Index B ersetzt den ersten Entwurf (Index A, Chargenbetrieb). Warum, steht im
> [Prüfbericht](PRUEFBERICHT.md): 32 Kollisionen und 9 Logikfehler im alten Stand.
> Index A liegt zum Nachschlagen im Ordner [`archiv_Index_A/`](archiv_Index_A/).

## Bedienung

| Was | Wie |
|---|---|
| **Bier holen** | Taste *Öffnen* (grün). Nach ca. 10 s blinkt die Säule grün und das Fachlicht leuchtet. Klappe öffnen, Flasche nehmen, Klappe schließen. |
| **Befüllen** | Taste *Laden* (blau). Die nächste leere Tasche fährt ins Fach. Klappe öffnen, Flasche einsetzen, schließen. Je Flasche einmal drücken. |
| **Kronkorken leeren** | Tür links öffnen, Schublade ziehen. Das Fach ist durch eine Trennwand von allen bewegten Teilen getrennt. |
| **Format wechseln** | Servicedeckel öffnen, die 3 Stellarme des Geländerrings auf den Skalenwert der Sorte schieben (Tabelle im PDF). Die Höhe findet die Maschine selbst. |
| **Störung** | Säule rot blinkt, Text in der Weboberfläche, quittieren mit *Reset*. |

Öffnen ist gesperrt, solange eine offene Flasche im Fach steht, die Schublade fehlt
oder voll ist oder das Magazin leer ist. Jeder Grund wird angezeigt.

## Ablauf je Flasche

1. Das Sternrad fährt die nächste volle Tasche auf die Station (hinten, 90°).
2. Der Kopf fährt ab, bis der gefederte Stempel den Kronkorken berührt (Höhe automatisch).
3. Ein Induktivsensor im Stempel prüft, ob wirklich ein Kronkorken da ist. Ohne Kronkorken
   wird nicht gehebelt, sondern die Flasche mit Hinweis ausgegeben.
4. Das Sternrad fährt die letzten 3 mm, der Kronkorkenrand gleitet über die Hakenlippe.
5. Der Haftmagnet hält den Kronkorken, der Linearantrieb hebelt ihn ab.
6. Kopf in sichere Höhe, Stempelarm schwenkt 90° über den festen Trichter, Magnet aus.
   Der Kronkorken rutscht über eine Rinne in die Schublade, eine Lichtschranke zählt ihn.
7. Das Sternrad dreht 180° weiter: Die offene Flasche steht im Bedienfach (vorn, 270°).

Die Belegung jeder Tasche (leer, voll, offen) wird im ESP32 gespeichert und übersteht
einen Stromausfall. Beim Schließen der Klappe erkennt ein Lichttaster, ob eine Flasche
entnommen oder eingesetzt wurde.

## Dateien

| Datei | Inhalt |
|---|---|
| [`modell_a.py`](modell_a.py) | **einzige Geometriequelle** (CadQuery): 141 Teile in 10 Unterbaugruppen, Bewegungen, Formatberechnung |
| [`pruefe_kollisionen.py`](pruefe_kollisionen.py) | Kollisionsprüfung K1–K9 mit exakten Volumenkörpern für jede Stellung und alle 9 Flaschensorten. Stand Index B: 0 Befunde |
| [`TFO-A_Flaschenoeffner_Automatik.step`](TFO-A_Flaschenoeffner_Automatik.step) | **STEP AP214**, exakte Geometrie mit Namen und Farben. Öffnet in FreeCAD, Fusion, SolidWorks, Inventor |
| [`Technische_Dokumentation_TFO-A.pdf`](Technische_Dokumentation_TFO-A.pdf) | 14 Seiten: Daten, Bedienung, Formattabelle, Schrittkette, GRAFCET, Sicherheitskonzept, Betriebsmittel, I/O-Liste, Stromlaufplan (3 Blätter), Zusammenbau, Stückliste, Inbetriebnahme |
| [`vorschau_automatik.html`](vorschau_automatik.html) | interaktive 3D-Vorschau (WebGL) mit animiertem Ablauf: Öffnen, Abwurf, Ausgabe, Entnahme |
| [`PRUEFBERICHT.md`](PRUEFBERICHT.md) | Befunde des alten Stands, Praxisregeln, Stand Index B |
| `TFO-A_*.stl` | Gesamtmodelle, 1:4-Druckmodell für den P1S |
| `teile/` | Eigenfertigungsteile als STL (Dateiname = Teilename im STEP) |
| [`firmware/flaschenoeffner_automatik/`](firmware/flaschenoeffner_automatik/) | ESP32-Programm (Arduino): Schrittkette, Belegung, Weboberfläche, optional Alexa |

## Neu erzeugen

Benötigt Python 3 mit `cadquery` und `numpy`.

```
python pruefe_kollisionen.py
python erzeuge_step.py
python erzeuge_automatik.py
python doku_automatik.py
```

`doku_automatik.py` liest die STEP-Datei für die Ansichten und zählt die Stückliste
direkt aus `modell_a.py`. Deshalb zuerst `erzeuge_step.py` ausführen. Flaschenmaße,
Menschmodell und PDF-Funktionen kommen aus [`../gemeinsam/`](../gemeinsam/).

## Firmware

- Benötigt: Arduino IDE 2, ESP32-Core ab 3.0, Bibliothek
  [FastAccelStepper](https://github.com/gin66/FastAccelStepper) (529 Sterne, letztes Update 2026-11-08).
  Die 16 Eingänge laufen über einen MCP23017. Das Programm spricht ihn direkt über
  `Wire` an, ohne weitere Bibliothek.
- Optional Alexa: [SinricPro](https://github.com/sinricpro/esp8266-esp32-sdk) (280 Sterne,
  letztes Update 2026-11-12), dazu `ALEXA_AKTIV 1` setzen.
- `zugang_beispiel.h` nach `zugang.h` kopieren und die WLAN-Daten eintragen. `zugang.h` ist
  per `.gitignore` ausgeschlossen.
- **Status: ungetestet.** Das Programm ist ohne Hardware geschrieben und nicht kompiliert.

## Sicherheit

Not-Halt wirkt zweikanalig auf ein Not-Halt-Relais mit manuellem Start. Bedienklappe
und Servicedeckel wirken zweikanalig auf einen Schutztürwächter. Beide schalten die
24-V-Leistung der Antriebe ab. Das Schließen der Klappe startet keine Bewegung. Der
ESP32 ist keine Sicherheitssteuerung. Die Einschätzung im PDF ist ein Entwurf.
Risikobeurteilung und PL-Nachweis muss eine Fachkraft durchführen.
