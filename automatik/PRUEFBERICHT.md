# Prüfbericht TFO-A

Prüfung der Automatik-Variante auf Kollisionen, Funktion und Bedienlogik.
Die Kollisionen werden mit exakten Volumenkörpern (CadQuery) in jeder Bewegungsstellung
und für alle 9 Flaschensorten gerechnet: `python pruefe_kollisionen.py`.

## Stand Index B (2026-11-23): 0 Befunde

| Prüfung | Inhalt | Ergebnis |
|---|---|---|
| K1 | Takten mit Kopf in sicherer Höhe: Flaschen auf dem ganzen Umlauf gegen Kopf, Schwenkarm, Trichter | frei |
| K2 | Arbeitsstellung (Vorposition 3 mm und Station) je Sorte | frei |
| K3 | Abhebeln 0 … 15°: Haken gegen Glas | frei (Lippe 2 mm über der Drehachse) |
| K4 | Hubweg des Kopfes gegen feste Teile | frei, Aktorbügel tiefste Stellung 197,5 mm über Deck |
| K5 | Schwenkarm 0 … 90° in sicherer Höhe | frei |
| K6 | Nachbartaschen gegen Kopf in Arbeitsstellung | frei |
| K7 | Geländerring je Sorte eingestellt | frei, Stellbereich Radius 171,3 … 199,1 mm |
| K8 | Sternrad und Flaschen gegen feste Teile | frei |
| K9 | Konsistenz: Kronkorken nach dem Schwenk über dem Trichter (Unterkante 404 mm, Trichter 400 mm), Rutsche 25°, Hakenlippe in sicherer Höhe 385 mm über dem höchsten Kronkorken 365,5 mm | erfüllt |

**Wie die Befunde des alten Stands behoben sind:**

| Befund (Index A) | Lösung (Index B) |
|---|---|
| K1–K3, L5: mitfahrender Trichter und Schlauch in der Flaschenbahn | fester Trichter neben der Station, Stempel am Schwenkarm bringt den Kronkorken hin |
| K5: ein Federband für 24 mm Durchmesserspanne | Geländerring mit 3 Stellarmen und Skala, Feder gleicht den Rest aus |
| K6: Aktorhalter läuft unter dem Hebel durch | Linearantrieb über dem Hebel, Bügel oben |
| L1, L2, L9: keine Ausgabe, Beladen bei offener Haube | Bedienfach mit verriegelter Klappe vorn, Funktionen *Öffnen* und *Laden* |
| L3: keine Erkennung des Kronkorkens | Stempelkontakt -B3 plus Induktivsensor -B8 im Stempel |
| L4: keine Belegung | Belegung je Tasche im Flash, Erfassung mit -B7 beim Schließen der Klappe |
| L6: Behälter nur bei offener Haube | Schublade im abgetrennten Fach mit eigener Tür, Meldung voll/fehlt |
| L7: keine Tropfschale | Tropfschale mit Gitter unter dem Fach |
| L8: Bedienung unklar | Ausgabeautomat: eine Taste je Funktion, Signalsäule, Fachlicht, Weboberfläche |

Bei der Prüfung von Index B zusätzlich gefunden und behoben: Haken gegen Glas (Lippe von
ZP−15 auf ZP+2), Säule und Führung in der Flaschenbahn (Säule nach hinten, Distanzplatte
A25), Referenzsensor in der Flaschenbahn (auf Radius 75 mm), Aktorbügel gegen
Nachbarflasche.

**Nicht durch Rechnung geprüft** (offen für den Prototyp): Abhebekraft, Haltekraft und
Restmagnetismus des Haftmagneten, Schaltabstand -B8 durch die POM-Platte, Rutschverhalten
der Kronkorken, Firmware (ungetestet, nicht kompiliert).

---

# Teil A: Befunde des ersten Entwurfs (Index A)

## 1. Kollisionen (gerechnet)

| Nr. | Befund | Ursache |
|---|---|---|
| K1 | Beim Takten (Kopf in sicherer Höhe) streifen NRW 0,5 l und Longneck 0,5 l den Trichter bei 115° | Der Trichter fährt mit dem Kopf und hängt 42 mm unter der Drehachse, also tiefer als hohe Kronkorken |
| K2 | Der Trichterhalter überschneidet sich in Arbeitsstellung bei **allen 9 Sorten** mit dem Flaschenhals, in Vorposition und in der Station (bis 437 mm³) | Halter liegt bei x −26 … −14 mm, der Kronkorken der einlaufenden Flasche reicht bis x −17,9 mm |
| K3 | Der Spiralschlauch schneidet bei 6 Sorten die Flasche bei 105° (bis 2612 mm³) | Der Schlauch führt quer über die Bahn der einlaufenden Flaschen |
| K4 | Aktorhalter in tiefster Stellung 26,5 mm über der Deckplatte | in Ordnung |
| K5 | Federband: Spalt zur Flasche je nach Sorte 4,6 … 28,2 mm | Ein Federband kann nicht 24 mm Spanne ausgleichen. Kleine Flaschen würden nicht in die Tasche gedrückt, damit wäre die Lage in Umfangsrichtung (und damit der Haken) unbestimmt |
| K6 | Aktorhalter berührt bei 5 Sorten die Nachbarflasche bei 45° (bis 5303 mm³) | Der Halter läuft auf Flaschenhöhe quer unter dem Hebel durch |

