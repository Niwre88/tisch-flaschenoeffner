"""
Technische Dokumentation des Flaschenöffner-Automaten TFO-A, Index B (PDF).

Inhalt: Deckblatt, technische Daten, Bedienung, Funktion und Schrittkette,
GRAFCET, Sicherheitskonzept, Betriebsmittel, I/O-Liste, Stromlaufplan (3 Blätter),
Zusammenbau aus der STEP-Baugruppe, Stückliste (aus dem 3D-Modell gezählt),
Inbetriebnahme.

Nutzt die PDF-Funktionen aus ../zeichnungen.py.   Aufruf:  python doku_automatik.py
"""
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent))
sys.path.insert(0, str(HIER))
import zeichnungen as Z  # noqa: E402
import modell_a as A     # noqa: E402

AUSGABE = HIER / "Technische_Dokumentation_TFO-A.pdf"
STEP = HIER / "TFO-A_Flaschenoeffner_Automatik.step"
TITEL = "Flaschenöffner-Automat TFO-A"
DOKNR = "TFO-A-D01 Index B"
SEITE = [0]
WARNUNGEN = []
Z.DATUM = "2026-11-23"          # Stand Index B


def kopf(pdf, titel):
    S = pdf.seite(210, 297)
    SEITE[0] += 1
    S.linie(20, 282, 200, 282, 0.3)
    S.text(20, 284.5, f"Technische Dokumentation  {TITEL}", 2.6, grau=0.35)
    S.text(200, 284.5, DOKNR, 2.6, ausr="r", grau=0.35)
    S.linie(20, 15, 200, 15, 0.3)
    S.text(20, 10.5, f"Entwurf, Stand {Z.DATUM}", 2.4, grau=0.35)
    S.text(200, 10.5, f"Seite {SEITE[0]}", 2.4, ausr="r", grau=0.35)
    S.text(20, 268, titel, 6, True)
    return S, 256


def zeichnungsblatt(pdf, titel, nr, art="Zeichnung", blatt="1/1", massstab="–"):
    SEITE[0] += 1
    S = Z.blatt(pdf, "A3q", titel, nr, massstab, "–", "–", "", TITEL, blatt, toleranz=False)
    x0 = 420 - 10 - 180            # Dokumentenart im Schriftfeld überschreiben
    S.rechteck(x0 + 35.2, 10.2, x0 + 69.8, 17.6, 0, fuellen=1.0)
    S.text(x0 + 36.2, 11.6, art, 2.2)
    return S


def tab(S, x, y, spalten, zeilen, h=2.8, seite=""):
    """Tabelle wie Z.tabelle, prüft aber, ob jeder Text in seine Spalte passt."""
    for z in zeilen:
        for (k, b), t in zip(spalten, z):
            if Z.tb(str(t), h) > b - 2.5:
                WARNUNGEN.append(f"{seite}: Spalte '{k}' zu schmal für '{t}'")
    return Z.tabelle(S, x, y, spalten, zeilen, h)


# =====================================================================
# Daten
# =====================================================================
SCHRITTE = [
    # Schritt, Name, Aktion, Weiterschaltbedingung, Zeitgrenze, Abweichung
    ("S0", "Referenz", "Z-Achse auf bis -B2, Sternrad im Uhrzeigersinn bis -B4, Linearantrieb ein, Servo 0°",
     "-B2 und -B4 erreicht", "30 s", "Referenz nicht gefunden -> Störung"),
    ("S1", "Takten", "nächste volle Tasche auf Vorposition (3 mm vor der Station)",
     "-M2 steht und -B6 = 1", "15 s", "-B6 = 0: Tasche leer, nächste Tasche"),
    ("S2", "Antasten", "Z ab: Eilgang bis 15 mm über der letzten Höhe, dann 10 mm/s",
     "-B3 = 1, danach 0,5 mm anheben", "Z = 251 mm", "ohne Kontakt: Warnung, weiter S7"),
    ("S3", "Prüfen", "Induktivsensor im Stempel fragt Metall ab",
     "-B8 = 1 (Kronkorken)", "–", "-B8 = 0: nicht hebeln, weiter S7"),
    ("S4", "Feinposition", "Sternrad die letzten 3 mm, Kronkorkenrand gleitet über die Lippe",
     "-M2 steht", "–", "–"),
    ("S5", "Abhebeln", "Haftmagnet -Y2 ein, Linearantrieb fährt aus, Hebel hebt Kronkorken ab",
     "t > T_HEBELN", "1,4 s", "–"),
    ("S6", "Hebel zurück", "Linearantrieb fährt ein, Kronkorken haftet am Stempel",
     "-B10 = 1", "2,5 s", "Hebel nicht in Grundstellung -> Störung"),
    ("S7", "Kopf hoch", "Z-Achse in sichere Höhe 400 mm (über allen Flaschen)",
     "-M1 steht", "15 s", "Z erreicht Höhe nicht -> Störung"),
    ("S8", "Schwenken", "Servo -M4 schwenkt Stempelarm 90° über den Trichter",
     "t > T_SCHWENK", "0,7 s", "–"),
    ("S9", "Abwurf", "Haftmagnet aus, Kronkorken fällt durch Trichter auf die Rutsche",
     "Flanke -B11", "1,5 s", "kein -B11: Warnung, weiter"),
    ("S10", "Zurückschwenken", "Servo 0°, Tasche als \"offen\" speichern",
     "t > T_SCHWENK", "0,7 s", "–"),
    ("S11", "Ausgabe", "Sternrad 4 Taschen (180°) weiter: offene Flasche steht im Bedienfach",
     "-M2 steht, -B4 plausibel", "15 s", "Lage falsch -> Störung, neue Referenz"),
]

BETRIEBSMITTEL = [
    ("-Q1", "Hauptschalter", "2-polig, 10 A, abschließbar", "230 V AC"),
    ("-F1", "Feinsicherung primär", "T 2 A", "230 V AC"),
    ("-T1", "Netzteil", "24 V DC, 150 W (6,5 A)", "230 V -> 24 V"),
    ("-F2", "Sicherung Steuerung", "T 1 A", "+24 V"),
    ("-F3", "Sicherung Leistung", "T 4 A", "über -K1, -K2"),
    ("-T2", "DC/DC-Wandler", "24 V -> 5 V, 2 A", "-A1, -A2, -A7"),
    ("-T3", "DC/DC-Wandler", "24 V -> 6 V, 3 A", "-M4 (geschaltet)"),
    ("-K1", "Not-Halt-Relais", "2-kanalig, Querschluss, man. überwachter Start", "-S0, -S4"),
    ("-K2", "Schutztürwächter", "2-kanalig, Querschluss, automatischer Start", "-B1a, -B1b"),
    ("-S0", "Not-Halt", "Pilztaster, 2 Öffner, EN ISO 13850", "-K1"),
    ("-B1a", "Sicherheitsschalter Klappe", "Typ 2 codiert, 2 Öffner + 1 Schließer", "-K2, E16"),
    ("-B1b", "Sicherheitsschalter Deckel", "Typ 2 codiert, 2 Öffner", "-K2"),
    ("-S1", "Leuchttaster Öffnen", "grün, Schließer, LED 24 V (-H1)", "E1, A12"),
    ("-S2", "Leuchttaster Laden", "blau, Schließer, LED 24 V (-H2)", "E2, A13"),
    ("-S3", "Drucktaster Stopp", "rot, Öffner", "E3"),
    ("-S4", "Drucktaster Reset", "weiß, 2 Schließer", "E4, -K1"),
    ("-B2", "Näherungsschalter Z oben", "induktiv M8, PNP, Sn 2 mm", "E6"),
    ("-B3", "Näherungsschalter Stempel", "induktiv M8, PNP, Schaltfahne", "E7"),
    ("-B4", "Näherungsschalter Sternrad", "induktiv M12, PNP, Sn 4 mm", "E9"),
    ("-B6", "Reflexlichttaster Station", "M18, PNP, Hintergrundausblendung", "E10"),
    ("-B7", "Reflexlichttaster Fach", "M18, PNP, Hintergrundausblendung", "E11"),
    ("-B8", "Näherungsschalter Kronkorken", "induktiv M8 bündig, PNP, Sn 1,5 mm", "E8"),
    ("-B10", "Näherungsschalter Hebel", "induktiv M8, PNP", "E12"),
    ("-B11", "Gabellichtschranke Rutsche", "Gabelweite 30 mm, PNP", "E13"),
    ("-B12", "Einweglichtschranke Schublade", "Sender + Empfänger, PNP, hellschaltend", "E14"),
    ("-B13", "Reedkontakt Schublade", "Schließer, Magnet an der Schublade", "E15"),
    ("-A1", "Mikrocontroller", "ESP32-DevKit (WROOM-32)", "5 V von -T2"),
    ("-A2", "Optokoppler-Platine", "16 Kanäle, 24 V -> 3,3 V", "E1 … E16"),
    ("-A7", "I/O-Erweiterung", "MCP23017, I2C-Adresse 0x20", "GPIO 21/22"),
    ("-A3", "Schrittmotortreiber Z", "TMC2209, Standalone, 1/8, 1,2 A", "A1, A3"),
    ("-A4", "Schrittmotortreiber Stern", "TMC2209, Standalone, 1/8, 1,5 A", "A2, A3"),
    ("-A5", "Motortreiber Linearantrieb", "H-Brücke 24 V, 5 A", "A4, A5"),
    ("-A6", "MOSFET-Ausgangsplatine", "8 Kanäle, 24 V, Low-Side, Gate-Pull-down", "A7 … A13"),
    ("-M1", "Schrittmotor Z-Achse", "NEMA17, 1,5 A, 0,45 Nm", "-A3"),
    ("-M2", "Schrittmotor Sternrad", "NEMA17, 1,7 A, 0,59 Nm", "-A4"),
    ("-M3", "Linearantrieb", "24 V, Hub 50 mm, 200 N, Endschalter intern", "-A5"),
    ("-M4", "Servo Schwenkarm", "MG996R, 6 V, 10 kg·cm", "A6"),
    ("-Y2", "Elektro-Haftmagnet", "Ø 16 mm, 24 V, ca. 3 W, Freilaufdiode", "A7"),
    ("-E1", "LED-Leiste Bedienfach", "24 V, 120 mm, ca. 1 W", "A8"),
    ("-P1", "Signalsäule", "grün / gelb / rot, 24 V LED", "A9 … A11"),
]

