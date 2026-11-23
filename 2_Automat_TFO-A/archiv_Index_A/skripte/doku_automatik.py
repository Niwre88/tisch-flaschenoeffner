"""
Technische Dokumentation des automatischen Flaschenöffners TFO-A (PDF).

Inhalt: Deckblatt, technische Daten, Funktionsbeschreibung, Schrittkette und
Ablaufdiagramm, Sicherheitskonzept, Betriebsmittel- und I/O-Liste, Stromlaufplan
(3 Blätter), Zusammenbauansichten aus der STEP-Baugruppe, Stückliste,
Inbetriebnahme und Programmierung.

Nutzt die PDF-Funktionen aus ../zeichnungen.py.   Aufruf:  python doku_automatik.py
"""
import math
import sys
from pathlib import Path

import numpy as np

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))
import zeichnungen as Z  # noqa: E402
import erzeuge_automatik as A  # noqa: E402

AUSGABE = HIER / "Technische_Dokumentation_TFO-A.pdf"
STEP = HIER / "TFO-A_Flaschenoeffner_Automatik.step"
TITEL = "Flaschenöffner Automatik TFO-A"
SEITE = [0]


def kopf(pdf, titel):
    S = pdf.seite(210, 297)
    SEITE[0] += 1
    S.linie(20, 282, 200, 282, 0.3)
    S.text(20, 284.5, f"Technische Dokumentation  {TITEL}", 2.6, grau=0.35)
    S.text(200, 284.5, "TFO-A-D01", 2.6, ausr="r", grau=0.35)
    S.linie(20, 15, 200, 15, 0.3)
    S.text(20, 10.5, f"Entwurf, Stand {Z.DATUM}", 2.4, grau=0.35)
    S.text(200, 10.5, f"Seite {SEITE[0]}", 2.4, ausr="r", grau=0.35)
    S.text(20, 268, titel, 6, True)
    return S, 256


def zeichnungsblatt(pdf, titel, nr, art="Zeichnung", blatt="1/1", massstab="–"):
    SEITE[0] += 1
    S = Z.blatt(pdf, "A3q", titel, nr, massstab, "–", "–", "", TITEL, blatt, toleranz=False)
    # Dokumentenart im Schriftfeld überschreiben (Feld liegt bei x0+35..70, y0..10)
    x0 = 420 - 10 - 180
    S.rechteck(x0 + 35.2, 10.2, x0 + 69.8, 17.6, 0, fuellen=1.0)
    S.text(x0 + 36.2, 11.6, art, 2.2)
    return S


# =====================================================================
# Daten
# =====================================================================
SCHRITTE = [
    ("S0", "Grundstellung / Referenz", "Z-Achse fährt nach oben auf B2, Sternrad dreht bis B4, Hebel ausgefahren (B8), Servo 0°",
     "B2 und B4 erreicht", "30 s", "Referenz nicht gefunden"),
    ("S1", "Takten", "Sternrad auf Vorposition der Tasche (3 mm vor Station); B5 prüfen",
     "M2 steht; B5 = 1 (sonst Tasche überspringen)", "15 s", "Sternrad erreicht Position nicht"),
    ("S2", "Antasten", "Z-Achse fährt mit 3 mm/s ab bis der Magnetstempel den Kronkorken berührt",
     "B3 = 1 (Kontakt), dann 0,5 mm anheben", "unterste Lage", "kein Kronkorken -> Warnung, S6"),
    ("S3", "Feinposition", "Sternrad fährt die letzten 3 mm; Kronkorkenrand gleitet über die Hakenlippe",
     "M2 und M1 stehen", "–", "–"),
    ("S4", "Abhebeln", "Linearantrieb M3 fährt ein, Haken hebt Kronkorken ab, Stempel = Drehpunkt",
     "Zeit T_HEBELN abgelaufen", "1,4 s", "–"),
    ("S5", "Hebel zurück", "M3 fährt aus, Kronkorken haftet am Magnet",
     "B8 = 1 (Hebel in Grundstellung)", "2,5 s", "Hebel nicht in Grundstellung"),
    ("S6", "Kopf hoch", "Z-Achse fährt in sichere Höhe (395 mm)", "M1 steht", "15 s", "Z erreicht Höhe nicht"),
    ("S7", "Abstreifen", "Servo M4 schwenkt 130°, schiebt Kronkorken in den Trichter, zurück auf 0°",
     "Zeit T_SERVO abgelaufen", "0,6 s", "–"),
    ("S8", "Kontrolle", "Gabellichtschranke B6 im Trichter zählt den Kronkorken",
     "Flanke B6", "1,5 s", "kein Kronkorken -> Warnung"),
    ("S9", "Weiterschalten", "Behälter prüfen (B7), nächste Tasche oder Ende der Charge",
     "B7 = 0 und Tasche < 8 -> S1; Tasche = 8 -> Fertig", "–", "B7 = 1 -> Behälter voll"),
]

BETRIEBSMITTEL = [
    # BMK, Benennung, Typ / Daten, Anschluss
    ("-Q1", "Hauptschalter", "2-polig, 10 A, abschließbar", "230 V AC"),
    ("-F1", "Feinsicherung Primär", "T 2 A", "230 V AC"),
    ("-T1", "Netzteil", "24 V DC, 150 W (6,5 A)", "230 V AC -> 24 V"),
    ("-F2", "Sicherung Steuerung", "T 1 A", "24 V"),
    ("-F3", "Sicherung Leistung", "T 4 A", "24 V über -K1"),
    ("-T2", "DC/DC-Wandler", "24 V -> 5 V, 2 A", "ESP32, Optokoppler"),
    ("-T3", "DC/DC-Wandler", "24 V -> 6 V, 3 A", "Servo -M4 (über -K1)"),
    ("-K1", "Sicherheitsrelais", "2-kanalig, Querschluss­erkennung, manueller Start, 2 Schließer + 1 Öffner (Meldekontakt)", "24 V"),
    ("-S0", "Not-Halt", "Pilztaster, 2 Öffner, EN ISO 13850", "Kanal 1/2 -K1"),
    ("-B1", "Sicherheits-Türschalter", "Typ 2 (EN ISO 14119), 2 Öffner zwangsöffnend", "Kanal 1/2 -K1"),
    ("-S1", "Drucktaster Start", "grün, Schließer, mit Leuchtmelder 24 V", "E1"),
    ("-S2", "Drucktaster Stopp", "rot, Öffner", "E2"),
    ("-S3", "Drucktaster Reset", "blau, Schließer (auch Start -K1)", "E3"),
    ("-B2", "Näherungsschalter Z-Referenz", "induktiv M8, PNP, Sn 2 mm", "E5"),
    ("-B3", "Näherungsschalter Stempel", "induktiv M8, PNP, Sn 2 mm", "E6"),
    ("-B4", "Näherungsschalter Sternrad", "induktiv M12, PNP, Sn 4 mm", "E7"),
    ("-B5", "Reflexlichttaster Flasche", "M18, PNP, Tastweite 100 mm", "E8"),
    ("-B6", "Gabellichtschranke Trichter", "Gabelweite 30 mm, PNP", "E9"),
    ("-B7", "Einweglichtschranke Behälter", "M18 Sender/Empfänger, PNP, hellschaltend", "E10"),
    ("-B8", "Näherungsschalter Hebel", "induktiv M8, PNP", "E11"),
    ("-A1", "Mikrocontroller", "ESP32-DevKit (WROOM-32) auf Trägerplatine", "5 V"),
    ("-A2", "Optokoppler-Platine", "11 Kanäle, 24 V -> 3,3 V, mit Pull-ups", "E1 … E11"),
    ("-A3", "Schrittmotortreiber Z", "TMC2209, Standalone, 1/8, 1,2 A", "A1, A3"),
    ("-A4", "Schrittmotortreiber Sternrad", "TMC2209, Standalone, 1/8, 1,5 A", "A2, A3"),
    ("-A5", "Motortreiber Linearantrieb", "H-Brücke 24 V, 5 A", "A4, A5"),
    ("-A6", "Relaisplatine", "4 Kanäle, 5-V-Ansteuerung, 24-V-Kontakte", "A7 … A10"),
    ("-M1", "Schrittmotor Z-Achse", "NEMA17, 1,5 A, 0,45 Nm", "-A3"),
    ("-M2", "Schrittmotor Sternrad", "NEMA17, 1,7 A, 0,59 Nm", "-A4"),
    ("-M3", "Linearantrieb", "24 V, Hub 50 mm, 200 N, interne Endschalter", "-A5"),
    ("-M4", "Servo Abstreifer", "MG996R, 6 V, 10 kg·cm", "A6"),
    ("-P1", "Signalsäule", "grün/gelb/rot, 24 V LED", "-A6"),
]

