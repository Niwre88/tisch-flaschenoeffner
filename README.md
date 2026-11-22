# Tisch-Flaschenöffner

Manuell betätigter Kronkorken-Öffner für den Tisch, gebaut fast nur aus Normteilen
(Alu-Systemprofil 40×40, Klemmhebel, Schubstangenspanner, Passschraube,
Gleitlager, Kugelknopf). Eine Person bedient ihn, die Flasche wird
eingespannt, und die Höhe lässt sich für alle gängigen deutschen Mehrweg-Bierflaschen
verstellen (171–270 mm Höhe, Ø 57–80 mm).

## Anschauen im Browser

- **Interaktive 3D-Vorschau:** [niwre88.github.io/tisch-flaschenoeffner/vorschau.html](https://niwre88.github.io/tisch-flaschenoeffner/vorschau.html)
  – Flaschensorte wählen, Spanner und Hebel bewegen, Ablauf abspielen. Läuft direkt
  im Browser, ohne Konto und ohne Installation.
- **STL-Dateien** zeigt GitHub direkt als drehbares 3D-Modell an, wenn man sie anklickt:
  - [`Flaschenoeffner_1zu1_Szene_mit_Mensch.stl`](Flaschenoeffner_1zu1_Szene_mit_Mensch.stl): Gerät auf Tisch mit Person
  - [`Flaschenoeffner_1zu1_mit_Flasche.stl`](Flaschenoeffner_1zu1_mit_Flasche.stl): Gerät mit NRW-Flasche
  - [`Flaschenoeffner_1zu1_ohne_Flasche.stl`](Flaschenoeffner_1zu1_ohne_Flasche.stl): nur das Gerät
  - [`Flaschenoeffner_1zu3_Druckmodell.stl`](Flaschenoeffner_1zu3_Druckmodell.stl): Anschauungsmodell für den 3D-Drucker
  - [`teile/`](teile/): einzelne Eigenfertigungsteile
- **Technische Dokumentation (PDF, 16 Seiten):** [`Technische_Dokumentation_TFO.pdf`](Technische_Dokumentation_TFO.pdf).
  Enthält Deckblatt, technische Daten, Montageanleitung, Einstell- und Wartungsblatt,
  Zusammenbauzeichnung TFO-000 mit Positionsnummern, Stückliste und die bemaßten
  Einzelteilzeichnungen TFO-001 … TFO-008. Die Zeichnungen haben ein Schriftfeld nach
  DIN EN ISO 7200 und folgen Projektionsmethode 1.
- **Stückliste:** [`Stueckliste.md`](Stueckliste.md)

## Funktionsprinzip

1. Den Schlitten mit zwei Klemmhebeln auf die Flaschenhöhe einstellen. Das Maßband
   zeigt direkt die Flaschenhöhe an.
2. Die Flasche vorn hinstellen. Der Schubstangenspanner schiebt sie in ein
   90°-Prisma, dabei gleitet der Kronkorken über die Hakenleiste.
3. Den Kugelknopf drücken. Der zweiseitige Hebel (≈ 4,4 : 1) hebt den Kronkorken
   ab, ein Magnet fängt ihn.

Das Prisma zentriert jede Flasche in X. Ein anderer Durchmesser verschiebt sie nur
in Y, also entlang der Hakenleiste. Deshalb greift der Haken bei allen Sorten.

## Dateien neu erzeugen

Alle Modelle entstehen aus `erzeuge_stl.py`, die Dokumentation und die Stückliste aus
`zeichnungen.py`. Beide brauchen nur Python 3 und numpy:

```
python erzeuge_stl.py
python zeichnungen.py
```

Maße ändern sich im Skript im Abschnitt „Hauptmaße der Maschine“.
`vorschau_vorlage.html` ist die Vorlage, in die das Skript die Modelldaten einsetzt.

## Quellen

Flaschenmaße: VLB Berlin, Tabelle der Standardpoolflaschen (Stand Jan. 2025).
Kronkorken: DIN EN 17177 und die technischen Lieferbedingungen für Kronenkorken.
Details und Links stehen in der Stückliste.