EINGAENGE = [
    # Adresse, MCP-Pin, BMK, Signal, Kurzname (Stromlaufplan), Bemerkung
    ("E1", "GPA0", "-S1", "Öffnen", "Öffnen", "Schließer, Flanke = Anforderung"),
    ("E2", "GPA1", "-S2", "Laden", "Laden", "Schließer, Flanke = Anforderung"),
    ("E3", "GPA2", "-S3", "Stopp", "Stopp", "Öffner, 0 = Stopp (drahtbruchsicher)"),
    ("E4", "GPA3", "-S4", "Reset / Quittieren", "Reset", "2. Kontakt startet -K1"),
    ("E5", "GPA4", "-K1/-K2", "Sicherheitskreis OK", "Sicher OK", "Hilfsschließer in Reihe"),
    ("E6", "GPA5", "-B2", "Z-Achse oben (Referenz)", "Z oben", "1 = bedämpft"),
    ("E7", "GPA6", "-B3", "Stempelkontakt", "Stempel", "1 = Stempel berührt"),
    ("E8", "GPA7", "-B8", "Kronkorken am Stempel", "Kronkorken", "1 = Metall erkannt"),
    ("E9", "GPB0", "-B4", "Sternrad Referenz", "Stern Ref.", "1 = Tasche 1 in der Station"),
    ("E10", "GPB1", "-B6", "Flasche in der Station", "Fl. Station", "1 = Flasche erkannt"),
    ("E11", "GPB2", "-B7", "Flasche im Bedienfach", "Fl. Fach", "1 = Flasche erkannt"),
    ("E12", "GPB3", "-B10", "Hebel Grundstellung", "Hebel", "1 = Grundstellung"),
    ("E13", "GPB4", "-B11", "Kronkorken in der Rutsche", "KK Rutsche", "Impuls je Kronkorken"),
    ("E14", "GPB5", "-B12", "Schublade voll", "Schubl. voll", "1 = Strahl unterbrochen"),
    ("E15", "GPB6", "-B13", "Schublade eingesetzt", "Schubl. da", "1 = eingesetzt"),
    ("E16", "GPB7", "-B1a", "Bedienklappe geschlossen", "Klappe zu", "Meldekontakt (Schließer)"),
]

AUSGAENGE = [
    ("A1", "GPIO 16 / 17", "-A3", "Z-Achse STEP / DIR", "800 Schritte/mm"),
    ("A2", "GPIO 18 / 19", "-A4", "Sternrad STEP / DIR", "1000 Schritte je Tasche"),
    ("A3", "GPIO 23", "-A3, -A4", "Treiber Enable", "LOW = aktiv"),
    ("A4", "GPIO 25", "-A5", "Linearantrieb ausfahren", "Abhebeln"),
    ("A5", "GPIO 26", "-A5", "Linearantrieb einfahren", "Grundstellung"),
    ("A6", "GPIO 27", "-M4", "Servo PWM", "50 Hz, 0,5 … 2,5 ms"),
    ("A7", "GPIO 32", "-A6 / -Y2", "Haftmagnet", "aus +24 V Leistung"),
    ("A8", "GPIO 33", "-A6 / -E1", "Fachlicht", "aus +24 V Steuerung"),
    ("A9", "GPIO 4", "-A6 / -P1", "Signalsäule grün", ""),
    ("A10", "GPIO 5", "-A6 / -P1", "Signalsäule gelb", "Strapping-Pin"),
    ("A11", "GPIO 2", "-A6 / -P1", "Signalsäule rot", "Strapping-Pin"),
    ("A12", "GPIO 13", "-A6 / -H1", "Leuchtmelder Öffnen", "in -S1"),
    ("A13", "GPIO 14", "-A6 / -H2", "Leuchtmelder Laden", "in -S2"),
    ("I2C", "GPIO 21 / 22", "-A7", "SDA / SCL", "400 kHz, MCP23017"),
]

EIGENTEILE = {     # Nr -> (Benennung, Werkstoff / Fertigung)
    "A01": ("Deckplatte 600×560×8", "EN AW-5754, Laser/Fräsen"),
    "A02": ("Gleitplatte Ø460×6", "PE-UHMW, Wasserstrahl"),
    "A03": ("Sternradscheibe Ø327×10, 8 V-Taschen 90°", "PE-HD, Fräsen"),
    "A05": ("Kopfplatte 60×110×10", "EN AW-5754"),
    "A06": ("Mutternhalter 22×66×10", "EN AW-5754"),
    "A07": ("Schwenkarm 8 mm", "S235JR, Laser"),
    "A10": ("Aktorbügel 8 mm", "S235JR, Laser + Kanten"),
    "A11": ("Hebel 30×12, L 215", "S235JR"),
    "A12": ("Hakenleiste mit Lippe", "C45, gehärtet"),
    "A13": ("Kronkorken-Schublade 113×80×150", "PP (oder PETG, P1S)"),
    "A14": ("Tropfschale 96×106", "PP"),
    "A15": ("Tropfgitter 94×104", "PE (oder PETG, P1S)"),
    "A16": ("Geländerband 2×20", "1.4310, gebogen"),
    "A17": ("Stellarm-Sockel mit Langloch", "EN AW-6060"),
    "A18": ("Stellarm-Schieber mit Skala", "EN AW-6060"),
    "A19": ("Stempelplatte Ø28×4", "POM"),
    "A20": ("Schwenkarmträger", "S235JR, Laser + Kanten"),
    "A22": ("Trichter Ø40", "PETG, 3D-Druck P1S"),
    "A23": ("Rutsche 1,5 mm, 25° Gefälle", "1.4301, Kanten"),
    "A24": ("Trennwand Kronkorkenfach 3 mm", "EN AW-5754"),
    "A25": ("Distanzplatte 20 mm", "EN AW-6060"),
}
BMK_MUSTER = re.compile(r"_(A\d+(_A\d+)?|B\d+[ab]?|M\d|S\d|P1|K1|T1|Y2)$")