IO = [
    ("E1", "GPIO 34", "-S1", "Start", "Schließer, Flanke startet die Charge"),
    ("E2", "GPIO 35", "-S2", "Stopp", "Öffner, 0 = Stopp (drahtbruchsicher)"),
    ("E3", "GPIO 36", "-S3", "Reset / Quittieren", "Schließer"),
    ("E4", "GPIO 39", "-K1", "Sicherheitskreis OK", "Meldekontakt Sicherheitsrelais"),
    ("E5", "GPIO 32", "-B2", "Z-Achse oben (Referenz)", "1 = bedämpft"),
    ("E6", "GPIO 33", "-B3", "Stempelkontakt", "1 = Kronkorken berührt"),
    ("E7", "GPIO 25", "-B4", "Sternrad Referenz", "1 = Tasche 0 in Station"),
    ("E8", "GPIO 26", "-B5", "Flasche in Station", "1 = Flasche erkannt"),
    ("E9", "GPIO 27", "-B6", "Kronkorken im Trichter", "Impuls je Kronkorken"),
    ("E10", "GPIO 14", "-B7", "Behälter voll", "1 = Strahl unterbrochen"),
    ("E11", "GPIO 13", "-B8", "Hebel Grundstellung", "1 = Grundstellung"),
    ("A1", "GPIO 16 / 17", "-A3", "Z-Achse STEP / DIR", "800 Schritte/mm"),
    ("A2", "GPIO 18 / 19", "-A4", "Sternrad STEP / DIR", "1000 Schritte je Tasche"),
    ("A3", "GPIO 21", "-A3, -A4", "Treiber Enable", "LOW = aktiv"),
    ("A4", "GPIO 22", "-A5", "Linearantrieb ausfahren", "Grundstellung"),
    ("A5", "GPIO 23", "-A5", "Linearantrieb einfahren", "Abhebeln"),
    ("A6", "GPIO 15", "-M4", "Servo PWM", "50 Hz, 0,5 … 2,5 ms"),
    ("A7", "GPIO 4", "-A6/-P1", "Signalsäule grün", ""),
    ("A8", "GPIO 5", "-A6/-P1", "Signalsäule gelb", ""),
    ("A9", "GPIO 2", "-A6/-P1", "Signalsäule rot", ""),
    ("A10", "GPIO 12", "-A6/-S1", "Leuchtmelder Start", "erst nach dem Booten schalten"),
]

STUECKLISTE = [
    ("Eigenfertigung", [
        ("A01", 1, "Deckplatte 600×560×8", "EN AW-5754"), ("A02", 1, "Gleitplatte Ø460×6", "PE-UHMW"),
        ("A03", 2, "Sternradscheibe Ø350×10, 8 V-Taschen", "PE-HD"), ("A05", 1, "Kopfplatte 60×110×10", "EN AW-5754"),
        ("A06", 1, "Mutternhalter 22×46×10", "EN AW-5754"), ("A07", 1, "Stempelarm 8 mm", "S235JR"),
        ("A08", 1, "Abstreifer 70×6×4", "1.4301"), ("A09", 1, "Trichter mit Halter", "PETG (3D-Druck) / S235"),
        ("A10", 1, "Aktorhalter 8 mm", "S235JR"), ("A11", 1, "Hebel 30×12, L 225", "S235JR"),
        ("A12", 1, "Hakenleiste 35×42×10", "C45, gehärtet"), ("A13", 1, "Sammelbehälter 105×107×150", "PP"),
        ("–", 1, "Nabe Ø44, Welle Ø15 h6, Motorhalter, Säulenfuß, Motorplatte, Lagerwinkel, Sensorhalter", "Stahl / Alu"),
    ]),
    ("Mechanik-Kaufteile", [
        ("M1", 2, "Systemprofil 40×80 Nut 8, L 600", "Alu"), ("M2", 2, "Systemprofil 40×80 Nut 8, L 480", "Alu"),
        ("M3", 1, "Systemprofil 40×40 Nut 8, L 432 (Säule)", "Alu"), ("M4", 8, "Systemprofil 20×20 Nut 5 (Haube)", "Alu"),
        ("M5", 4, "Gerätefuß Ø36, M8", "NR"), ("M6", 2, "Flanschlager KFL002 (d 15)", "Grauguss"),
        ("M7", 1, "Zahnriemenscheibe GT2 20 Z / 100 Z, Zahnriemen GT2 6 mm", "Alu / PU"),
        ("M8", 1, "Linearführung MGN12, L 395, Wagen MGN12H", "Stahl"),
        ("M9", 1, "Trapezgewindespindel TR8×2, L 340, Mutter, Kupplung 5/8, Lagerbock KFL08", "Stahl / Messing"),
        ("M10", 1, "Passschraube ISO 7379 10×16, 2 Bundbuchsen 10×12×6", "12.9 / iglidur G"),
        ("M11", 1, "Flachgreifer Ø16 M4, Führungsbuchse, Stößel Ø6, Druckfeder", "Stahl"),
        ("M12", 1, "Federband 2×20 und 6 Haltebolzen mit Druckfedern", "1.4310"),
        ("M13", 1, "Spiralschlauch Ø22, ca. 0,5 m", "PVC"), ("M14", 5, "Polycarbonatscheibe 4 mm, Scharniere, Griffleiste", "PC"),
        ("M15", 1, "Schrauben, Nutensteine, Winkel (Satz)", "8.8 / verzinkt"),
    ]),
    ("Antriebe und Elektro", [(b, 1, f"{n}: {t}", "") for b, n, t, _ in BETRIEBSMITTEL]),
]


