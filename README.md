# Flaschenöffner-Projekt

Kronkorken-Öffner für Bierflaschen, vom einfachen Handgerät für den Tisch bis zum
Automaten mit Magnetbahn und Industrie-SPS. Konstruiert mit Python (numpy, CadQuery),
gebaut fast nur aus Normteilen.

## Übersicht der Stände

| Ordner | Was | Status | 3D-Vorschau |
|---|---|---|---|
| [`1_Handgeraet_TFO/`](1_Handgeraet_TFO/) | **Handgerät TFO**: manueller Tisch-Flaschenöffner, Flasche wird eingespannt, Hebel mit Kugelknopf | fertig konstruiert, Zeichnungssatz (PDF, 16 Seiten) | [öffnen](https://niwre88.github.io/tisch-flaschenoeffner/1_Handgeraet_TFO/vorschau.html) |
| [`4_Automat_TFO-A_Index_D/`](4_Automat_TFO-A_Index_D/) | **Automat TFO-A, Index D** (aktuell, Konzeptstudie): Magnetbahn mit 6 Movern, Flasche für Flasche, Orbital-Entbördler (Neuentwicklung), Magnet-Kronkorkenabfuhr in einen Sammelturm, TwinCAT-SPS | Entwurf, Kollisionsprüfung 0 Befunde, Verfahren braucht Versuchsstand | [öffnen](https://niwre88.github.io/tisch-flaschenoeffner/4_Automat_TFO-A_Index_D/vorschau_automatik.html) |
| [`3_Automat_TFO-A_Index_C/`](3_Automat_TFO-A_Index_C/) | **Automat TFO-A, Index C** (Vorgänger, Greifer-Variante): Greifkopf öffnet von oben (Backen greifen, Schwinge kippt), Flaschen bis Ø 100 mm / 350 mm, Fangrinne statt Magnet | Entwurf, Kollisionsprüfung 0 Befunde, Firmware ungetestet | [öffnen](https://niwre88.github.io/tisch-flaschenoeffner/3_Automat_TFO-A_Index_C/vorschau_automatik.html) |
| [`2_Automat_TFO-A/`](2_Automat_TFO-A/) | **Automat TFO-A, Index B** (Vorgänger): Ausgabeautomat mit langem Hebel und Linearantrieb, Flaschen bis Ø 79 mm / 270 mm | Entwurf, durch Index C abgelöst, bleibt als Hebel-Variante erhalten | [öffnen](https://niwre88.github.io/tisch-flaschenoeffner/2_Automat_TFO-A/vorschau_automatik.html) |
| [`2_Automat_TFO-A/archiv_Index_A/`](2_Automat_TFO-A/archiv_Index_A/) | **Automat TFO-A, Index A**: erster Automatik-Entwurf im Chargenbetrieb | **verworfen**, nicht bauen (32 Kollisionen, 9 Logikfehler) | [öffnen](https://niwre88.github.io/tisch-flaschenoeffner/2_Automat_TFO-A/archiv_Index_A/vorschau_automatik.html) |
| [`gemeinsam/`](gemeinsam/) | Werkzeuge: Generator des Handgeräts, Zeichnungs- und PDF-Funktionen, Flaschenmaße | wird von allen Ständen benutzt | – |

**Was heißt „Index“?** Wie bei Zeichnungen in der Fertigung kennzeichnet der Index den
Änderungsstand eines Produkts. TFO-A ist der Automat: Index A sein erster Stand (verworfen),
Index B die überarbeitete Fassung mit Hebel, Index C die Fassung mit Greifkopf, Index D die
aktuelle Fassung mit Magnetbahn und Orbital-Entbördler.
Warum Index A verworfen wurde, steht im [Prüfbericht von Index B](2_Automat_TFO-A/PRUEFBERICHT.md),
die Prüfungen von Index C und D in deren Prüfberichten ([C](3_Automat_TFO-A_Index_C/PRUEFBERICHT.md),
[D](4_Automat_TFO-A_Index_D/PRUEFBERICHT.md)).

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
4. **Automat TFO-A Index C:** Öffnen von oben ohne langen Hebel. Ein Greifkopf greift den
   Kronkorken mit zwei Backen und kippt ihn ab, wie ein Handöffner mit Drehpunkt auf dem
   Kronkorken. Sternrad und Geländer für Flaschen bis Ø 100 mm und 350 mm Höhe.
5. **Automat TFO-A Index D:** alles neu gedacht. Jede Flasche fährt auf einem eigenen Mover
   einer Magnetbahn, ein Laser misst die Höhe im Vorbeifahren, gemischte Sorten sind
   erlaubt. Geöffnet wird durch Orbital-Entbördeln: Rollen biegen die Zähne des
   Kronkorkens rundum auf. Magnetbänder tragen die Kronkorken in einen Sammelturm.
   Industrie-SPS mit TwinCAT und TwinSAFE.

Feste Stände lassen sich auch über Git-Tags abrufen:
`TFO-1.0` (Handgerät), `TFO-A-Index-A`, `TFO-A-Index-B` und `TFO-A-Index-C`.

## Alles neu erzeugen

Benötigt Python 3 mit `numpy`; für den Automaten zusätzlich `cadquery`.

```
python gemeinsam/erzeuge_stl.py
python gemeinsam/zeichnungen.py
python 2_Automat_TFO-A/pruefe_kollisionen.py
python 2_Automat_TFO-A/erzeuge_step.py
python 2_Automat_TFO-A/erzeuge_automatik.py
python 2_Automat_TFO-A/doku_automatik.py
python 3_Automat_TFO-A_Index_C/pruefe_kollisionen.py
python 3_Automat_TFO-A_Index_C/erzeuge_step.py
python 3_Automat_TFO-A_Index_C/erzeuge_automatik.py
python 3_Automat_TFO-A_Index_C/doku_automatik.py
python 4_Automat_TFO-A_Index_D/pruefe_kollisionen.py
python 4_Automat_TFO-A_Index_D/erzeuge_step.py
python 4_Automat_TFO-A_Index_D/erzeuge_automatik.py
python 4_Automat_TFO-A_Index_D/doku_automatik.py
```

## Alte Links

Die früheren Vorschau-Adressen (`/vorschau.html` und `/automatik/vorschau_automatik.html`)
leiten automatisch auf die neuen Ordner weiter.