def stueckliste_daten():
    """Zählt Eigenfertigungs- und Kaufteile direkt aus dem 3D-Modell."""
    eigen = OrderedDict()
    kauf = OrderedDict()
    for t in A.TEILE:
        if t.nr:
            eigen[t.nr] = eigen.get(t.nr, 0) + 1
            continue
        if BMK_MUSTER.search(t.name) or t.name.startswith("Signalsaeule_"):
            continue                      # Elektro-Betriebsmittel: siehe Betriebsmittelliste
        n = re.sub(r"_\d+$", "", t.name)
        kauf[n] = kauf.get(n, 0) + 1
    fehlend = set(eigen) - set(EIGENTEILE)
    if fehlend:
        raise SystemExit(f"Benennung fehlt für Eigenfertigungsteile: {sorted(fehlend)}")
    zeilen_e = [(nr, str(eigen[nr]), *EIGENTEILE[nr]) for nr in sorted(eigen)]
    zeilen_k = []
    for i, (n, m) in enumerate(kauf.items(), 1):
        b = n.replace("_", " ").replace("Geraetefuss", "Gerätefuß").replace("Saeule", "Säule") \
             .replace("Fuehrung", "Führung").replace("Gelaender", "Geländer").replace("Tuer", "Tür") \
             .replace("Bruecke", "Brücke").replace("gehaeuse", "gehäuse").replace("Betaetiger", "Betätiger")
        zeilen_k.append((f"K{i:02d}", str(m), b, ""))
    zeilen_k.append((f"K{len(kauf) + 1:02d}", "1", "Schrauben, Nutensteine, Winkel, Kabelkanal (Satz)", ""))
    return zeilen_e, zeilen_k


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
    S.text(110, 248, "Flaschenöffner-Automat", 9, True, "m")
    S.text(110, 238, "TFO-A Index B: Ausgabeautomat mit Bedienfach, Magazin für 8 Flaschen,", 3.5, ausr="m")
    S.text(110, 232.5, "Kronkorken-Abfuhr in eine Schublade, ESP32-Steuerung", 3.5, ausr="m")
    A_ = Z.einpassen(S, iso, 35, 100, 185, 226)
    Z.zeichne_strecken(A_, iso, 0.22)
    tab(S, 40, 88, [("Dokument", 55), ("Angabe", 85)], [
        ("Dokumentnummer", DOKNR), ("3D-Modell", "TFO-A_Flaschenoeffner_Automatik.step"),
        ("Geometriequelle", "modell_a.py (CadQuery)"),
        ("Steuerungsprogramm", "firmware/flaschenoeffner_automatik"),
        ("Ausgabedatum", Z.DATUM), ("Dokumentenstatus", "Entwurf, nicht freigegeben"),
        ("Erstellt durch", "KI-Entwurf, Prüfung durch Fachkraft nötig"),
    ], 3.0, "Deckblatt")


def daten(pdf):
    S, y = kopf(pdf, "1  Übersicht und technische Daten")
    hs = [f[2] for f in A.M.FLASCHEN]
    ds = [f[3] for f in A.M.FLASCHEN]
    y = tab(S, 20, y, [("Merkmal", 62), ("Wert", 118)], [
        ("Bauform", "Werkbankgerät, Ausgabeautomat mit Sternrad-Magazin"),
        ("Abmessungen B × T × H", "603 × 618 × 802 mm (mit Bedienpult und Signalsäule)"),
        ("Masse", "ca. 30 kg (Abschätzung)"),
        ("Magazin", "8 Taschen, Befüllen und Entnehmen über das Bedienfach"),
        ("Flaschen", f"Kronkorken 26 mm, Höhe {min(hs):.1f} … {max(hs):.0f} mm, Ø {min(ds):.1f} … {max(ds):.0f} mm"),
        ("Formatwechsel", "Geländerring mit 3 Stellarmen und Skala (Durchmesser)"),
        ("Höhenanpassung", "automatisch durch Antasten mit dem gefederten Stempel"),
        ("Zeit je Flasche", "ca. 10 s von \"Öffnen\" bis zur Flasche im Fach (Schätzung)"),
        ("Antriebe", "2 Schrittmotoren NEMA17, Linearantrieb 24 V, Servo 6 V"),
        ("Steuerung", "ESP32 mit MCP23017, Weboberfläche, optional Alexa"),
        ("Versorgung", "230 V AC / 24 V DC, ca. 120 W"),
        ("Schutzeinrichtungen", "Haube, Klappe und Deckel verriegelt (Typ 2), Not-Halt"),
        ("Kronkorken-Abfuhr", "Haftmagnet, Schwenkarm, Trichter, Rutsche 25°, Schublade"),
        ("Füllmenge Schublade", "ca. 150 Kronkorken, Meldung \"voll\" per Lichtschranke"),
    ], 3.0, "Daten")
    y = Z.ueberschrift(S, y, "1.1 Baugruppen")
    Z.liste(S, y, [
        "Gestell: Rahmen aus Systemprofil 40×80, Deckplatte, Gleitplatte aus PE-UHMW, "
        "Tropfschale mit Gitter unter dem Bedienfach.",
        "Sternrad: zwei Scheiben mit je 8 V-Taschen (90°), Schrittmotor über Zahnriemen 5 : 1. "
        "Station (Öffnen) hinten bei 90°, Bedienfach vorn bei 270°.",
        "Geländerring: drei Federbänder an Stellarmen mit Skala halten die Flaschen in den Taschen. "
        "Vorn ist der Ring offen, dort liegt das Bedienfach.",
        "Z-Achse: Säule 40×40 mit Linearführung MGN12, Trapezspindel TR8×2 (selbsthemmend).",
        "Öffnerkopf: Hebel mit Hakenleiste wie beim Handgerät TFO, Linearantrieb über dem Hebel, "
        "gefederter Stempel mit Haftmagnet und Kronkorkensensor am schwenkbaren Arm.",
        "Kronkorken-Abfuhr: fester Trichter neben der Station, Rutsche mit Zähl-Lichtschranke, "
        "Schublade in einem abgetrennten Fach mit eigener Tür (links).",
        "Haube und Bedienung: Profil 20×20 mit Polycarbonat, Bedienklappe und Servicedeckel "
        "verriegelt, Bedienpult rechts vorn, Signalsäule.",
    ], 2.9)