# =====================================================================
# Ansichten aus der STEP-Baugruppe
# =====================================================================
def step_dreiecke(ohne_scheiben=True):
    import cadquery as cq
    w = cq.importers.importStep(str(STEP))
    T = []
    for s in w.solids().vals():
        bb = s.BoundingBox()
        if ohne_scheiben and min(bb.xlen, bb.ylen, bb.zlen) <= 4.5 and max(bb.xlen, bb.ylen, bb.zlen) > 300:
            continue
        v, f = s.tessellate(0.4, 0.4)
        if not f:
            continue
        v = np.array([(p.x, p.y, p.z) for p in v])
        T.append(v[np.array(f)])
    return T


# =====================================================================
# Seiten
# =====================================================================
def deckblatt(pdf, iso):
    S = pdf.seite(210, 297)
    SEITE[0] += 1
    S.rechteck(20, 10, 200, 287, 0.7)
    S.text(110, 262, "Technische Dokumentation", 6, True, "m")
    S.text(110, 248, "Flaschenöffner Automatik", 9, True, "m")
    S.text(110, 238, "TFO-A: Magazin für 8 Flaschen, Kronkorken-Abfuhr, ESP32-Steuerung", 3.5, ausr="m")
    A_ = Z.einpassen(S, iso, 35, 100, 185, 230)
    Z.zeichne_strecken(A_, iso, 0.22)
    Z.tabelle(S, 40, 88, [("Dokument", 55), ("Angabe", 85)], [
        ("Dokumentnummer", "TFO-A-D01"), ("3D-Modell", "TFO-A_Flaschenoeffner_Automatik.step"),
        ("Steuerungsprogramm", "firmware/flaschenoeffner_automatik"),
        ("Ausgabedatum", Z.DATUM), ("Dokumentenstatus", "Entwurf, nicht freigegeben"),
        ("Erstellt durch", "KI-Entwurf (Prüfung durch Fachkraft erforderlich)"),
    ], 3.0)


def daten(pdf):
    S, y = kopf(pdf, "1  Übersicht und technische Daten")
    y = Z.tabelle(S, 20, y, [("Merkmal", 72), ("Wert", 108)], [
        ("Bauform", "Werkbankgerät mit Schutzhaube, Sternrad-Magazin"),
        ("Abmessungen B × T × H", "600 × 618 × 802 mm (mit Signalsäule)"),
        ("Masse", "ca. 28 kg (Abschätzung)"),
        ("Magazin", "8 Taschen, Charge bis 8 Flaschen"),
        ("Flaschen", "Kronkorken 26 mm, Höhe 171,5 … 270 mm, Ø 57 … 80 mm"),
        ("Taktzeit", "ca. 6 s je Flasche (≈ 50 s je Charge)"),
        ("Höhenanpassung", "automatisch durch Antasten (Magnetstempel)"),
        ("Antriebe", "2 Schrittmotoren NEMA17, Linearantrieb 24 V, Servo 6 V"),
        ("Steuerung", "ESP32, Weboberfläche, optional Alexa (Sinric Pro)"),
        ("Versorgung", "230 V AC / 24 V DC, ca. 120 W"),
        ("Schutzeinrichtung", "Haube mit Türschalter Typ 2 und Not-Halt auf Sicherheitsrelais"),
        ("Kronkorken-Abfuhr", "Magnet, Servo-Abstreifer, Trichter, Schlauch, Behälter ca. 150 Stück"),
    ], 3.0)
    y = Z.ueberschrift(S, y, "1.1 Baugruppen")
    Z.liste(S, y, [
        "Gestell: Rahmen aus Systemprofil 40×80, Deckplatte, Gleitplatte aus PE-UHMW.",
        "Sternrad: zwei Scheiben mit je 8 V-Taschen (90°), Antrieb Schrittmotor über Zahnriemen 5 : 1 "
        "(spielarm), gefederter Führungsbogen drückt jede Flasche mittig in ihre Tasche.",
        "Z-Achse: Säule 40×40 mit Linearführung MGN12, Trapezspindel TR8×2 (selbsthemmend), "
        "Schrittmotor oben.",
        "Öffnerkopf: Hebel und Hakenleiste wie beim Handgerät TFO, Linearantrieb statt Handkraft, "
        "gefederter Magnetstempel als Drehpunkt und Höhenfühler.",
        "Kronkorken-Abfuhr: Servo-Abstreifer, mitfahrender Trichter mit Gabellichtschranke, "
        "Spiralschlauch, Sammelbehälter mit Füllstands-Lichtschranke.",
        "Schutzhaube und Bedienung: Profil 20×20 mit Polycarbonat, Klappe mit Sicherheits-"
        "Türschalter, Bedienpult mit Start, Stopp, Reset und Not-Halt, Signalsäule.",
    ])


def funktion(pdf):
    S, y = kopf(pdf, "2  Funktion und Schrittkette")
    y = Z.absatz(S, 20, y, 180, "Prinzip: Das V-Profil der Sternradtaschen zentriert jede Flasche in "
                 "Umfangsrichtung. Ein anderer Durchmesser verschiebt die Flasche nur radial, also "
                 "entlang der Hakenlippe. Die Lippe liegt deshalb bei jeder Sorte richtig. Die Höhe "
                 "findet die Maschine selbst: Der Kopf fährt ab, bis der gefederte Magnetstempel den "
                 "Kronkorken berührt. Erst danach fährt das Sternrad die letzten 3 mm, und der "
                 "Kronkorkenrand gleitet über die Lippe. Der Stempel wirkt beim Abhebeln als Drehpunkt "
                 "wie bei einem Handöffner, hält die Flasche nieder und fängt den Kronkorken magnetisch.")
    y = Z.ueberschrift(S, y, "2.1 Schrittkette")
    rows = [(s, n, w, t) for s, n, a, w, t, f in SCHRITTE]
    y = Z.tabelle(S, 20, y, [("Schritt", 15), ("Name", 30), ("Weiterschaltbedingung", 105), ("Zeitgrenze", 30)], rows, 2.6)
    y = Z.ueberschrift(S, y, "2.2 Aktionen und Störungen")
    for s, n, a, w, t, f in SCHRITTE:
        y = Z.absatz(S, 20, y, 180, f"{s} {n}: {a}." + (f" Störung: {f}." if f != "–" else ""), 2.7)
    y = Z.ueberschrift(S, y - 1, "2.3 Betriebsarten")
    Z.liste(S, y, [
        "Beladen: Haube öffnen (Antriebe stromlos), bis zu 8 Flaschen einsetzen, Behälter leeren, "
        "Haube schließen, Reset (Sicherheitsrelais), Start.",
        "Automatik: Charge läuft durch, leere Taschen werden über -B5 erkannt und übersprungen.",
        "Störung: rote Leuchte blinkt, Ursache in der Weboberfläche, Quittieren mit Reset.",
    ], 2.7)


