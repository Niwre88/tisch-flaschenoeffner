# Prüfbericht TFO-A, Index C

Prüfung des Greifkopf-Automaten auf Kollisionen und Konsistenz. Gerechnet wird mit exakten
Volumenkörpern (CadQuery) in jeder Bewegungsstellung und für alle 12 Flaschensorten
(Euro 0,25 l bis Grenzmaß Ø 100 × 350 mm): `python pruefe_kollisionen.py` (ca. 20 s).

## Stand 2026-11-24: 0 Befunde

| Prüfung | Inhalt | Ergebnis |
|---|---|---|
| K1 | Takten: Kopf in Abwurfhöhe, Fangrinne geparkt, Flaschen auf dem ganzen Umlauf (alle 7,5°) | frei |
| K2 | Kopf aufgesetzt, Backen offen und zu, Flasche mit Kronkorken | frei |
| K3 | Kippen 0 … 25° mit geschlossenen Backen gegen das Glas | frei |
| K4 | Hubweg des Kopfes (Kippachse 267,5 … 515 mm) gegen alle festen Teile und die geparkte Rinne | frei |
| K5 | Fangrinne 0 … 119,5° gegen feste Teile, Kopf in Abwurfhöhe und Flaschen in allen 8 Taschen | frei |
| K6 | Nachbartaschen gegen den Kopf (offen, zu, gekippt) | frei |
| K7 | Geländerring je Sorte: Luft 0,5 mm, Klemmhebel im Langloch | erfüllt, Stellbereich Radius 182,3 … 231,2 mm |
| K8 | Sternrad und Flaschen gegen feste Teile, Geländer jeweils auf die Sorte eingestellt | frei |
| K9 | Konsistenz (siehe unten) | erfüllt |
| K10 | Greiferschwinge und Backen gegen den Kopfrahmen in allen Stellungen | frei |

**Kennwerte aus K9 und Abstandsmessung**

| Größe | Wert |
|---|---|
| Kopf in Abwurfhöhe, tiefster Punkt / höchster Kronkorken | 494,0 / 445,5 mm |
| Fangrinne über den Hälsen (Boden) | 453,0 mm |
| Rinne unter den Backen (Oberkante / Backen) | 490,6 / 505,0 mm |
| Fallhöhe Kronkorken in die Rinne | 39,6 mm |
| Neigung Fangrinne / Rutsche | 20° / 25° |
| Lippe Hubbacke zum Glas (Backen zu) | 0,3 mm |
| Druckbacke zum Glas beim Kippen (min.) | 1,3 mm |
| Schwingenwange zum Glas (Grenzformate) | 4,5 mm |
| Halslage je Sorte / Backenlänge | ± 14,3 mm / ± 27 mm |
| Moment an der Kippachse bei 150 N Abhebekraft | 3,8 Nm (vorhanden ca. 11,8 Nm) |

Zur Selbstkontrolle wurde die Prüfung mit absichtlich falschen Stellungen gefahren: Ein um
3 mm zu tief gesetzter Kopf meldet sofort Tastleiste und Druckbacke im Kronkorken.

## Bei der Ausarbeitung gefunden und behoben

| Befund | Lösung |
|---|---|
| Sternrad R 185 hätte bei der kleinsten Sorte die Geländer-Schieber gestreift | R_STERN 178 (6 mm unter dem kleinsten Geländerradius) |
| Stellarm-Sockel lagen in Index B in der Gleitplatte und wären von großen Flaschen überfahren worden | Sockel fest außerhalb der Gleitplatte (R 241 … 305), Schieber mit 72-mm-Arm |
| Fangrinnen-Servo: Ritzel Z18 auf Kranz Z66 hätte 438° Servoweg gebraucht | 270°-Servo mit Zahnradstufe 2 : 1 (bis 135° an der Rinne) |
| Kippmoment für einen Standardservo zu hoch | Servo 60 kg·cm mit Zahnradstufe 2 : 1 |

## Nicht durch Rechnung geprüft (offen für den Prototyp)

- Tatsächliche Abhebekraft und Verformung des Kronkorkens beim Kippen. Bleibt er nach dem
  Abheben sicher im Greifer (Nachgreifen) und fällt beim Öffnen frei heraus?
- Schaltabstand des flachen Induktivsensors -B8 am Rand der Tastleiste (Hals ± 14,3 mm).
- Rutschverhalten der Kronkorken in Fangrinne (20°) und Rutsche (25°).
- Firmware: ungetestet, nicht kompiliert. Servowinkel sind Startwerte.
- Risikobeurteilung und PL-Nachweis (SISTEMA) durch eine Fachkraft.