def bedienung(pdf):
    S, y = kopf(pdf, "2  Bedienung")
    y = Z.absatz(S, 20, y, 180, "Die Maschine arbeitet wie ein Getränkeautomat. Der Bediener greift nur in das "
                 "Bedienfach vorn in der Mitte. Die Klappe davor überwacht ein Sicherheitsschalter. Ist sie offen, "
                 "sind alle Antriebe stromlos. Bewegungen starten nur auf Tastendruck und nur bei "
                 "geschlossener Klappe.", 2.9)
    y = Z.ueberschrift(S, y, "2.1 Bedienelemente")
    y = tab(S, 20, y, [("Element", 42), ("Funktion", 138)], [
        ("-S1 Öffnen (grün)", "nächste verschlossene Flasche öffnen und ins Fach fahren"),
        ("-S2 Laden (blau)", "nächste leere Tasche ins Fach fahren (zum Befüllen)"),
        ("-S3 Stopp (rot)", "Ablauf sofort anhalten, danach Reset"),
        ("-S4 Reset (weiß)", "Störung quittieren, Not-Halt-Relais starten, Referenzfahrt"),
        ("-S0 Not-Halt", "Antriebe sofort stromlos (Stoppkategorie 0)"),
        ("Weboberfläche", "flaschenoeffner.local: Öffnen, Laden, Stopp, Reset, Belegung"),
        ("Alexa (optional)", "\"Alexa, schalte Bier ein\" entspricht der Taste Öffnen"),
    ], 2.7, "Bedienung")
    y = tab(S, 20, y + 3, [("Anzeige", 42), ("Bedeutung", 138)], [
        ("grün Dauerlicht", "bereit, LED in S1/S2 zeigt, ob Öffnen bzw. Laden möglich ist"),
        ("grün blinkt", "geöffnete Flasche steht im Fach, Fachlicht an"),
        ("gelb", "Hinweis (Schublade voll, Magazin leer, kein Kronkorken …), Text im Web"),
        ("rot blinkt", "Störung, Ursache in der Weboberfläche, quittieren mit Reset"),
        ("rot Dauerlicht", "Klappe, Deckel offen oder Not-Halt gedrückt"),
    ], 2.7, "Bedienung")
    y = Z.ueberschrift(S, y, "2.2 Abläufe")
    y = Z.liste(S, y, [
        "Bier holen: Öffnen drücken. Nach etwa 10 s blinkt grün, das Fachlicht leuchtet. Klappe "
        "öffnen, Flasche herausnehmen, Klappe schließen. -B7 erkennt das leere Fach.",
        "Magazin befüllen: Laden drücken, die nächste leere Tasche fährt ins Fach. Klappe öffnen, "
        "Flasche einsetzen, Klappe schließen. Für jede weitere Flasche Laden erneut drücken.",
        "Kronkorken leeren: Tür links öffnen (nicht verriegelt, durch die Trennwand von allen "
        "bewegten Teilen getrennt), Schublade ziehen, leeren, einschieben. Ohne Schublade "
        "(-B13) oder bei voller Schublade (-B12) wird Öffnen gesperrt.",
        "Tropfschale: herausnehmen, spülen, Gitter einlegen. Die Schale liegt unter dem Fach.",
    ], 2.8, True)
    y = Z.ueberschrift(S, y, "2.3 Format einstellen (Geländerring)")
    y = Z.absatz(S, 20, y, 180, "Servicedeckel öffnen, die drei Klemmhebel lösen, alle Stellarme auf "
                 "denselben Skalenwert schieben, festklemmen. Die Höhe stellt die Maschine selbst ein.", 2.8)
    zeilen = []
    for fid, name, H, D, _ in A.M.FLASCHEN:
        zeilen.append((name, f"{D:.1f}", f"{H:.1f}", f"{A.gelaender_r(D):.1f}", f"{A.zp_arbeit(H):.1f}"))
    tab(S, 20, y, [("Sorte", 46), ("Ø mm", 22), ("Höhe mm", 24), ("Skala (Radius) mm", 44), ("Arbeitshöhe Z mm", 44)],
        zeilen, 2.6, "Format")


def funktion(pdf):
    S, y = kopf(pdf, "3  Funktion und Schrittkette")
    y = Z.absatz(S, 20, y, 180, "Prinzip: Das V-Profil der Sternradtaschen zentriert jede Flasche in "
                 "Umfangsrichtung. Ein anderer Durchmesser verschiebt sie nur radial, also entlang der "
                 "Hakenlippe, die deshalb bei jeder Sorte richtig liegt. Der Geländerring hält die Flasche "
                 "am Taschengrund. Die Höhe findet die Maschine selbst: Der Kopf fährt ab, bis der "
                 "gefederte Stempel den Kronkorken berührt. Ein Induktivsensor im Stempel prüft, ob "
                 "wirklich ein Kronkorken darauf sitzt. Erst dann fährt das Sternrad die letzten 3 mm, "
                 "und der Kronkorkenrand gleitet über die Lippe. Beim Abhebeln ist der Stempel der "
                 "Drehpunkt wie bei einem Handöffner und hält den Kronkorken mit dem Haftmagnet fest. "
                 "In sicherer Höhe schwenkt der Arm über den festen Trichter und lässt ihn fallen.", 2.8)
    y = Z.ueberschrift(S, y, "3.1 Schrittkette Öffnen")
    rows = [(s, n, w, t) for s, n, a, w, t, f in SCHRITTE]
    y = tab(S, 20, y, [("Schritt", 15), ("Name", 32), ("Weiterschaltbedingung", 103), ("Grenze", 30)], rows, 2.6,
            "Schrittkette")
    y = Z.ueberschrift(S, y, "3.2 Abweichungen (Aktionen je Schritt: siehe GRAFCET, Seite 5)")
    y = tab(S, 20, y, [("Schritt", 15), ("Name", 32), ("Abweichung und Reaktion", 133)],
            [(s, n, f) for s, n, a, w, t, f in SCHRITTE if f != "–"], 2.6, "Abweichungen")
    y = Z.ueberschrift(S, y, "3.3 Belegung der Taschen")
    Z.liste(S, y, [
        "Jede Tasche hat den Zustand leer, voll, offen oder unbekannt. Er wird im Flash des ESP32 "
        "gespeichert und übersteht einen Stromausfall. Nach dem ersten Einschalten ist alles unbekannt.",
        "Beim Schließen der Klappe bestimmt -B7 den Zustand der Fachtasche: keine Flasche = leer, "
        "neue Flasche = voll. \"Unbekannt\" prüft die Station beim Öffnen mit -B6.",
        "Öffnen ist gesperrt, solange eine geöffnete Flasche im Fach steht. Eine offene Flasche in "
        "einer anderen Tasche (z. B. nach Stopp) wird beim nächsten Öffnen zuerst ausgegeben.",
    ], 2.6)