def grafcet(pdf):
    S = zeichnungsblatt(pdf, "Ablaufdiagramm", "TFO-A-E00", "Ablaufplan")
    x, y = 125, 270
    S.text(30, 278, "Schrittkette nach GRAFCET (DIN EN 60848), vereinfacht", 3.5, True)
    schritte = [("0", "Grundstellung", "Referenz Z (B2), Sternrad (B4), Hebel aus (B8)"),
                ("1", "Takten", "M2: Vorposition Tasche n"),
                ("2", "Antasten", "M1 ab mit 3 mm/s"),
                ("3", "Feinposition", "M2: +3 mm, M1: +0,5 mm"),
                ("4", "Abhebeln", "M3 ein (1,4 s)"),
                ("5", "Hebel zurück", "M3 aus"),
                ("6", "Kopf hoch", "M1 auf 395 mm"),
                ("7", "Abstreifen", "M4 130° -> 0°"),
                ("8", "Kontrolle", "Zähler +1"),
                ("9", "Weiterschalten", "n = n + 1")]
    trans = ["Start (S1) · Sicherheit OK (K1)", "M2 steht · Flasche (B5)", "Stempel (B3)",
             "M1, M2 stehen", "t > 1,4 s", "Hebel Grundstellung (B8)", "M1 steht", "t > 0,6 s",
             "Kronkorken (B6) + t > 1,5 s", "n < 8 · Behälter frei (B7)"]
    dy = 23.5
    for i, (nr, name, akt) in enumerate(schritte):
        yy = y - i * dy
        if nr == "0":
            S.rechteck(x - 9, yy - 9, x + 9, yy + 9, 0.5)
            S.rechteck(x - 7.5, yy - 7.5, x + 7.5, yy + 7.5, 0.5)
        else:
            S.rechteck(x - 8, yy - 8, x + 8, yy + 8, 0.5)
        S.text(x, yy - 1.8, nr, 5, True, "m")
        S.linie(x + 8, yy, x + 18, yy, 0.35)
        S.rechteck(x + 18, yy - 6, x + 120, yy + 6, 0.35)
        S.text(x + 21, yy + 1, name, 3.0, True)
        S.text(x + 21, yy - 4, akt, 2.6)
        if i < len(schritte) - 1:
            S.linie(x, yy - 8, x, yy - dy + 8, 0.35)
            S.linie(x - 6, yy - dy / 2, x + 6, yy - dy / 2, 0.7)
            S.text(x - 8, yy - dy / 2 - 1.2, trans[i], 2.5, ausr="r")
    # Rücksprung 9 -> 1 und Ende
    yb = y - 9 * dy
    S.linie(x, yb - 8, x, yb - 14, 0.35)
    S.linie(x - 6, yb - 11, x + 6, yb - 11, 0.7)
    S.text(x - 8, yb - 12.2, trans[9], 2.5, ausr="r")
    S.linie(x, yb - 14, x - 95, yb - 14, 0.35)
    S.linie(x - 95, yb - 14, x - 95, y - dy + 12, 0.35)
    S.linie(x - 95, y - dy + 12, x, y - dy + 12, 0.35)
    S.pfeil(x, y - dy + 12, 0)
    S.text(x - 97, (yb + y) / 2, "nächste Tasche", 2.5, winkel=90)
    # Nebenzweige
    bx = 262
    S.text(bx, 270, "Neben- und Fehlerzweige", 3.5, True)
    for i, (k, t) in enumerate((
            ("aus 1", "B5 = 0 (Tasche leer): direkt zu 9, Zähler \"übersprungen\" +1"),
            ("aus 2", "unterste Lage ohne B3: Warnung \"kein Kronkorken\", weiter mit 6"),
            ("aus 8", "kein B6 in 1,5 s: Warnung \"Kronkorken nicht erkannt\", weiter mit 9"),
            ("aus 9", "B7 = 1: Zustand \"Behälter voll\", nach Leeren + Reset weiter mit 9"),
            ("aus 9", "n = 8: Zustand \"Fertig\", grün blinkt, neue Charge mit Start"),
            ("jeder", "K1 = 0 (Haube auf / Not-Halt): Antriebe stromlos (Hardware), Zustand"),
            ("", "\"Schutz offen\", nach Schließen + Reset neue Referenzfahrt (Schritt 0)"),
            ("jeder", "Zeitgrenze überschritten: Störung, Reset -> Grundstellung"),
            ("1 … 9", "Stopp (S2): Störung \"Stopp durch Bediener\""))):
        S.text(bx, 260 - i * 7, k, 2.8, True)
        S.text(bx + 14, 260 - i * 7, t, 2.8)
    S.text(bx, 180, "Legende", 3.2, True)
    for i, t in enumerate(("Doppelrahmen = Anfangsschritt, Rahmen = Schritt", "Querstrich = Transition mit Bedingung",
                           "Rechteck rechts = Aktion (nicht speichernd)", "· = logisches UND")):
        S.text(bx, 173 - i * 6, t, 2.8)


def sicherheit(pdf):
    S, y = kopf(pdf, "3  Sicherheitskonzept")
    y = Z.absatz(S, 20, y, 180, "Grundlage: Maschinenverordnung (EU) 2023/1230 bzw. Maschinenrichtlinie, "
                 "EN ISO 12100 (Risikobeurteilung), EN ISO 13849-1 (Sicherheitsfunktionen), EN ISO 14119 "
                 "(Verriegelung), EN ISO 13850 (Not-Halt), EN 60204-1 (elektrische Ausrüstung). Die "
                 "folgende Einschätzung ist ein Entwurf und ersetzt keine Risikobeurteilung durch "
                 "eine fachkundige Person.")
    y = Z.ueberschrift(S, y, "3.1 Gefährdungen und Maßnahmen")
    y = Z.tabelle(S, 20, y, [("Gefährdung", 52), ("Ort", 40), ("Maßnahme", 88)], [
        ("Quetschen, Scheren", "Sternrad / Führungsbogen", "feststehende Haube, Klappe verriegelt"),
        ("Quetschen", "Kopf (Z-Achse, Hebel)", "Haube; Leistung über -K1 abgeschaltet"),
        ("Glasbruch, Splitter", "Station", "Haube aus PC 4 mm, begrenzte Kräfte"),
        ("Schneiden", "Hakenlippe", "nur bei offener Haube zugänglich, Handschuhe"),
        ("Elektrischer Schlag", "Schaltkasten 230 V", "Schutzklasse I, PE, -Q1, Tür nur mit Werkzeug"),
        ("Unerwarteter Anlauf", "alle Antriebe", "manueller Start -K1, Reset + Start nötig"),
    ], 2.7)
    y = Z.ueberschrift(S, y, "3.2 Sicherheitsfunktionen")
    y = Z.tabelle(S, 20, y, [("SF", 12), ("Auslöser", 50), ("Reaktion", 70), ("PLr (Entwurf)", 48)], [
        ("SF1", "Klappe geöffnet (-B1)", "-K1 schaltet 24 V Leistung ab (STO-ähnlich)", "PL c, Kat. 3 angestrebt"),
        ("SF2", "Not-Halt betätigt (-S0)", "wie SF1, Stoppkategorie 0", "PL c, Kat. 3 angestrebt"),
        ("SF3", "Wiederanlauf", "nur mit Reset (-S3) nach Schließen", "manueller Start -K1"),
    ], 2.7)
    y = Z.ueberschrift(S, y, "3.3 Umsetzung")
    Z.liste(S, y, [
        "Türschalter und Not-Halt jeweils mit 2 zwangsöffnenden Öffnern, zweikanalig auf das "
        "Sicherheitsrelais -K1 mit Querschlusserkennung.",
        "Die Freigabekontakte von -K1 (13-14, 23-24) schalten die 24-V-Leistungsschiene für "
        "Schrittmotortreiber, H-Brücke und Servo-Wandler. Der ESP32 bleibt versorgt und liest "
        "über den Meldekontakt nur den Zustand.",
        "Selbsthemmende Spindel TR8×2: Der Kopf sinkt bei Abschaltung nicht ab.",
        "Restrisiko: Der Nachlauf des Sternrads ist gering (Masse klein, Schrittmotor). Die "
        "Zuhaltung entfällt deshalb. Zu prüfen: Nachlaufzeit < Zugangszeit.",
        "Validierung: PL mit SISTEMA nachrechnen, Prüfprotokoll (Funktion SF1 bis SF3, "
        "Querschluss, Drahtbruch) vor der ersten Inbetriebnahme.",
    ], 2.8)


