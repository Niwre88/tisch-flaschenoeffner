# 4 · Flaschenöffner-Automat TFO-A, Index D (Magnetbahn + Orbital-Entbördler)

**Status: Entwurf, Konzeptstudie mit Neuentwicklung. Kollisionsprüfung 0 Befunde, SPS-Programm ungetestet.**
Zur Übersicht aller Stände: [zurück zur Hauptseite](../README.md) ·
**3D-Vorschau:** [niwre88.github.io/tisch-flaschenoeffner/4_Automat_TFO-A_Index_D/vorschau_automatik.html](https://niwre88.github.io/tisch-flaschenoeffner/4_Automat_TFO-A_Index_D/vorschau_automatik.html)

Komplett neu gedachte Revision. Kein Hebel, kein Greifer, kein Drehteller.

| | Index C | Index D |
|---|---|---|
| Transport | Sternrad dreht 180° zur Ausgabe | **Magnetbahn mit 6 Movern**, jede Flasche fährt für sich, Flasche für Flasche |
| Flasche halten | V-Tasche + Geländerring (Format einstellen) | **selbstzentrierende Klemme** auf jedem Mover, keine Einstellung |
| Höhe | Kopf tastet jede Flasche an | **Laser misst im Vorbeifahren**, Kamera prüft den Verschluss |
| Öffnen | Backen greifen, Schwinge kippt (Hebelprinzip) | **Orbital-Entbördeln**: Rollen biegen die Zähne rundum auf |
| Kronkorken | Greifer hält, Fangrinne | **Magnet-Überband + Magnet-Steigband** in einen Sammelturm |
| Sorten | eine Sorte je Füllung | **gemischt**, jede Flasche anders |
| Takt | ca. 20 s | **ca. 4–6 s** (Schätzung) |
| Steuerung | ESP32 | **Industrie-PC mit TwinCAT, EtherCAT, TwinSAFE** |
| Maße B × T × H | 683 × 698 × 872 mm | 1040 × 731 × 992 mm |

## Wie Index D öffnet

Ein Kronkorken hält nur, weil seine 21 Zähne unter den Wulst der Flasche gebogen sind.
Index D hebelt ihn nicht ab, sondern **biegt die Zähne wieder auf**:

1. **Messen:** Der Mover hält kurz unter Laser und Kamera. Höhe und Verschluss sind bekannt,
   der Kopf fährt schon auf die richtige Höhe.
2. **Einfahren:** Der Rotorring und der Ständer sind geschlitzt (wie bei einer
   Orbital-Schweißzange). Der Hals fährt seitlich hinein.
3. **Entbördeln:** Drei Hartmetallrollen fahren 0,3 mm unter die Zahnkante und laufen
   zweimal um den Hals. Am Ende der Zustellung steigen sie um 1,5 mm und biegen immer nur
   2 bis 3 Zähne gleichzeitig auf. Die Zustellung kommt von einem zweiten Ring, dessen
   Winkelversatz zum Rotor die SPS als Kurvenscheibe fährt.
4. **Entlüften und Abheben:** Das Magnet-Überband liegt 0,5 mm über dem Kronkorken und hält
   ihn gegen den Innendruck. Das CO₂ entweicht langsam durch den Spalt, das gibt wenig Schaum.
   Dann hebt der Kopf 8 mm, und der Kronkorken hängt am Band.
5. **Ausfahren und Abfuhr:** Der Rotor dreht den Schlitz zur anderen Seite, die offene Flasche
   fährt hinaus zur Ausgabe. Das Überband trägt den Kronkorken nach hinten. Ein senkrechtes
   Magnet-Steigband übernimmt ihn und wirft ihn oben über eine Rutsche in den Sammelturm.

## Bedienung

| Was | Wie |
|---|---|
| **Bier holen** | Taste *Öffnen* (oder Panel/Alexa). Die offene Flasche steht im linken Fach, Klemme offen: Klappe auf, Flasche nach vorn herausziehen. |
| **Laden** | Leerer Mover im rechten Fach, Fachlicht an: Klappe auf, Flasche in die Klemme stellen, Klappe zu, Quittieren. Jede Sorte erlaubt. |
| **Kronkorken leeren** | Servicedeckel auf, Sammelturm (ca. 300 Kronkorken) per Bajonett herausnehmen. |
| **Störung** | Text am Panel, quittieren mit *Quittieren* (blau). |

Nur Flaschen mit **26-mm-Kronkorken**.

## Dateien

| Datei | Inhalt |
|---|---|
| [`modell_d.py`](modell_d.py) | **einzige Geometriequelle** (CadQuery): Bahnfunktion, Mover, Orbitalkopf, Abfuhr, 12 Flaschensorten |
| [`pruefe_kollisionen.py`](pruefe_kollisionen.py) | Kollisionsprüfung K1–K9: Durchfahrt durch den Schlitz, Entbördeln, Kronkorkenweg, Hubweg, Umlauf, Abstände. Stand: 0 Befunde |
| [`TFO-A_Flaschenoeffner_Automatik.step`](TFO-A_Flaschenoeffner_Automatik.step) | **STEP AP214**, 6 Mover an ihren Stationen |
| [`Technische_Dokumentation_TFO-A.pdf`](Technische_Dokumentation_TFO-A.pdf) | 14 Seiten: Daten, Bedienung, Schrittkette, GRAFCET, TwinSAFE-Sicherheitskonzept, Betriebsmittel, EtherCAT-I/O-Liste, Stromlaufplan (3 Blätter), Zusammenbau, Stückliste, Inbetriebnahme |
| [`vorschau_automatik.html`](vorschau_automatik.html) | 3D-Vorschau: Mover fahren Flasche für Flasche, Kopf passt sich jeder Flasche an, Kronkorken wandert in den Turm |
| [`PRUEFBERICHT.md`](PRUEFBERICHT.md) | Prüfungen, Kennwerte, gefundene und behobene Fehler, offene Punkte |
| `TFO-A_*.stl` | Gesamtmodelle, **1:5-Druckmodell** (208 × 146 × 198 mm, passt auf den P1S) |
| `teile/` | Eigenfertigungsteile als STL |
| [`sps/`](sps/) | TwinCAT-3-Programm (Structured Text): Mover-Verwaltung, Schrittkette Öffnungsstation |

## Neu erzeugen

```
python pruefe_kollisionen.py
python erzeuge_step.py
python erzeuge_automatik.py
python doku_automatik.py
```

## Ehrlich gesagt

Das Orbital-Entbördeln gibt es so noch nicht. Die Geometrie ist durchgerechnet, aber ob die
Zähne sich so sauber aufbiegen lassen, zeigt erst ein Versuchsstand. Deshalb wäre der erste
Schritt ein **Einzelkopf auf dem Tisch**: Rotor, eine Rolle, ein Servo, eine eingespannte
Flasche. Die Teile des Kopfs lassen sich dafür zum großen Teil auf dem P1S drucken
(Rollen und Hebel aus Stahl).