def grafcet(pdf):
    S = zeichnungsblatt(pdf, "Ablaufdiagramm", "TFO-A-E00", "Ablaufplan")
    S.text(25, 280, "GRAFCET nach DIN EN 60848 (vereinfacht): Hauptkette Öffnen", 3.5, True)
    x, y, dy = 112, 268, 16.6
    schritte = [("0", "Referenz", "M1 auf bis B2, M2 bis B4, M3 ein, M4 0°"),
                ("1", "Bereit", "P1 grün, H1/H2 nach Freigabe"),
                ("2", "S1 Takten", "M2: Vorposition (3 mm vor Station)"),
                ("3", "S2 Antasten", "M1 ab: Eilgang, dann 10 mm/s"),
                ("4", "S3 Prüfen", "M1 +0,5 mm, B8 abfragen"),
                ("5", "S4 Fein", "M2 +3 mm (Rand über Lippe)"),
                ("6", "S5 Abhebeln", "Y2 ein, M3 ausfahren"),
                ("7", "S6 Hebel zurück", "M3 einfahren"),
                ("8", "S7 Kopf hoch", "M1 auf 400 mm"),
                ("9", "S8 Schwenken", "M4 auf 90° (über Trichter)"),
                ("10", "S9 Abwurf", "Y2 aus, Zähler +1"),
                ("11", "S10 Zurück", "M4 auf 0°, Tasche = offen"),
                ("12", "S11 Ausgabe", "M2 4 Taschen (180°) ins Fach"),
                ("13", "Flasche bereit", "E1 Fachlicht ein, P1 grün blinkt")]
    trans = ["B2 · B4", "Öffnen (S1/Web) · Freigaben (Fach, Schublade, Magazin)",
             "M2 steht · Flasche in Station (B6)", "Stempel berührt (B3)", "Kronkorken erkannt (B8)",
             "M2 steht", "t > 1,4 s", "Hebel Grundstellung (B10)", "M1 steht",
             "t > 0,7 s", "Kronkorken in Rutsche (B11)", "t > 0,7 s", "M2 steht · Lage plausibel (B4)",
             "Klappe geöffnet und geschlossen (B1a) · Fach leer (B7)"]
    for i, (nr, name, akt) in enumerate(schritte):
        yy = y - i * dy
        if nr == "0":
            S.rechteck(x - 6.5, yy - 6.5, x + 6.5, yy + 6.5, 0.5)
            S.rechteck(x - 5.2, yy - 5.2, x + 5.2, yy + 5.2, 0.5)
        else:
            S.rechteck(x - 6, yy - 6, x + 6, yy + 6, 0.5)
        S.text(x, yy - 1.5, nr, 4, True, "m")
        S.linie(x + 6, yy, x + 14, yy, 0.35)
        S.rechteck(x + 14, yy - 5, x + 110, yy + 5, 0.35)
        S.text(x + 16.5, yy + 0.8, name, 2.8, True)
        S.text(x + 16.5, yy - 3.4, akt, 2.4)
        if i < len(schritte) - 1:
            S.linie(x, yy - 6, x, yy - dy + 6, 0.35)
            S.linie(x - 5, yy - dy / 2, x + 5, yy - dy / 2, 0.7)
            S.text(x - 7, yy - dy / 2 - 1.0, trans[i], 2.3, ausr="r")
    # Rücksprung 13 -> 1
    yb = y - 13 * dy
    S.linie(x, yb - 6, x, yb - 12, 0.35)
    S.linie(x - 5, yb - 9, x + 5, yb - 9, 0.7)
    S.text(x - 7, yb - 10, trans[13], 2.3, ausr="r")
    xr = 22
    S.pfad([(x, yb - 12), (xr, yb - 12), (xr, y - dy + 9), (x, y - dy + 9)], 0.35)
    S.pfeil(x, y - dy + 9, 0)
    S.text(xr - 1.5, (yb + y) / 2, "nächste Flasche", 2.4, winkel=90)
    # Zweige rechts
    bx = 240
    S.text(bx, 280, "Zweig Laden (Alternative zu Schritt 2)", 3.2, True)
    kl = [("1", "Bereit", ""), ("20", "Leere Tasche ins Fach", "M2 auf kürzestem Weg (nur Uhrzeigersinn)"),
          ("21", "Warten auf Bediener", "E1 Fachlicht ein, Text \"Flasche einsetzen\"")]
    kt = ["Laden (S2) · leere Tasche · Fach frei", "M2 steht · Lage plausibel (B4)"]
    xs, ys = bx + 8, 268
    for i, (nr, name, akt) in enumerate(kl):
        yy = ys - i * 15
        S.rechteck(xs - 5.5, yy - 5.5, xs + 5.5, yy + 5.5, 0.45 if nr != "1" else 0.25)
        S.text(xs, yy - 1.4, nr, 3.4, True, "m")
        S.linie(xs + 5.5, yy, xs + 12, yy, 0.3)
        S.rechteck(xs + 12, yy - 4.5, xs + 102, yy + 4.5, 0.3)
        S.text(xs + 14, yy + 0.6, name, 2.5, True)
        if akt:
            S.text(xs + 14, yy - 3.1, akt, 2.2)
        if i < len(kl) - 1:
            S.linie(xs, yy - 5.5, xs, yy - 15 + 5.5, 0.35)
            S.linie(xs - 4.5, yy - 7.5, xs + 4.5, yy - 7.5, 0.6)
            S.text(xs + 6, yy - 9.3, kt[i], 2.2)
    S.text(xs + 6, ys - 2 * 15 - 9.3, "Klappe auf/zu: Fach erfassen (B7), zurück zu 1", 2.2)
    S.linie(xs, ys - 30 - 5.5, xs, ys - 30 - 11, 0.35)
    S.linie(xs - 4.5, ys - 30 - 7.5, xs + 4.5, ys - 30 - 7.5, 0.6)

    S.text(bx, 214, "Neben- und Fehlerzweige", 3.2, True)
    zw = (("aus 1", "offene Flasche in anderer Tasche: direkt zu 12 (Ausgabe)"),
          ("aus 1", "Öffnen gesperrt mit Hinweis: Fach belegt, Schublade fehlt"),
          ("", "oder voll, Magazin leer"),
          ("aus 2", "B6 = 0: Tasche = leer, nächste volle Tasche suchen"),
          ("aus 3", "unterste Lage ohne B3: Warnung, weiter 8, Ausgabe"),
          ("aus 4", "B8 = 0 (kein Kronkorken): nicht hebeln, weiter 8,"),
          ("", "Flasche wird mit Warnung ausgegeben"),
          ("aus 10", "kein B11 in 1,5 s: Warnung, weiter mit 11"),
          ("jeder", "K1/K2 = 0 (Klappe, Deckel, Not-Halt): Antriebe stromlos"),
          ("", "(Hardware). In Bewegung unterbrochen: Referenz ungültig,"),
          ("", "nach dem Schließen Reset -> Schritt 0"),
          ("jeder", "Stopp (S3) oder Zeitgrenze: Störung, Reset -> 1"))
    for i, (k, t) in enumerate(zw):
        S.text(bx, 206 - i * 6, k, 2.6, True)
        S.text(bx + 15, 206 - i * 6, t, 2.6)
    S.text(bx, 125, "Legende", 3.0, True)
    for i, t in enumerate(("Doppelrahmen = Anfangsschritt, Rahmen = Schritt", "Querstrich = Transition mit Bedingung",
                           "Rechteck rechts = Aktion (solange der Schritt aktiv ist)", "· = logisches UND",
                           "Grenzzeiten siehe Schrittkette (Seite 4)")):
        S.text(bx, 119 - i * 5.5, t, 2.6)


def sicherheit(pdf):
    S, y = kopf(pdf, "4  Sicherheitskonzept")
    y = Z.absatz(S, 20, y, 180, "Grundlage: Maschinenverordnung (EU) 2023/1230, EN ISO 12100 "
                 "(Risikobeurteilung), EN ISO 13849-1 (Sicherheitsfunktionen), EN ISO 14119 "
                 "(Verriegelung), EN ISO 13850 (Not-Halt), EN ISO 13857 (Sicherheitsabstände), "
                 "EN 60204-1 (elektrische Ausrüstung). Die Einschätzung ist ein Entwurf und ersetzt "
                 "keine Risikobeurteilung durch eine fachkundige Person.", 2.8)
    y = Z.ueberschrift(S, y, "4.1 Gefährdungen und Maßnahmen")
    y = tab(S, 20, y, [("Gefährdung", 40), ("Ort", 44), ("Maßnahme", 96)], [
        ("Quetschen, Scheren", "Sternrad, Geländerring", "Haube fest, Klappe und Deckel verriegelt"),
        ("Quetschen", "Kopf (Z-Achse, Hebel)", "Haube; Leistung über -K1/-K2 abgeschaltet"),
        ("Hineingreifen", "Bedienfach 130 mm breit", "Öffnung > 120 mm: Klappe verriegelt (B1a)"),
        ("Glasbruch, Splitter", "Station", "Haube aus PC 4 mm, Kräfte begrenzt"),
        ("Schneiden", "Hakenlippe", "nur bei offenem Deckel erreichbar"),
        ("Elektrischer Schlag", "Schaltkasten 230 V", "Schutzklasse I, PE, -Q1, Tür mit Werkzeug"),
        ("Unerwarteter Anlauf", "alle Antriebe", "Schließen startet nichts, Start nur per Taste"),
        ("Kronkorkenfach", "Tür links", "nicht verriegelt: Trennwand A24 trennt alles"),
    ], 2.6, "Sicherheit")
    y = Z.ueberschrift(S, y, "4.2 Sicherheitsfunktionen")
    y = tab(S, 20, y, [("SF", 12), ("Auslöser", 52), ("Reaktion", 70), ("PLr (Entwurf)", 46)], [
        ("SF1", "Bedienklappe offen (-B1a)", "-K2 schaltet 24 V Leistung ab", "PL c, Kat. 3"),
        ("SF2", "Servicedeckel offen (-B1b)", "wie SF1", "PL c, Kat. 3"),
        ("SF3", "Not-Halt (-S0)", "-K1 schaltet ab, Stoppkat. 0", "PL c, Kat. 3"),
        ("SF4", "Wiederanlauf", "Not-Halt: Reset; Klappe: Taste", "manueller Start"),
    ], 2.6, "Sicherheit")
    y = Z.ueberschrift(S, y, "4.3 Umsetzung")
    Z.liste(S, y, [
        "Not-Halt -S0 zweikanalig auf das Not-Halt-Relais -K1 (manueller, überwachter Start mit "
        "-S4). Klappe -B1a und Deckel -B1b, je 2 zwangsöffnende Öffner, in Reihe zweikanalig auf "
        "den Schutztürwächter -K2.",
        "-K2 startet automatisch beim Schließen. Das ist zulässig, weil die Steuerung danach "
        "nichts von selbst bewegt (EN 60204-1, 9.2.5): Jede Bewegung braucht Öffnen oder Laden.",
        "Freigabekontakte von -K1 und -K2 in Reihe schalten die 24-V-Leistung für Treiber, "
        "H-Brücke, Servo-Wandler und Haftmagnet. ESP32, Sensoren und Fachlicht bleiben versorgt.",
        "Selbsthemmende Spindel TR8×2: Der Kopf sinkt bei Abschaltung nicht ab. Schrittmotoren "
        "laufen ohne Strom kaum nach, deshalb entfällt eine Zuhaltung. Zu prüfen: Nachlauf kürzer "
        "als die Zeit zum Öffnen der Klappe und Hineingreifen.",
        "Station und Kopf liegen dem Fach gegenüber (Abstand ca. 300 mm, durch das Sternrad verdeckt).",
        "Validierung: PL mit SISTEMA nachrechnen, Prüfprotokoll (SF1 bis SF4, Querschluss, "
        "Drahtbruch) vor der ersten Inbetriebnahme.",
    ], 2.7)