def io_liste(pdf):
    S, y = kopf(pdf, "4  Betriebsmittel und I/O-Liste")
    y = Z.tabelle(S, 20, y, [("BMK", 14), ("Benennung", 50), ("Typ / Daten", 88), ("Anschluss", 28)],
                  BETRIEBSMITTEL, 2.35)
    y = Z.ueberschrift(S, y + 2, "I/O-Belegung ESP32")
    Z.tabelle(S, 20, y, [("Adr.", 12), ("GPIO", 22), ("BMK", 20), ("Signal", 55), ("Bemerkung", 71)], IO, 2.35)


# ---------------------------------------------------------------- Stromlaufplan
def klemme(S, x, y, t=""):
    S.kreis(x, y, 0.8, 0.25, fuellen=1.0)
    if t:
        S.text(x + 1.2, y + 1.0, t, 1.8)


def oeffner(S, x, y, t=""):
    """Öffner senkrecht, oben bei y, unten bei y-10."""
    S.linie(x, y, x, y - 3, 0.35)
    S.linie(x, y - 7, x, y - 10, 0.35)
    S.linie(x - 3, y - 3, x + 0.6, y - 7.5, 0.35)
    S.linie(x, y - 3, x - 3, y - 3, 0.35)
    if t:
        S.text(x + 2, y - 6, t, 2.2)


def schliesser(S, x, y, t=""):
    S.linie(x, y, x, y - 3, 0.35)
    S.linie(x, y - 7, x, y - 10, 0.35)
    S.linie(x, y - 7, x - 3, y - 3.5, 0.35)
    if t:
        S.text(x + 2, y - 6, t, 2.2)


def geraet(S, x0, y0, x1, y1, bmk, name, pins_l=(), pins_r=(), pins_o=(), pins_u=()):
    S.rechteck(x0, y0, x1, y1, 0.5)
    S.text((x0 + x1) / 2, (y0 + y1) / 2 + 1.5, bmk, 3.0, True, "m")
    for i, z in enumerate(name.split("\n")):
        S.text((x0 + x1) / 2, (y0 + y1) / 2 - 3 - i * 3.2, z, 2.3, ausr="m")
    out = {}
    for pins, seite in ((pins_l, "l"), (pins_r, "r"), (pins_o, "o"), (pins_u, "u")):
        n = len(pins)
        for i, p in enumerate(pins):
            if seite in "lr":
                yy = y1 - (y1 - y0) * (i + 1) / (n + 1)
                xx = x0 if seite == "l" else x1
                S.text(xx + (1 if seite == "l" else -1), yy - 0.9, p, 1.9, ausr="l" if seite == "l" else "r")
            else:
                xx = x0 + (x1 - x0) * (i + 1) / (n + 1)
                yy = y1 if seite == "o" else y0
                S.text(xx, yy + (-3 if seite == "o" else 1.2), p, 1.9, ausr="m")
            out[p] = (xx, yy)
    return out


def draht(S, pts, w=0.3, t=None):
    S.pfad(pts, w)
    if t:
        (xa, ya), (xb, yb) = pts[0], pts[1]
        S.text((xa + xb) / 2 + 0.8, (ya + yb) / 2 + 0.8, t, 1.8, grau=0.3)