## 2. Funktions- und Logikfehler (Durchsicht)

| Nr. | Befund | Folge |
|---|---|---|
| L1 | Flaschen werden nie ausgegeben. Zugesagt war „nacheinander geöffnet und ausgeschoben“ | Bediener muss 8 offene Flaschen aus der Maschine holen |
| L2 | Beladen nur bei offener Haube, Sternrad steht dann still | Hintere Taschen schwer erreichbar, keine definierte Ladeposition |
| L3 | Keine Erkennung „Kronkorken vorhanden“. Der Stempel tastet auch auf Glas an | Bei schon offener Flasche fährt der Stempel auf den Glasrand und der Hebel löst aus: Gefahr von Glasbruch |
| L4 | Keine Belegungsverwaltung der Taschen (leer / verschlossen / geöffnet) | Neue Charge öffnet wieder alle 8 Taschen, Zustand nach Stromausfall unbekannt |
| L5 | Kronkorken-Abwurf in einen mitfahrenden Trichter statt an einer festen Stelle außerhalb der Flaschenbahn (Praxis bei Rotationsentkorkern: Magnet hält, Auswurf an fester Position) | siehe K1 bis K3 |
| L6 | Sammelbehälter nur bei offener Haube zu leeren | Stillstand für eine Nebentätigkeit |
| L7 | Keine Tropfschale | Überschäumendes Bier läuft auf Gleitplatte und Sternrad |
| L8 | Bedienung unklar: „Start“ öffnet die ganze Charge, es gibt keine Funktion „eine Flasche öffnen“ und kein „Laden“ | entspricht nicht der Nutzung zu Hause |
| L9 | Eine einzige Klappe (580 × 570 mm) ist zugleich Lade-, Entnahme- und Servicezugang | große Öffnung, schwere Klappe, ständiger Stillstand |

## 3. Was aus der Praxis übernommen wird

- **Formatteile:** Sternrad, Geländer und Mittenführung werden in Flaschenlinien je Durchmesser
  gewechselt oder verstellt. Umgesetzt als verstellbarer Geländerring mit Skala (statt
  Wechselteilen), eine Feder gleicht Toleranzen aus.
- **Gefederter Zaun:** Er drückt die Flasche in die Sternradtasche (Patent US4070854A), mit
  kurzem Federweg je Formatstufe.
- **Kronkorken magnetisch halten, an fester Stelle auswerfen:** feste Rutsche hinter der Station,
  außerhalb der Flaschenbahn, in eine Schublade, die von außen zu leeren ist.
- **Zugang:** Öffnungen von 40 bis 120 mm brauchen 850 mm Abstand zur Gefahrstelle
  (EN ISO 13857). Deshalb ist das Bedienfach eine verriegelte Klappe, und das Sternrad steht,
  solange sie offen ist.

## 4. Konsequenz

Neuaufbau als **Flaschenöffner-Automat mit Bedienfach** (Ablauf wie bei einem Ausgabeautomaten):
befüllen und entnehmen durch ein kleines verriegeltes Fach vorn, öffnen auf Knopfdruck oder per
Alexa, Kronkorken in eine Schublade, die von außen zu leeren ist. Die Begründung steht im Konzept.

## Quellen

- [US4070854A Apparatus for removing bottle caps](https://patents.google.com/patent/US4070854A/en): gefederter Zaun drückt Flaschen in die Sternradtaschen
- [Lexikon Entkorker (yumda)](https://www.yumda.com/de/lexikon/Entkorker.html): Takt- und Rotationsentkorker, magnetisches Halten und Auswerfen
- [Star Wheel Conveyors](https://packagingconveyor.com/conveyor-functions/infeed-outfeed/star-wheel/): Formatteile je Flaschendurchmesser
- [Pilz: Sicherheitsabstände EN ISO 13857](https://www.pilz.com/mam/pilz/content/editors_subsidiaries/tg-de/presentations/booklet_safety_distance.pdf)
- [earthtojake/text-to-cad](https://github.com/earthtojake/text-to-cad) (dein Sternchen-Repo): Prüfschema „Kollision je Stellung, von innen nach außen“