def betriebsmittel(pdf):
    S, y = kopf(pdf, "5  Betriebsmittel")
    tab(S, 20, y, [("BMK", 14), ("Benennung", 50), ("Typ / Daten", 84), ("Anschluss", 32)],
        BETRIEBSMITTEL, 2.35, "Betriebsmittel")


def io_liste(pdf):
    S, y = kopf(pdf, "6  I/O-Liste")
    y = Z.absatz(S, 20, y, 180, "Eingänge: 24-V-Signale über die Optokoppler-Platine -A2 auf die I/O-Erweiterung "
                 "-A7 (MCP23017, I2C). Pull-ups und Invertierung im Baustein, Bit 1 = Signal aktiv. "
                 "Ausgänge direkt am ESP32.", 2.7)
    y = Z.ueberschrift(S, y, "6.1 Eingänge (MCP23017, Adresse 0x20)")
    y = tab(S, 20, y, [("Adr.", 12), ("Pin", 14), ("BMK", 18), ("Signal", 58), ("Bemerkung", 78)],
            [(a, p, b, s, bem) for a, p, b, s, _, bem in EINGAENGE], 2.4, "Eingänge")
    y = Z.ueberschrift(S, y, "6.2 Ausgänge (ESP32)")
    tab(S, 20, y, [("Adr.", 12), ("GPIO", 24), ("BMK", 22), ("Signal", 54), ("Bemerkung", 68)], AUSGAENGE, 2.4,
        "Ausgänge")


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
                S.text(xx + (1 if seite == "l" else -1), yy - 0.9, p.strip(), 1.9, ausr="l" if seite == "l" else "r")
            else:
                xx = x0 + (x1 - x0) * (i + 1) / (n + 1)
                yy = y1 if seite == "o" else y0
                S.text(xx, yy + (-3 if seite == "o" else 1.2), p.strip(), 1.9, ausr="m")
            out[p] = (xx, yy)
    return out


def kanal(S, pa, pb, x, ytop, schalter):
    """Sicherheitskanal: von Pin pa nach oben, über Öffner in Reihe bei x, zurück auf Pin pb."""
    S.pfad([pa, (pa[0], ytop), (x, ytop)], 0.3)
    yy = ytop
    for t in schalter:
        oeffner(S, x, yy, t)
        yy -= 10
    S.pfad([(x, yy), (x, pb[1] + 3), (pb[0], pb[1] + 3), pb], 0.3)


def stromlauf_1(pdf):
    S = zeichnungsblatt(pdf, "Einspeisung, Sicherheitskreis", "TFO-A-E01", "Stromlaufplan", "1/3")
    S.text(30, 278, "Einspeisung 230 V, Netzteile, Sicherheitskreis (Not-Halt -K1, Schutztüren -K2)", 3.5, True)
    for t, y in (("L", 255), ("N", 249), ("PE", 243)):
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
    y24, y0v, y24l = 225, 106, 205
    S.linie(t1["+24V"][0], t1["+24V"][1], 140, t1["+24V"][1], 0.35)
    S.linie(140, t1["+24V"][1], 140, y24, 0.35)
    S.rechteck(138.5, 228, 141.5, 236, 0.35)
    S.text(143, 231, "-F2 T1A", 2.2)
    S.linie(35, y24, 405, y24, 0.5)
    S.text(405, y24 + 1.5, "+24V Steuerung (L+)", 2.4, ausr="r")
    S.linie(t1["0V"][0], t1["0V"][1], 132, t1["0V"][1], 0.35)
    S.linie(132, t1["0V"][1], 132, y0v, 0.35)
    S.linie(37, y0v, 405, y0v, 0.5)
    S.text(405, y0v - 3.5, "0V (M)", 2.4, ausr="r")
    # -K1 Not-Halt-Relais, -K2 Schutztürwächter
    oben = ("A1", "S11", "S12", "S21", "S22", "S33", "S34")
    unten = ("A2", "13", "14", "23", "24", "43", "44")
    k1 = geraet(S, 175, 140, 225, 190, "-K1", "Not-Halt-Relais\nman. Start", pins_o=oben, pins_u=unten)
    k2 = geraet(S, 280, 140, 330, 190, "-K2", "Schutztürwächter\nAutostart", pins_o=oben, pins_u=unten)
    for k in (k1, k2):
        S.linie(k["A1"][0], y24, k["A1"][0], k["A1"][1], 0.3)
        S.linie(k["A2"][0], k["A2"][1], k["A2"][0], y0v, 0.3)
    kanal(S, k1["S11"], k1["S12"], 155, 217, ["-S0"])
    kanal(S, k1["S21"], k1["S22"], 165, 217, [""])
    S.text(150, 219.5, "Not-Halt 2-kanalig", 2.2)
    kanal(S, k2["S11"], k2["S12"], 255, 219, ["-B1a", "-B1b"])
    kanal(S, k2["S21"], k2["S22"], 266, 219, ["", ""])
    S.text(240, 221.5, "Klappe + Deckel 2-kanalig", 2.2)
    # Start -K1 über -S4, -K2 gebrückt (Autostart)
    a, b = k1["S33"], k1["S34"]
    S.pfad([a, (a[0], 200), (238, 200), (238, 207)], 0.3)
    schliesser(S, 238, 217, "-S4 Reset")
    S.pfad([(238, 217), (238, 219), (232, 219), (232, 196), (b[0], 196), b], 0.3)
    a, b = k2["S33"], k2["S34"]
    S.pfad([a, (a[0], 194), (b[0], 194), b], 0.3)
    S.text((a[0] + b[0]) / 2, 195.5, "Brücke", 1.6, ausr="m")
    # Freigabepfade in Reihe: +24V -> K1 13-14 -> 23-24 -> K2 13-14 -> 23-24 -> F3 -> +24V Leistung
    S.pfad([(148, y24), (148, 128), (k1["13"][0], 128), k1["13"]], 0.3)
    for k in (k1, k2):
        S.pfad([k["14"], (k["14"][0], 134), (k["23"][0], 134), k["23"]], 0.3)
        S.text((k["14"][0] + k["23"][0]) / 2, 135.2, "Brücke", 1.6, ausr="m")
    S.pfad([k1["24"], (k1["24"][0], 124), (k2["13"][0], 124), k2["13"]], 0.3)
    S.pfad([k2["24"], (k2["24"][0], 124), (345, 124), (345, y24l)], 0.3)
    S.rechteck(343.5, 150, 346.5, 158, 0.35)
    S.text(348, 153, "-F3 T4A", 2.2)
    S.linie(345, y24l, 405, y24l, 0.5)
    S.text(405, y24l + 1.5, "+24V Leistung (geschaltet)", 2.4, ausr="r")
    # Meldekontakte 43-44 in Reihe -> E5
    S.pfad([k1["43"], (k1["43"][0], 118), (152, 118), (152, y24)], 0.3)
    S.pfad([k1["44"], (k1["44"][0], 114), (k2["43"][0], 114), k2["43"]], 0.3)
    S.pfad([k2["44"], (k2["44"][0], 118), (300, 118)], 0.3)
    S.text(301, 117.3, "-> E5 Sicherheit OK (Blatt 3)", 2.0)
    # DC/DC-Wandler
    t2 = geraet(S, 45, 150, 80, 175, "-T2", "DC/DC\n24 -> 5 V", ("+24V", "0V"), ("+5V", "GND"))
    S.pfad([t2["+24V"], (35, t2["+24V"][1]), (35, y24)], 0.3)
    S.pfad([t2["0V"], (37, t2["0V"][1]), (37, y0v)], 0.3)
    S.text(t2["+5V"][0] + 2, t2["+5V"][1] + 1, "-> -A1, -A2, -A7", 2.0)
    t3 = geraet(S, 365, 150, 400, 175, "-T3", "DC/DC\n24 -> 6 V", ("+24V", "0V"), ())
    S.pfad([t3["+24V"], (358, t3["+24V"][1]), (358, y24l)], 0.3)
    S.pfad([t3["0V"], (361, t3["0V"][1]), (361, y0v)], 0.3)
    S.text(382, 146, "+6V -> Servo -M4", 2.0, ausr="m")
    S.text(30, 96, "Leitungsquerschnitte: 230 V 1,5 mm², 24 V Leistung 0,75 mm², Signale 0,25 mm². "
                   "PE an Deckplatte, Rahmen und Schaltkasten.", 2.4)
    S.text(30, 91, "Kanäle 1 und 2 getrennt verlegen. -B1a/-B1b: Typ 2 codiert, Betätiger gegen "
                   "Umgehen sichern (EN ISO 14119).", 2.4)