def stromlauf_1(pdf):
    S = zeichnungsblatt(pdf, "Einspeisung, Sicherheitskreis", "TFO-A-E01", "Stromlaufplan", "1/3")
    S.text(30, 278, "Einspeisung 230 V, Netzteile, Sicherheitskreis", 3.5, True)
    # Netz
    for i, (t, y) in enumerate((("L", 255), ("N", 249), ("PE", 243))):
        klemme(S, 30, y, t)
        S.linie(30, y, 45, y, 0.35)
    S.rechteck(45, 240, 57, 258, 0.5)
    S.text(51, 260, "-Q1", 2.6, True, "m")
    S.text(51, 236, "Hauptschalter", 2.2, ausr="m")
    S.linie(57, 255, 70, 255, 0.35)
    S.rechteck(70, 253.5, 80, 256.5, 0.35)
    S.text(75, 258, "-F1 T2A", 2.2, ausr="m")
    S.linie(80, 255, 95, 255, 0.35)
    S.linie(57, 249, 95, 249, 0.35)
    S.linie(45, 243, 95, 243, 0.35)
    t1 = geraet(S, 95, 236, 125, 262, "-T1", "Netzteil\n24 V 150 W", ("L", "N", "PE"), ("+24V", "0V"))
    # 24-V-Schienen
    y24, y0v, y24l = 225, 120, 205
    S.linie(t1["+24V"][0], t1["+24V"][1], 140, t1["+24V"][1], 0.35)
    S.linie(140, t1["+24V"][1], 140, y24, 0.35)
    S.rechteck(138.5, 228, 141.5, 236, 0.35)
    S.text(143, 231, "-F2 T1A", 2.2)
    S.linie(140, y24, 400, y24, 0.5)
    S.text(400, y24 + 1.5, "+24V Steuerung (L+)", 2.4, ausr="r")
    S.linie(t1["0V"][0], t1["0V"][1], 132, t1["0V"][1], 0.35)
    S.linie(132, t1["0V"][1], 132, y0v, 0.35)
    S.linie(132, y0v, 400, y0v, 0.5)
    S.text(400, y0v - 3.5, "0V (M)", 2.4, ausr="r")
    # Sicherheitskreis: zwei Kanäle über -S0 und -B1 auf -K1
    k1 = geraet(S, 230, 140, 300, 200, "-K1", "Sicherheitsrelais\n2-kanalig, man. Start",
                pins_o=("A1", "S11", "S12", "S21", "S22", "S34"), pins_u=("A2", "13", "14", "23", "24", "41", "42"))
    S.linie(k1["A1"][0], y24, k1["A1"][0], k1["A1"][1], 0.3)
    S.linie(k1["A2"][0], k1["A2"][1], k1["A2"][0], y0v, 0.3)
    for kanal, (sa, sb, x) in enumerate((("S11", "S12", 165), ("S21", "S22", 185))):
        xa, ya = k1[sa]
        xb, yb = k1[sb]
        S.linie(xa, ya, xa, 218, 0.3)
        S.linie(xa, 218, x, 218, 0.3)
        oeffner(S, x, 218, "-S0" if kanal == 0 else "")
        oeffner(S, x, 208, "-B1" if kanal == 0 else "")
        S.linie(x, 198, x, 196, 0.3)
        S.linie(x, 196, xb, 196, 0.3)
        S.linie(xb, 196, xb, yb, 0.3)
    S.text(150, 214, "Not-Halt", 2.2)
    S.text(150, 204, "Türschalter", 2.2)
    xs, ys = k1["S34"]
    S.linie(xs, ys, xs, 212, 0.3)
    S.linie(xs, 212, 320, 212, 0.3)
    schliesser(S, 320, 212, "-S3 Reset")
    S.linie(320, 202, 320, y24 - 0.1, 0.0)
    S.linie(320, 212, 320, y24, 0.3)
    # Freigabepfade in REIHE (redundant): +24 V -> 13-14 -> 23-24 -> F3 -> +24 V Leistung
    S.linie(k1["13"][0], k1["13"][1], k1["13"][0], 130, 0.3)
    S.linie(k1["13"][0], 130, 215, 130, 0.3)
    S.linie(215, 130, 215, y24, 0.3)
    S.pfad([k1["14"], (k1["14"][0], 134), (k1["23"][0], 134), k1["23"]], 0.3)
    S.text((k1["14"][0] + k1["23"][0]) / 2, 135.2, "Brücke", 1.6, ausr="m")
    S.linie(k1["24"][0], k1["24"][1], k1["24"][0], 130, 0.3)
    S.linie(k1["24"][0], 130, 340, 130, 0.3)
    S.rechteck(338.5, 132 + 18, 341.5, 132 + 26, 0.35)
    S.linie(340, 130, 340, y24l, 0.3)
    S.text(343, 153, "-F3 T4A", 2.2)
    S.linie(340, y24l, 400, y24l, 0.5)
    S.text(400, y24l + 1.5, "+24V Leistung (L+ geschaltet)", 2.4, ausr="r")
    S.linie(k1["41"][0], k1["41"][1], k1["41"][0], 128, 0.3)
    S.text(k1["41"][0] + 1, 126, "Meldekontakt -> E4", 2.0)
    # DC/DC-Wandler
    t2 = geraet(S, 40, 150, 75, 175, "-T2", "DC/DC\n24 -> 5 V", ("+24V", "0V"), ("+5V", "GND"))
    S.linie(t2["+24V"][0], t2["+24V"][1], 35, t2["+24V"][1], 0.3)
    S.linie(35, t2["+24V"][1], 35, y24, 0.3)
    S.linie(35, y24, 140, y24, 0.5)
    S.linie(t2["0V"][0], t2["0V"][1], 37, t2["0V"][1], 0.3)
    S.linie(37, t2["0V"][1], 37, y0v, 0.3)
    S.linie(37, y0v, 132, y0v, 0.5)
    S.text(t2["+5V"][0] + 2, t2["+5V"][1] + 1, "-> -A1, -A2, -A6 (Blatt 3)", 2.0)
    t3 = geraet(S, 360, 150, 395, 175, "-T3", "DC/DC\n24 -> 6 V", ("+24V", "0V"), ())
    S.linie(t3["+24V"][0], t3["+24V"][1], 355, t3["+24V"][1], 0.3)
    S.linie(355, t3["+24V"][1], 355, y24l, 0.3)
    S.linie(t3["0V"][0], t3["0V"][1], 357, t3["0V"][1], 0.3)
    S.linie(357, t3["0V"][1], 357, y0v, 0.3)
    S.text(378, 146, "+6V -> Servo -M4", 2.0, ausr="m")
    S.text(30, 100, "Hinweise: Leitungsquerschnitte 230 V: 1,5 mm², 24 V Leistung: 0,75 mm², Signale: 0,25 mm².", 2.4)
    S.text(30, 95, "Schutzleiter an Deckplatte, Rahmen und Schaltkasten. Kanäle -S0/-B1 getrennt verlegen.", 2.4)


def stromlauf_2(pdf):
    S = zeichnungsblatt(pdf, "Antriebe", "TFO-A-E02", "Stromlaufplan", "2/3")
    S.text(30, 278, "Antriebe: Schrittmotoren, Linearantrieb, Servo", 3.5, True)
    yl, y0v = 255, 110
    S.linie(30, yl, 400, yl, 0.5)
    S.text(30, yl + 1.5, "+24V Leistung (von -K1, Blatt 1)", 2.4)
    S.linie(30, y0v, 400, y0v, 0.5)
    S.text(30, y0v - 3.5, "0V", 2.4)
    for i, (bmk, mot, name, step) in enumerate((("-A3", "-M1", "Z-Achse", "GPIO16/17"),
                                                ("-A4", "-M2", "Sternrad", "GPIO18/19"))):
        x = 50 + i * 95
        d = geraet(S, x, 175, x + 55, 225, bmk, f"TMC2209\n{name}", ("STEP", "DIR", "EN", "GND"), ("A1", "A2", "B1", "B2"),
                   pins_o=("VM",), pins_u=("GND ",))
        S.linie(d["VM"][0], d["VM"][1], d["VM"][0], yl, 0.3)
        S.linie(d["GND "][0], d["GND "][1], d["GND "][0], y0v, 0.3)
        for p in ("STEP", "DIR", "EN"):
            S.linie(d[p][0], d[p][1], d[p][0] - 8, d[p][1], 0.3)
        S.text(x - 9, d["STEP"][1] + 2.5, step + ", EN GPIO21", 1.9, ausr="r")
        mx, my = x + 27, 150
        S.kreis(mx, my, 9, 0.5)
        S.text(mx, my - 1.5, "M", 4, True, "m")
        S.text(mx, my - 14, f"{mot} NEMA17", 2.4, ausr="m")
        for j, p in enumerate(("A1", "A2", "B1", "B2")):
            px, py = d[p]
            S.pfad([(px, py), (px + 6 + j * 2, py), (px + 6 + j * 2, 165), (mx - 6 + j * 4, 165), (mx - 6 + j * 4, my + 8)], 0.3)
    h = geraet(S, 250, 180, 300, 225, "-A5", "H-Brücke\n24 V 5 A", ("IN A", "IN B", "GND"), ("OUT1", "OUT2"),
               pins_o=("VM",), pins_u=("GND ",))
    S.linie(h["VM"][0], h["VM"][1], h["VM"][0], yl, 0.3)
    S.linie(h["GND "][0], h["GND "][1], h["GND "][0], y0v, 0.3)
    for p, g in (("IN A", "GPIO22"), ("IN B", "GPIO23")):
        S.linie(h[p][0], h[p][1], h[p][0] - 8, h[p][1], 0.3)
        S.text(h[p][0] - 9, h[p][1] - 0.8, g, 1.9, ausr="r")
    S.kreis(330, 150, 9, 0.5)
    S.text(330, 148.5, "M", 4, True, "m")
    S.text(330, 136, "-M3 Linearantrieb 24 V", 2.4, ausr="m")
    S.pfad([h["OUT1"], (318, h["OUT1"][1]), (318, 158), (326, 158)], 0.3)
    S.pfad([h["OUT2"], (342, h["OUT2"][1]), (342, 158), (334, 158)], 0.3)
    S.text(345, 175, "Endschalter intern", 2.0)
    s = geraet(S, 355, 190, 395, 225, "-M4", "Servo\nMG996R", ("PWM", "+6V", "GND"))
    S.linie(s["PWM"][0], s["PWM"][1], s["PWM"][0] - 6, s["PWM"][1], 0.3)
    S.text(s["PWM"][0] - 7, s["PWM"][1] + 1.5, "GPIO15", 1.9, ausr="r")
    S.text(s["+6V"][0] - 7, s["+6V"][1] + 1.5, "-T3", 1.9, ausr="r")
    S.linie(s["GND"][0], s["GND"][1], s["GND"][0] - 3, s["GND"][1], 0.3)
    S.linie(s["GND"][0] - 3, s["GND"][1], s["GND"][0] - 3, y0v, 0.3)
    S.text(30, 95, "Strom TMC2209 über Vref einstellen: Z 1,2 A, Sternrad 1,5 A (Standalone, MS1/MS2 = 1/8 Schritt).", 2.4)
    S.text(30, 90, "Motorleitungen geschirmt, Schirm einseitig an PE im Schaltkasten.", 2.4)


