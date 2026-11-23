# Archiv: Automat TFO-A, Index A (verworfen)

> **Nicht bauen.** Dieser erste Automatik-Entwurf hat 32 Kollisionen und 9 Funktions-
> und Logikfehler. Er ist durch [Index B](../README.md) ersetzt. Die Befunde und wie sie
> in Index B gelöst sind, stehen im [Prüfbericht](../PRUEFBERICHT.md).

Zur Übersicht aller Stände: [zurück zur Hauptseite](../../README.md)

## Was Index A war

Chargenbetrieb: Haube öffnen, bis zu 8 Flaschen einsetzen, Start. Die Maschine öffnet
alle Flaschen nacheinander. Ein Servo streift die Kronkorken in einen mitfahrenden
Trichter, von dort laufen sie über einen Schlauch in einen Sammelbehälter.

## Hauptmängel

- Trichter, Schlauch und Aktorhalter ragen in die Flaschenbahn (Kollisionen).
- Die geöffneten Flaschen werden nicht ausgegeben, Beladen und Entnehmen nur bei offener Haube.
- Keine Erkennung des Kronkorkens: Bei einer schon offenen Flasche würde der Hebel auf das Glas fahren.
- Keine Belegung der Taschen, keine Tropfschale, Behälter nur bei offener Haube zu leeren.

## Inhalt

Die Dateien sind unverändert aus Commit `a924b7b` (Git-Tag `TFO-A-Index-A`) übernommen:

| Datei | Inhalt |
|---|---|
| [`vorschau_automatik.html`](https://niwre88.github.io/tisch-flaschenoeffner/2_Automat_TFO-A/archiv_Index_A/vorschau_automatik.html) | 3D-Vorschau von Index A (alte Steuerung) |
| `TFO-A_Flaschenoeffner_Automatik.step` | STEP-Baugruppe Index A |
| `Technische_Dokumentation_TFO-A.pdf` | Dokumentation Index A, 12 Seiten |
| `TFO-A_*.stl`, `teile/` | Modelle und Teile von Index A |
| `firmware/` | Firmware Index A (Chargenbetrieb) |
| `skripte/` | Generatoren von Index A. Nur zur Nachvollziehbarkeit, so nicht mehr lauffähig |
| [`README_Original_Index_A.md`](README_Original_Index_A.md) | die ursprüngliche Beschreibung |