def stromlauf_2(pdf):
    S = zeichnungsblatt(pdf, "Antriebe", "TFO-A-E02", "Stromlaufplan", "2/3")
    S.text(30, 278, "Antriebe: Schrittmotoren, Linearantrieb, Servo", 3.5, True)
    yl, y0v = 255, 110
    S.linie(30, yl, 400, yl, 0.5)
    S.text(30, yl + 1.5, "+24V Leistung (von -K1/-K2, Blatt 1)", 2.4)
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
        S.text(x - 9, d["STEP"][1] + 2.5, step + ", EN GPIO23", 1.9, ausr="r")
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
    for p, g in (("IN A", "GPIO25 ausfahren"), ("IN B", "GPIO26 einfahren")):
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
    S.text(s["PWM"][0] - 7, s["PWM"][1] + 1.5, "GPIO27", 1.9, ausr="r")
    S.text(s["+6V"][0] - 7, s["+6V"][1] + 1.5, "-T3", 1.9, ausr="r")
    S.linie(s["GND"][0], s["GND"][1], s["GND"][0] - 3, s["GND"][1], 0.3)
    S.linie(s["GND"][0] - 3, s["GND"][1], s["GND"][0] - 3, y0v, 0.3)
    S.text(30, 95, "Strom TMC2209 über Vref einstellen: Z 1,2 A, Sternrad 1,5 A (Standalone, MS1/MS2 = 1/8 Schritt).", 2.4)
    S.text(30, 90, "Motorleitungen geschirmt, Schirm einseitig an PE. Linearantrieb: ausfahren = Hebel drücken (Abhebeln).", 2.4)


def stromlauf_3(pdf):
    S = zeichnungsblatt(pdf, "Steuerung, Sensoren", "TFO-A-E03", "Stromlaufplan", "3/3")
    S.text(25, 280, "ESP32, Eingänge über Optokoppler und MCP23017, Ausgänge über MOSFET-Platine", 3.5, True)
    y24, y0v = 262, 95
    S.linie(25, y24, 408, y24, 0.5)
    S.text(25, y24 + 1.5, "+24V Steuerung (Blatt 1)", 2.4)
    S.linie(25, y0v, 408, y0v, 0.5)
    S.text(25, y0v - 3.5, "0V", 2.4)
    opto = geraet(S, 25, 150, 205, 178, "-A2", "Optokoppler-Platine 16-fach (24 V -> 3,3 V)",
                  pins_o=tuple(e for e, *_ in EINGAENGE), pins_u=("0V",))
    S.linie(opto["0V"][0], opto["0V"][1], opto["0V"][0], y0v, 0.3)
    for i, (e, pin, b, s, kurz, _) in enumerate(EINGAENGE):
        x, y = opto[e]
        yt = 222
        S.linie(x, y, x, yt, 0.3)
        if b in ("-S1", "-S2", "-S4", "-K1/-K2", "-B13", "-B1a"):
            schliesser(S, x, yt + 10)
        elif b == "-S3":
            oeffner(S, x, yt + 10)
        else:                                  # Sensor PNP
            S.rechteck(x - 2.8, yt, x + 2.8, yt + 10, 0.4)
            S.linie(x - 2.8, yt + 10, x + 2.8, yt, 0.25)
        S.linie(x, yt + 10, x, y24, 0.3)
        S.text(x, yt + 13 + (3.2 if i % 2 else 0), b, 1.9, ausr="m")
        S.text(x - 1.0, 184, kurz, 1.8, winkel=90)
    S.text(25, 254, "Sensoren PNP 3-Leiter: BN +24 V, BU 0 V, BK Signal", 2.2)
    mcp = geraet(S, 220, 150, 252, 178, "-A7", "MCP23017\n0x20", pins_l=("GPA", "GPB"), pins_r=("SDA", "SCL"),
                 pins_u=("3V3", "GND"))
    S.pfad([(205, 168), mcp["GPA"]], 0.6)
    S.pfad([(205, 160), mcp["GPB"]], 0.6)
    S.text(207, 170, "GPA0-7", 1.8)
    S.text(207, 162, "GPB0-7", 1.8)
    S.text(206, 147, "Kontakte A2 -> A7", 1.7)
    rechts = ("16", "17", "18", "19", "23", "25", "26", "27", "32", "33", "4", "5", "2", "13", "14")
    esp = geraet(S, 272, 105, 305, 245, "-A1", "ESP32\nDevKit", pins_l=("21", "22"), pins_r=rechts,
                 pins_u=("5V", "GND"))
    S.pfad([mcp["SDA"], (262, mcp["SDA"][1]), (262, esp["21"][1]), esp["21"]], 0.3)
    S.pfad([mcp["SCL"], (266, mcp["SCL"][1]), (266, esp["22"][1]), esp["22"]], 0.3)
    S.text(esp["5V"][0], esp["5V"][1] - 5, "von -T2", 2.0, ausr="m")
    zuord = {"16": "-A3 STEP", "17": "-A3 DIR", "18": "-A4 STEP", "19": "-A4 DIR", "23": "-A3/-A4 EN",
             "25": "-A5 IN A", "26": "-A5 IN B", "27": "-M4 PWM"}
    for p, t in zuord.items():
        x, y = esp[p]
        S.linie(x, y, x + 12, y, 0.3)
        S.text(x + 13, y - 0.8, t + " (Blatt 2)", 1.9)
    aus = ("32", "33", "4", "5", "2", "13", "14")
    last = (("-Y2 Magnet", True), ("-E1 Fachlicht", False), ("-P1 grün", False), ("-P1 gelb", False),
            ("-P1 rot", False), ("-H1 LED Öffnen", False), ("-H2 LED Laden", False))
    mos = geraet(S, 340, 100, 362, 170, "-A6", "MOSFET\n8-fach", pins_l=tuple(f"IN{i}" for i in range(1, 8)),
                 pins_r=tuple(f"Q{i}" for i in range(1, 8)), pins_u=("GND",))
    S.linie(mos["GND"][0], mos["GND"][1], mos["GND"][0], y0v, 0.3)
    for i, p in enumerate(aus):
        xin, yin = mos[f"IN{i + 1}"]
        xm = 318 + i * 2.5
        S.pfad([esp[p], (xm, esp[p][1]), (xm, yin), (xin, yin)], 0.3)
        xq, yq = mos[f"Q{i + 1}"]
        name, magnet = last[i]
        S.linie(xq, yq, 380, yq, 0.3)
        if magnet:
            S.rechteck(380, yq - 2, 388, yq + 2, 0.4)
            S.linie(388, yq, 392, yq, 0.3)
            S.text(393, yq - 0.8, "+24V L", 1.8)
        else:
            S.kreis(383, yq, 2.4, 0.35)
            S.linie(381.3, yq - 1.7, 384.7, yq + 1.7, 0.25)
            S.linie(381.3, yq + 1.7, 384.7, yq - 1.7, 0.25)
            S.linie(385.4, yq, 404, yq, 0.3)
        S.text(370, yq + 1.2, name, 1.7, ausr="m")
    ys = [mos[f"Q{i}"][1] for i in range(2, 8)]
    S.linie(404, min(ys), 404, y24, 0.3)
    S.text(366, 92 + 81, "Last zwischen +24 V und Q (Low-Side)", 1.8, ausr="m")
    S.text(25, 132, "Hinweise: MCP23017 mit 3,3 V vom ESP32, Pull-ups 4,7 kOhm an SDA/SCL. Adresspins A0-A2 an GND.", 2.3)
    S.text(25, 127, "Strapping-Pins GPIO 2 und 5: Gate-Pull-down auf -A6, Leuchten können beim Booten kurz aufblitzen.", 2.3)
    S.text(25, 122, "-Y2 mit Freilaufdiode, aus +24 V Leistung: bei offener Klappe ist der Magnet stromlos.", 2.3)