def stromlauf_3(pdf):
    S = zeichnungsblatt(pdf, "Steuerung, Sensoren", "TFO-A-E03", "Stromlaufplan", "3/3")
    S.text(30, 278, "ESP32, Eingänge (24 V über Optokoppler), Ausgänge (Relais)", 3.5, True)
    y24, y0v = 262, 95
    S.linie(30, y24, 400, y24, 0.5)
    S.text(30, y24 + 1.5, "+24V Steuerung (Blatt 1)", 2.4)
    S.linie(30, y0v, 400, y0v, 0.5)
    S.text(30, y0v - 3.5, "0V", 2.4)
    ein = [(e, g, b, s) for e, g, b, s, _ in IO if e.startswith("E")]
    opto = geraet(S, 40, 140, 160, 175, "-A2", "Optokoppler-Platine 11-fach",
                  pins_o=tuple(e for e, *_ in ein), pins_r=("OUT", "3V3", "GND"), pins_u=("0V",))
    S.linie(opto["0V"][0], opto["0V"][1], opto["0V"][0], y0v, 0.3)
    for e, g, b, s in ein:
        x, y = opto[e]
        yt = 220
        S.linie(x, y, x, yt, 0.3)
        if b in ("-S1", "-S3"):
            schliesser(S, x, yt + 10)
        elif b == "-S2":
            oeffner(S, x, yt + 10)
        elif b == "-K1":
            schliesser(S, x, yt + 10)
        else:
            S.rechteck(x - 3, yt, x + 3, yt + 10, 0.4)
            S.linie(x - 3, yt + 10, x + 3, yt, 0.25)
        S.linie(x, yt + 10, x, y24, 0.3)
        S.text(x, yt + 13.5 + (3 if int(e[1:]) % 2 else 0), b, 2.0, ausr="m")
        S.text(x - 1.2, 182, s, 1.8, winkel=90)
    S.text(40, 247, "Sensoren PNP 3-Leiter: BN +24 V, BU 0 V, BK Signal", 2.2)
    esp = geraet(S, 200, 130, 260, 230, "-A1", "ESP32-DevKit\n(WROOM-32)",
                 pins_l=tuple(f"{g.split()[1]}" for e, g, b, s, _ in IO if e.startswith("E")),
                 pins_r=("16", "17", "18", "19", "21", "22", "23", "15", "4", "5", "2", "12"), pins_u=("5V", "GND"))
    S.linie(opto["OUT"][0], opto["OUT"][1], 185, opto["OUT"][1], 0.3)
    S.linie(185, opto["OUT"][1], 185, 225, 0.3)
    S.text(176, 228, "E1 … E11", 2.0)
    for e, g, b, s, _ in IO:
        if e.startswith("E"):
            px, py = esp[g.split()[1]]
            S.linie(185, py, px, py, 0.3)
    S.text(esp["5V"][0], esp["5V"][1] - 5, "von -T2", 2.0, ausr="m")
    zuord = {"16": "-A3 STEP", "17": "-A3 DIR", "18": "-A4 STEP", "19": "-A4 DIR", "21": "-A3/-A4 EN",
             "22": "-A5 IN A", "23": "-A5 IN B", "15": "-M4 PWM"}
    for p, t in zuord.items():
        x, y = esp[p]
        S.linie(x, y, x + 25, y, 0.3)
        S.text(x + 26, y - 0.8, t + " (Blatt 2)", 1.9)
    rel = geraet(S, 300, 120, 340, 165, "-A6", "Relais\n4-fach", ("IN1", "IN2", "IN3", "IN4"), ("K1", "K2", "K3", "K4"))
    for p, inn in (("4", "IN1"), ("5", "IN2"), ("2", "IN3"), ("12", "IN4")):
        S.pfad([esp[p], (283, esp[p][1]), (283, rel[inn][1]), rel[inn]], 0.3)
    for i, (k, t) in enumerate((("K1", "-P1 grün"), ("K2", "-P1 gelb"), ("K3", "-P1 rot"), ("K4", "-S1 Leuchtmelder"))):
        x, y = rel[k]
        S.linie(x, y, 360, y, 0.3)
        S.kreis(364, y, 3, 0.4)
        S.linie(361.9, y - 2.1, 366.1, y + 2.1, 0.3)
        S.linie(361.9, y + 2.1, 366.1, y - 2.1, 0.3)
        S.linie(367, y, 375, y, 0.3)
        S.linie(375, y, 375, y0v, 0.3)
        S.text(371, y + 3.5, t, 1.9)
    S.linie(352, 160, 352, y24, 0.3)
    S.text(354, 168, "+24V an Relaiskontakte", 1.9)


