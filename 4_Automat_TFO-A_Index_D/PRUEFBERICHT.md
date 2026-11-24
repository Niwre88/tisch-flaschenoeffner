# Prüfbericht TFO-A, Index D

Prüfung mit exakten Volumenkörpern (CadQuery) für alle 12 Flaschensorten:
`python pruefe_kollisionen.py` (ca. 1 min).

## Stand 2026-11-24: 0 Befunde

| Prüfung | Inhalt | Ergebnis |
|---|---|---|
| K1 | Durchfahrt Öffnungsstation: Einfahrt mit Kronkorken (Rotor 0°), Ausfahrt offen (Rotor 180°, Kopf + 8 mm), je 10 mm | frei |
| K2 | Entbördeln: Rollen zugestellt, Rotor 0 … 360° gegen das Glas | frei |
| K3 | Kronkorken am Überband vom Kopf bis zum Steigband | frei (0,8 mm über dem Mechanismus) |
| K4 | Hubweg Kopf ZC 289 … 476 mm gegen alle festen Teile | frei |
| K5 | Mover mit Flasche auf der ganzen Bahn (alle 20 mm) gegen feste Teile und den Kopf in beiden Endlagen | frei |
| K6 | Benachbarte Mover an allen Stationen (Ø 100 mm) | frei, engster Abstand Messen–Öffnen 180 mm |
| K7 | Klemme auf jeden Durchmesser geschlossen, offen frei | erfüllt |
| K8 | Rotor, Zustellring, Hebel gegen Kopfrahmen in allen Stellungen | frei |
| K9 | Konsistenz | erfüllt |

| Kennwert | Wert |
|---|---|
| Schlitz im Rotor (Sehne innen) | 36,3 mm (Kronkorken 29,8 mm) |
| Rollenkante zugestellt / Glas | 13,4 mm / 13,15 mm |
| Rolle unter der Zahnkante | 0,3 mm, Anstieg 1,5 mm am Ende der Zustellung |
| Spalt Überband / Kronkorken | 0,5 mm (Entlüften) |
| Spalt Überband-Ende / Steigband | 6 mm |
| Übergabehöhe an das Steigband | 298 … 476 mm (Steigband 270 … 815 mm) |
| Abwurfrutsche Steigband → Turm | 21,4° |
| Sammelturm | ca. 2,9 l, ca. 300 Kronkorken |

**Gegenprobe:** Mit falsch stehendem Rotorschlitz (90°) meldet die Prüfung Rotor und
Zustellring, mit 4 mm zu tief gesetztem Kopf das Überband.

## Bei der Ausarbeitung gefunden und behoben

| Befund | Lösung |
|---|---|
| Kronkorken am Überband wäre beim Abtransport gegen Ständer und Zustellring gestoßen | gesamter Orbitalmechanismus unter die Zahnkante gelegt (alles unter 6,3 mm) |
| Rollen hätten die Zahnkante nur berührt, nicht aufgebogen | Hebelachse geneigt: 1,5 mm Anstieg am Ende der Zustellung |
| Klemmschienen benachbarter Mover überschnitten sich (K6) | Schiene ±84 mm, Messstation 10 mm weiter weg |
| Zahnstange der Klemme im Glas der 100-mm-Flasche (K7) | Zahnstangen oben auf die Schiene |
| Steigband-Motor im Z-Modul, Abwurfrutsche hinter statt vor dem Steigband | Motor auf die andere Seite, Rutsche vor das Band |
| Fachsensoren ragten aus der Front | Reflextaster schauen von oben in die Tasche |

## Nicht durch Rechnung geprüft (Versuchsstand nötig)

- **Orbital-Entbördeln** als Verfahren: Rollenform, Zustellweg, Drehzahl, Zahl der Umdrehungen,
  Verhalten bei Kronkorken verschiedener Hersteller und Wandstärken.
- Haltekraft des Überbands gegen den Innendruck (bis ca. 3 bar) und Entlüften über den Spalt.
- Magnetische Übergabe Überband → Steigband bei allen Höhen.
- Kräfte auf die Mover-Klemme beim Entbördeln (Reibmoment der Rollen).
- SPS-Programm: Gerüst, nicht übersetzt, nicht getestet.
- Risikobeurteilung und PL-Nachweis durch eine Fachkraft.