def ansichten(pdf, T):
    S = zeichnungsblatt(pdf, "Zusammenbau", "TFO-A-000", "Zeichnung", "1/2", "1:10")
    m = 0.1
    AV = Z.Ansicht(S, 85, 172, m)
    AD = Z.Ansicht(S, 85, 112, m)
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
        "Bedienfach vorn Mitte, Kronkorkenfach links vorn, Bedienpult rechts vorn, Station hinten.",
        "Alle Maße in mm. Dargestellt: Kopf in Arbeitshöhe NRW 0,5 l, Klappe und Deckel geschlossen.",
    ], 2.5, "Hinweise")


def stueckliste(pdf):
    S = zeichnungsblatt(pdf, "Stückliste", "TFO-A-000", "Stückliste", "2/2")
    eigen, kauf = stueckliste_daten()
    sp = [("Pos.", 13), ("Menge", 12), ("Benennung", 110), ("Werkstoff / Hinweis", 55)]
    zh = 3.55
    spalten_x = (20, 215)
    zustand = {"s": 0, "y": 287}

    def zeile(w, fett=False, grau=None):
        if zustand["y"] - zh < 62 and zustand["s"] == 0:
            zustand["s"], zustand["y"] = 1, 287
        if zustand["y"] - zh < 62:
            WARNUNGEN.append("Stückliste: zu viele Zeilen")
            return
        x0, y = spalten_x[zustand["s"]], zustand["y"]
        if grau is not None:
            S.rechteck(x0, y - zh, x0 + 190, y, 0, fuellen=grau)
        x = x0
        for (k, b), t in zip(sp, w):
            if Z.tb(str(t), 2.2, fett) > b - 2:
                WARNUNGEN.append(f"Stückliste: '{t}' zu lang")
            S.text(x + 1.2, y - zh + 1.1, str(t), 2.2, fett)
            x += b
        S.linie(x0, y - zh, x0 + 190, y - zh, 0.15)
        zustand["y"] = y - zh

    zeile([k for k, _ in sp], True, 0.88)
    zeile(["", "", "Eigenfertigung (Zeichnungsnummer = Pos.)", ""], True, 0.95)
    for e in eigen:
        zeile(list(e))
    zeile(["", "", "Mechanik-Kaufteile und Normteile", ""], True, 0.95)
    for k in kauf:
        zeile(list(k))
    zeile(["", "", "Elektro: siehe Betriebsmittelliste (Seite 7)", ""], True, 0.95)
    print(f"  Stückliste: {len(eigen)} Eigenfertigungs-, {len(kauf)} Kaufteilpositionen")


def inbetriebnahme(pdf):
    S, y = kopf(pdf, "7  Inbetriebnahme und Programmierung")
    y = Z.ueberschrift(S, y, "7.1 Programm aufspielen")
    y = Z.liste(S, y, [
        "Arduino IDE 2, Boardverwalter \"esp32\" von Espressif (Core ab 3.0), Bibliothek "
        "\"FastAccelStepper\" (gin66). Für Alexa zusätzlich \"SinricPro\" und ALEXA_AKTIV = 1.",
        "zugang_beispiel.h nach zugang.h kopieren und WLAN-Daten eintragen. zugang.h wird nicht "
        "ins Repository übertragen.",
        "Board \"ESP32 Dev Module\" wählen, hochladen, serielle Ausgabe mit 115200 Baud prüfen. "
        "Weboberfläche: http://flaschenoeffner.local",
    ], 2.7, True)
    y = Z.ueberschrift(S, y, "7.2 Erstinbetriebnahme (Deckel offen, Leistung aus)")
    y = Z.liste(S, y, [
        "Verdrahtung nach Stromlaufplan prüfen, Isolationsmessung 230-V-Kreis, PE-Durchgang.",
        "Eingänge E1 … E16 einzeln betätigen und in der seriellen Ausgabe kontrollieren. Antwortet "
        "der MCP23017 nicht, I2C-Adresse und Pull-ups prüfen.",
        "SF1 bis SF4 prüfen: Klappe, Deckel, Not-Halt. -K1/-K2 müssen abfallen. Querschluss simulieren.",
        "Treiberströme über Vref einstellen. Drehrichtung: Z positiv = aufwärts, Sternrad "
        "negativ = im Uhrzeigersinn von oben.",
        "Referenzfahne so ausrichten, dass Tasche 1 bei Referenz genau in der Station steht. In "
        "jeder Taktlage darf -B4 nur bei Tasche 1 melden (Plausibilitätsprüfung).",
        "Z_REFERENZ_MM an der Drehachse messen. Hakenleiste in den Langlöchern einstellen: Lippe "
        "ca. 1 mm unter dem Kronkorkenrand, ohne das Glas zu berühren.",
        "-B6 und -B7 mit Hintergrundausblendung so einstellen, dass eine leere Tasche nicht schaltet. "
        "-B8 muss den Kronkorken durch die Stempelplatte (4 mm POM) erkennen.",
        "Servowinkel so einstellen, dass der Stempel bei 90° mittig über dem Trichter steht. "
        "Abwurf mit -B11 prüfen. Lichtschranke -B12 auf die gewünschte Füllhöhe setzen.",
        "Geländerring auf die Sorte einstellen (Tabelle Seite 3). Probelauf mit der kleinsten "
        "und der größten Sorte: Laden, Öffnen, Entnahme. T_HEBELN bei Bedarf anpassen.",
    ], 2.6, True)
    y = Z.ueberschrift(S, y, "7.3 Offene Punkte (Prototyp)")
    Z.liste(S, y, [
        "Abhebekraft und Hebelweg am Muster messen, ggf. stärkeren Linearantrieb wählen.",
        "Haftmagnet: Restmagnetismus kann den Kronkorken halten. Die POM-Platte hält Luftspalt, "
        "sonst Magnet mit Gegenimpuls oder Abstreifkante am Trichter vorsehen.",
        "Firmware ist ungetestet (ohne Hardware geschrieben, nicht kompiliert).",
        "Risikobeurteilung und PL-Nachweis (SISTEMA) durch eine Fachkraft.",
    ], 2.6)


def main():
    A.aufbauen()
    print("Lese STEP-Baugruppe und berechne Ansichten …")
    T = step_dreiecke()
    iso = Z.kanten_sichtbar(T, T, "iso", res=0.7, eps=1.2)
    pdf = Z.PDF()
    deckblatt(pdf, iso)
    daten(pdf)
    bedienung(pdf)
    funktion(pdf)
    grafcet(pdf)
    sicherheit(pdf)
    betriebsmittel(pdf)
    io_liste(pdf)
    stromlauf_1(pdf)
    stromlauf_2(pdf)
    stromlauf_3(pdf)
    ansichten(pdf, T)
    stueckliste(pdf)
    inbetriebnahme(pdf)
    pdf.speichern(AUSGABE)
    print(f"{AUSGABE.name}: {len(pdf.seiten)} Seiten")
    for w in WARNUNGEN:
        print("  WARNUNG", w)
    pruef = os.environ.get("TFO_SVG")
    if pruef:
        Path(pruef).mkdir(parents=True, exist_ok=True)
        for i, s in enumerate(pdf.seiten, 1):
            (Path(pruef) / f"a_seite_{i:02d}.svg").write_text(s.als_svg(), encoding="utf-8")


if __name__ == "__main__":
    main()