def ansichten(pdf, T):
    S = zeichnungsblatt(pdf, "Zusammenbau", "TFO-A-000", "Zeichnung", "1/2", "1:10")
    m = 0.1
    AV = Z.Ansicht(S, 85, 172, m)
    AD = Z.Ansicht(S, 85, 120, m)
    AL = Z.Ansicht(S, 205, 172, m)
    Z.zeichne_strecken(AV, Z.kanten_sichtbar(T, T, "vorne", res=0.6, eps=1.2), 0.25)
    Z.zeichne_strecken(AD, Z.kanten_sichtbar(T, T, "oben", res=0.6, eps=1.2), 0.25)
    Z.zeichne_strecken(AL, Z.kanten_sichtbar(T, T, "links", res=0.6, eps=1.2), 0.25)
    iso = Z.kanten_sichtbar(T, T, "iso", res=0.6, eps=1.2)
    AI = Z.einpassen(S, iso, 268, 62, 405, 272)
    Z.zeichne_strecken(AI, iso, 0.22)
    S.text(336, 278, "Isometrie (ohne Maßstab, ohne Scheiben)", 2.8, ausr="m")
    x0, x1, y0, y1 = A.RAHMEN
    AV.mass((x0, 0), (x1, 0), "h", -7)
    AV.mass((x0, -8), (x0, 794), "v", -10, text="802")
    AV.mass((x0, 0), (x0, A.HAUBE_Z + 20), "v", -20)
    AD.mass((x1, y0 - 58), (x1, y1), "v", 8, text="618")
    AL.mass((-y1, 0), (-(y0 - 58), 0), "h", -7, text="618")
    AL.mass((-(y0 - 58), 0), (-(y0 - 58), A.Z0), "v", 8)
    Z.notizen(S, 25, 52, [
        "Ansichten aus der STEP-Baugruppe TFO-A_Flaschenoeffner_Automatik.step (Scheiben ausgeblendet).",
        "Teile und Maße: siehe STEP-Datei (Produktnamen = Stücklistenbezeichnung) und Stückliste.",
        "Alle Maße in mm. Grundstellung: Kopf in Arbeitshöhe NRW 0,5 l.",
    ], 2.5, "Hinweise")


def stueckliste(pdf):
    S = zeichnungsblatt(pdf, "Stückliste", "TFO-A-000", "Stückliste", "2/2")
    x0, y = 20, 287
    sp = [("Pos.", 16), ("Menge", 14), ("Benennung", 250), ("Werkstoff", 110)]
    zh = 3.6
    def zeile(w, fett=False, grau=None):
        nonlocal y
        if grau is not None:
            S.rechteck(x0, y - zh, x0 + 390, y, 0, fuellen=grau)
        x = x0
        for (k, b), t in zip(sp, w):
            S.text(x + 1.5, y - zh + 1.2, str(t), 2.3, fett)
            x += b
        S.linie(x0, y - zh, x0 + 390, y - zh, 0.15)
        y -= zh
    zeile([k for k, _ in sp], True, 0.88)
    for gruppe, eintraege in STUECKLISTE:
        zeile(["", "", gruppe, ""], True, 0.95)
        for e in eintraege:
            zeile(list(e))


def inbetriebnahme(pdf):
    S, y = kopf(pdf, "5  Inbetriebnahme und Programmierung")
    y = Z.ueberschrift(S, y, "5.1 Programm aufspielen")
    y = Z.liste(S, y, [
        "Arduino IDE 2 installieren, Boardverwalter: \"esp32\" von Espressif (Core ab 3.0).",
        "Bibliothek \"FastAccelStepper\" (gin66) über den Bibliotheksverwalter installieren; für "
        "Alexa zusätzlich \"SinricPro\" und ALEXA_AKTIV = 1 in konfiguration.h.",
        "zugang_beispiel.h nach zugang.h kopieren, WLAN-Daten eintragen (zugang.h wird nicht "
        "ins Repository übertragen).",
        "Board \"ESP32 Dev Module\" wählen, flaschenoeffner_automatik.ino hochladen, serielle "
        "Ausgabe mit 115200 Baud prüfen.",
        "Weboberfläche: http://flaschenoeffner.local (Status, Start, Stopp, Reset).",
    ], 2.8, True)
    y = Z.ueberschrift(S, y, "5.2 Erstinbetriebnahme (Haube offen, Leistung aus)")
    y = Z.liste(S, y, [
        "Verdrahtung nach Stromlaufplan prüfen, Isolationsmessung 230-V-Kreis, PE-Durchgang.",
        "Ohne Leistung (-K1 aus): alle Eingänge E1 … E11 einzeln betätigen und in der seriellen "
        "Ausgabe bzw. Weboberfläche kontrollieren.",
        "Sicherheitsfunktionen SF1 bis SF3 prüfen: Klappe öffnen und Not-Halt drücken, -K1 muss "
        "abfallen. Querschluss Kanal 1/2 simulieren.",
        "Treiberströme über Vref einstellen. Drehrichtungen prüfen: Z positiv = aufwärts, "
        "Sternrad negativ = im Uhrzeigersinn von oben.",
        "Referenzfahne Sternrad so ausrichten, dass Tasche 0 bei Referenz genau in der Station "
        "steht. Z_REFERENZ_MM mit Messschieber an der Drehachse bestimmen.",
        "Hakenleiste in den Langlöchern einstellen: Lippe ca. 1 mm unter dem Kronkorkenrand, "
        "ohne das Glas zu berühren (wie beim Handgerät).",
        "Probelauf mit einer Flasche je Sorte (kleinste und größte), dann volle Charge. Zeiten "
        "T_HEBELN und Servowinkel bei Bedarf anpassen.",
    ], 2.8, True)
    y = Z.ueberschrift(S, y, "5.3 Offene Punkte (Prototyp)")
    Z.liste(S, y, [
        "Abhebekraft und Hebelweg am Muster messen, ggf. Linearantrieb mit mehr Kraft wählen.",
        "Abstreifen: Haltekraft Magnet gegen Schubkraft Servo abstimmen.",
        "Firmware ist ungetestet (ohne Hardware geschrieben), Kompilieren und Funktionstest stehen aus.",
        "Risikobeurteilung und PL-Nachweis (SISTEMA) durch Fachkraft.",
    ], 2.8)


def main():
    print("Lese STEP-Baugruppe und berechne Ansichten …")
    T = step_dreiecke()
    iso = Z.kanten_sichtbar(T, T, "iso", res=0.7, eps=1.2)
    pdf = Z.PDF()
    deckblatt(pdf, iso)
    daten(pdf)
    funktion(pdf)
    grafcet(pdf)
    sicherheit(pdf)
    io_liste(pdf)
    stromlauf_1(pdf)
    stromlauf_2(pdf)
    stromlauf_3(pdf)
    ansichten(pdf, T)
    stueckliste(pdf)
    inbetriebnahme(pdf)
    pdf.speichern(AUSGABE)
    print(f"{AUSGABE.name}: {len(pdf.seiten)} Seiten")
    import os
    pruef = os.environ.get("TFO_SVG")
    if pruef:
        Path(pruef).mkdir(parents=True, exist_ok=True)
        for i, s in enumerate(pdf.seiten, 1):
            (Path(pruef) / f"a_seite_{i:02d}.svg").write_text(s.als_svg(), encoding="utf-8")


if __name__ == "__main__":
    main()
