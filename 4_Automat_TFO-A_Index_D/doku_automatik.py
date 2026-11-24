"""
Technische Dokumentation des Flaschenöffner-Automaten TFO-A, Index D (PDF).

Inhalt: Deckblatt, technische Daten, Bedienung, Funktion und Schrittkette, GRAFCET,
Sicherheitskonzept (TwinSAFE), Betriebsmittel, EtherCAT-I/O-Liste, Stromlaufplan
(3 Blätter), Zusammenbau aus der STEP-Baugruppe, Stückliste, Inbetriebnahme.

Nutzt die PDF-Funktionen aus ../gemeinsam/zeichnungen.py.   Aufruf:  python doku_automatik.py
"""
import math
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

import numpy as np

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent / "gemeinsam"))
sys.path.insert(0, str(HIER))
import zeichnungen as Z  # noqa: E402
import modell_d as A     # noqa: E402

AUSGABE = HIER / "Technische_Dokumentation_TFO-A.pdf"
STEP = HIER / "TFO-A_Flaschenoeffner_Automatik.step"
TITEL = "Flaschenöffner-Automat TFO-A"
DOKNR = "TFO-A-D01 Index D"
SEITE = [0]
WARNUNGEN = []
Z.DATUM = "2026-11-24"


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
    x0 = 420 - 10 - 180
    S.rechteck(x0 + 35.2, 10.2, x0 + 69.8, 17.6, 0, fuellen=1.0)
    S.text(x0 + 36.2, 11.6, art, 2.2)
    return S


def tab(S, x, y, spalten, zeilen, h=2.8, seite=""):
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
    ("S0", "Grundstellung", "Achsen ein, Kopf oben, Rotor 0°, Rollen zurück, Mover-Positionen lesen",
     "alle Achsen bereit, TwinSAFE OK", "20 s", "Achsfehler -> Störung"),
    ("S1", "Messen", "Mover hält 0,3 s unter Laser -B3 und Kamera -B4",
     "Höhe 171 … 352 mm, -B4 = Kronkorken", "1 s", "kein Kronkorken: ohne Öffnen zur Ausgabe"),
    ("S2", "Einstellen", "Z auf Kronkorken-Oberkante, Rotorschlitz 0° (Einfahrt)",
     "Z und Rotor in Position", "2 s", "Höhe unplausibel -> Störung"),
    ("S3", "Einfahren", "Mover fährt in den Kopf, letzte 60 mm mit 50 mm/s",
     "Mover in Position (± 0,1 mm)", "2 s", "Schleppfehler -> Störung"),
    ("S4", "Entbördeln", "Rotor 2 Umdr. (2 U/s), Zustellung über Kurvenscheibe 0 -> 100 % -> 0",
     "Kurvenscheibe fertig", "1,5 s", "Momentgrenze M2/M3 -> Störung"),
    ("S5", "Entlüften", "0,3 s warten: CO2 entweicht über den Spalt am Überband",
     "t > T_ENTLUEFTEN", "0,3 s", "–"),
    ("S6", "Abheben", "Z + 8 mm, Kronkorken hängt am Überband",
     "-B8 = 1 (Kronkorken am Band)", "0,5 s", "-B8 = 0: Warnung, Station prüfen"),
    ("S7", "Ausfahren", "Rotorschlitz 180°, Mover fährt zur Ausgabe, Überband ein",
     "Mover außerhalb Kopf (> 70 mm)", "2 s", "–"),
    ("S8", "Abfuhr", "Überband und Steigband laufen, Kronkorken fällt in den Turm",
     "Flanke -B11", "4 s", "kein -B11: Warnung, Zähler nicht erhöht"),
    ("S9", "Ausgabe", "Mover an der Ausgabe, Fachlicht ein, Klemme durch Kurvenschiene offen",
     "-B6 = 0 (Flasche entnommen)", "–", "Flasche bleibt stehen: Mover wartet"),
]

BETRIEBSMITTEL = [
    ("-Q1", "Hauptschalter", "3-polig, 16 A, abschließbar", "230 V AC"),
    ("-F1", "Leitungsschutz", "C 10 A", "230 V AC"),
    ("-T1", "Netzteil Steuerung", "24 V DC, 20 A, DC-OK-Kontakt", "230 V -> 24 V"),
    ("-T2", "Netzteil Leistung", "48 V DC, 20 A, DC-OK-Kontakt", "230 V -> 48 V"),
    ("-F2", "Sicherungsautomat 24 V", "B 6 A (Steuerung, I/O)", "+24 V"),
    ("-F3", "Sicherungsautomat 48 V", "B 16 A (Magnetbahn, Servos)", "+48 V"),
    ("-A1", "Embedded-PC", "TwinCAT 3, EtherCAT-Master, 2 × Ethernet", "24 V"),
    ("-A2", "EtherCAT-Koppler + Klemmen", "EK1100, EL1809, EL2809, EL3052, EL7332", "E-Bus"),
    ("-A4", "Sicherheitssteuerung", "EL6910 TwinSAFE Logic, 2 × EL1904, EL2904", "FSoE"),
    ("-A3", "Servoklemmen", "3 × EL7221-9014 (48 V, STO)", "-M1, -M2, -M3"),
    ("-A10", "Magnetbahn", "Motormodule 1428 mm, 6 Mover, Einspeisung 48 V", "EtherCAT"),
    ("-M1", "Servomotor Z-Achse", "48 V, 0,6 Nm, Multiturn-Absolutgeber", "-A3.1"),
    ("-M2", "Servomotor Rotor", "48 V, 0,3 Nm, Absolutgeber", "-A3.2"),
    ("-M3", "Servomotor Zustellring", "48 V, 0,3 Nm, Absolutgeber", "-A3.3"),
    ("-M4", "Getriebemotor Überband", "24 V DC, 15 W", "EL7332 K1"),
    ("-M5", "Getriebemotor Steigband", "24 V DC, 25 W", "EL7332 K2"),
    ("-S0", "Not-Halt", "Pilztaster, 2 Öffner, EN ISO 13850", "EL1904.1"),
    ("-B1a", "Sicherheitsschalter Ausgabe", "RFID codiert, 2 OSSD", "EL1904.1"),
    ("-B1b", "Sicherheitsschalter Laden", "RFID codiert, 2 OSSD", "EL1904.2"),
    ("-B1c", "Sicherheitsschalter Deckel", "RFID codiert, 2 OSSD", "EL1904.2"),
    ("-S1", "Leuchttaster Öffnen", "grün, Schließer, LED 24 V", "E1, A6"),
    ("-S3", "Drucktaster Stopp", "rot, Öffner", "E2"),
    ("-S4", "Leuchtdrucktaster Quittieren", "blau, Schließer (Reset Sicherheit)", "EL1904"),
    ("-B3", "Laser-Abstandssensor", "Triangulation, 50 … 500 mm, 4 … 20 mA", "EL3052.1"),
    ("-B4", "Smart-Kamera", "Verschluss-Erkennung, 2 Schaltausgänge", "E4, E5"),
    ("-B6", "Reflextaster Ausgabe", "M18, PNP, Hintergrundausblendung", "E6"),
    ("-B7", "Reflextaster Laden", "M18, PNP, Hintergrundausblendung", "E7"),
    ("-B8", "Näherungsschalter Überband", "induktiv M12, PNP", "E8"),
    ("-B11", "Gabellichtschranke Rutsche", "PNP, Impuls je Kronkorken", "E9"),
    ("-B12", "Einweglichtschranke Turm voll", "PNP", "E10"),
    ("-B13", "Reedkontakt Turm", "Schließer", "E11"),
    ("-A20", "Bedienpanel", "7-Zoll-Touch, Ethernet", "-A1"),
    ("-P1", "Signalsäule", "grün / gelb / rot, 24 V LED", "A3 … A5"),
    ("-E1", "Fachlicht Ausgabe / Laden", "2 × LED-Leiste 24 V", "A1, A2"),
]

EINGAENGE = [
    ("E1", "EL1809.1", "-S1", "Öffnen", "Schließer, Flanke"),
    ("E2", "EL1809.2", "-S3", "Stopp", "Öffner, 0 = Stopp"),
    ("E3", "EL1809.3", "-B1a…c", "Klappen/Deckel geschlossen", "Meldeausgang"),
    ("E4", "EL1809.4", "-B4", "Kamera: Kronkorken erkannt", "1 = Kronkorken"),
    ("E5", "EL1809.5", "-B4", "Kamera: anderer Verschluss", "Bügel, Schraub"),
    ("E6", "EL1809.6", "-B6", "Flasche an der Ausgabe", "1 = Flasche"),
    ("E7", "EL1809.7", "-B7", "Flasche an der Ladestelle", "1 = Flasche"),
    ("E8", "EL1809.8", "-B8", "Kronkorken am Überband", "1 = Metall"),
    ("E9", "EL1809.9", "-B11", "Kronkorken in der Rutsche", "Impuls"),
    ("E10", "EL1809.10", "-B12", "Turm voll", "1 = Strahl unterbrochen"),
    ("E11", "EL1809.11", "-B13", "Turm eingesetzt", "1 = eingesetzt"),
    ("E12", "EL1809.12", "-T1/-T2", "Netzteile DC OK", "in Reihe"),
    ("AI1", "EL3052.1", "-B3", "Höhe Kronkorken", "4 … 20 mA = 50 … 500 mm"),
]

AUSGAENGE = [
    ("A1", "EL2809.1", "-E1", "Fachlicht Ausgabe", ""),
    ("A2", "EL2809.2", "-E1", "Fachlicht Laden", ""),
    ("A3", "EL2809.3", "-P1", "Signalsäule grün", ""),
    ("A4", "EL2809.4", "-P1", "Signalsäule gelb", ""),
    ("A5", "EL2809.5", "-P1", "Signalsäule rot", ""),
    ("A6", "EL2809.6", "-S1", "LED Öffnen", ""),
    ("A7", "EL2809.7", "-B4", "Kamera Auslösen", "Trigger"),
    ("A8", "EL2809.8", "-S4", "LED Quittieren", "blinkt = Reset nötig"),
    ("M4", "EL7332.1", "-M4", "Überband", "24 V, Drehzahl per PWM"),
    ("M5", "EL7332.2", "-M5", "Steigband", "24 V, Drehzahl per PWM"),
]

EIGENTEILE = {
    "A01": ("Deckplatte 1040×700×8", "EN AW-5754, Laser"),
    "A14": ("Tropfwanne 180×140", "1.4301, Kanten"),
    "A20": ("Kurvenschiene Klemme öffnen", "C45, gehärtet"),
    "A21": ("Halterplatte 110×115×8", "EN AW-6082, Fräsen"),
    "A22": ("Halterstütze", "EN AW-6082"),
    "A23": ("Klemmbacke 90°-V", "POM, Fräsen (oder PETG, P1S)"),
    "A40": ("Statorsegment 100°", "EN AW-7075, eloxiert"),
    "A41": ("Orbitalrotor mit Schlitz 54°", "42CrMo4, vergütet, Zahnkranz m 0,8"),
    "A42": ("Zustellring mit Kurvennuten", "42CrMo4, vergütet, Zahnkranz m 0,8"),
    "A43": ("Entbördelhebel", "1.2379, gehärtet 60 HRC"),
    "A44": ("Kopfträger 200×215×10", "EN AW-6082"),
    "A45": ("Schlittenplatte", "EN AW-6082"),
    "A46": ("Bandrahmen Überband", "EN AW-6082"),
    "A47": ("Steigbandrahmen", "EN AW-6082"),
    "A48": ("Abwurfrutsche 21°", "1.4301, Kanten"),
    "A49": ("Sammelturm Ø 86 × 590", "PC, klar, abnehmbar"),
    "A50": ("Einfülltrichter Turm", "PETG, 3D-Druck P1S"),
}
BMK_MUSTER = re.compile(r"_(A\d+(_A\d+)?|B\d+[a-c]?|M\d|S\d|P1|K\d|T\d|Y\d)$")


def stueckliste_daten():
    """Zählt Eigenfertigungs- und Kaufteile aus dem 3D-Modell (Mover-Teile × 6)."""
    eigen, kauf = OrderedDict(), OrderedDict()
    for t in A.TEILE:
        n_ = A.N_MOVER if t.gruppe == "11_Mover" else 1
        if t.nr:
            eigen[t.nr] = eigen.get(t.nr, 0) + n_
            continue
        if BMK_MUSTER.search(t.name) or t.name.startswith("Signalsaeule_"):
            continue
        n = re.sub(r"_\d+$", "", t.name)
        kauf[n] = kauf.get(n, 0) + n_
    fehlend = set(eigen) - set(EIGENTEILE)
    if fehlend:
        raise SystemExit(f"Benennung fehlt für Eigenfertigungsteile: {sorted(fehlend)}")
    zeilen_e = [(nr, str(eigen[nr]), *EIGENTEILE[nr]) for nr in sorted(eigen)]
    zeilen_k = []
    for i, (n, m) in enumerate(kauf.items(), 1):
        b = n.replace("_", " ").replace("Geraetefuss", "Gerätefuß").replace("Saeule", "Säule") \
             .replace("Fuehrung", "Führung").replace("Ueberband", "Überband").replace("Stuetze", "Stütze") \
             .replace("Tuer", "Tür").replace("gehaeuse", "gehäuse").replace("Betaetiger", "Betätiger") \
             .replace("Entboerdel", "Entbördel").replace("Messsaeule", "Messsäule")
        zeilen_k.append((f"K{i:02d}", str(m), b, ""))
    zeilen_k.append((f"K{len(kauf) + 1:02d}", "1", "Schrauben, Nutensteine, Winkel, Kabelkanal (Satz)", ""))
    return zeilen_e, zeilen_k


def masse():
    xs, ys, zs = [], [], []
    for t in A.TEILE:
        if t.klasse in A.MOVER_KLASSEN:
            continue
        bb = t.form.BoundingBox()
        xs += [bb.xmin, bb.xmax]
        ys += [bb.ymin, bb.ymax]
        zs += [bb.zmin, bb.zmax]
    return (max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)), (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


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
        v, f = s.tessellate(0.5, 0.5)
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
    S.text(110, 238, "TFO-A Index D: Magnetbahn mit 6 Movern, Orbital-Entbördler,", 3.5, ausr="m")
    S.text(110, 232.5, "Magnet-Kronkorkenabfuhr in einen Sammelturm, TwinCAT-Steuerung", 3.5, ausr="m")
    A_ = Z.einpassen(S, iso, 35, 100, 185, 226)
    Z.zeichne_strecken(A_, iso, 0.22)
    tab(S, 40, 88, [("Dokument", 55), ("Angabe", 85)], [
        ("Dokumentnummer", DOKNR), ("3D-Modell", "TFO-A_Flaschenoeffner_Automatik.step"),
        ("Geometriequelle", "modell_d.py (CadQuery)"),
        ("Steuerungsprogramm", "sps/ (TwinCAT 3, Structured Text)"),
        ("Ausgabedatum", Z.DATUM), ("Dokumentenstatus", "Entwurf, nicht freigegeben"),
        ("Erstellt durch", "KI-Entwurf, Prüfung durch Fachkraft nötig"),
    ], 3.0, "Deckblatt")


def daten(pdf):
    S, y = kopf(pdf, "1  Übersicht und technische Daten")
    hs = [f[2] for f in A.FLASCHEN]
    ds = [f[3] for f in A.FLASCHEN]
    (b, t, h), _ = masse()
    y = tab(S, 20, y, [("Merkmal", 62), ("Wert", 118)], [
        ("Bauform", "Werkbankgerät mit Magnetbahn, Flasche für Flasche"),
        ("Abmessungen B × T × H", f"{b:.0f} × {t:.0f} × {h:.0f} mm (mit Bedienpanel, Signalsäule)"),
        ("Masse", "ca. 75 kg (Abschätzung)"),
        ("Magazin", "6 Mover; Laden und Entnehmen während des Betriebs"),
        ("Flaschen", f"Kronkorken 26 mm, H {min(hs):.1f} … {max(hs):.0f} mm, Ø {min(ds):.1f} … {max(ds):.0f} mm"),
        ("Sorten", "beliebig gemischt, Höhe wird je Flasche gemessen"),
        ("Öffnen", "Orbital-Entbördeln: 3 Rollen biegen die Zähne auf"),
        ("Takt", "ca. 4 … 6 s je Flasche (Schätzung, Entbördeln ca. 1 s)"),
        ("Antriebe", "Magnetbahn, 3 Servomotoren 48 V, 2 Getriebemotoren 24 V"),
        ("Steuerung", "Embedded-PC mit TwinCAT 3, EtherCAT, TwinSAFE"),
        ("Versorgung", "230 V AC, 24 V / 48 V DC, ca. 400 W Spitze"),
        ("Schutzeinrichtungen", "Haube, 2 Klappen und Deckel RFID-verriegelt, Not-Halt"),
        ("Kronkorken-Abfuhr", "Magnet-Überband, Magnet-Steigband, Turm (ca. 300 Stück)"),
    ], 3.0, "Daten")
    y = Z.ueberschrift(S, y, "1.1 Baugruppen")
    Z.liste(S, y, [
        "Magnetbahn: Motormodule in Stadionform (Geraden 400 mm, Kurven R 100), 6 Mover. Jeder "
        "Mover fährt für sich. Halter mit selbstzentrierender Klemme (zwei 90°-V-Backen, Feder).",
        "Stationen gegen den Uhrzeigersinn: Laden (vorn rechts), Messen (hinten rechts, Laser und "
        "Kamera), Öffnen (hinten Mitte), Ausgabe (vorn links). Kurvenschienen öffnen die Klemmen.",
        "Orbitalkopf auf einem Z-Linearmodul: zweigeteilter Ständer, geschlitzter Rotor und "
        "Zustellring (je ein Servo), drei Entbördelhebel mit Hartmetallrollen, Magnet-Überband.",
        "Kronkorken-Abfuhr: Überband (fährt mit Z) übergibt an ein senkrechtes Magnet-Steigband, "
        "oben fällt der Kronkorken über eine Rutsche in den abnehmbaren Sammelturm.",
        "Haube aus Profil 20×20 und Polycarbonat, zwei Klappen vorn (Ausgabe, Laden), "
        "Servicedeckel, Bedienpanel, Signalsäule. Schaltschrank hinten rechts.",
    ], 2.9)


def bedienung(pdf):
    S, y = kopf(pdf, "2  Bedienung")
    y = Z.absatz(S, 20, y, 180, "Vorn gibt es zwei Fächer mit eigener Klappe: links die Ausgabe der "
                 "geöffneten Flasche, rechts die Ladestelle. Ist eine Klappe offen, schalten alle Antriebe "
                 "sicher ab. Der Ablauf geht Flasche für Flasche: Während du eine Flasche nimmst, steht "
                 "die nächste schon gemessen vor dem Kopf.", 2.9)
    y = Z.ueberschrift(S, y, "2.1 Bedienelemente")
    y = tab(S, 20, y, [("Element", 46), ("Funktion", 134)], [
        ("-S1 Öffnen (grün)", "eine Flasche öffnen (oder am Panel: Anzahl wählen, Dauerbetrieb)"),
        ("-S3 Stopp (rot)", "nach dem laufenden Schritt anhalten"),
        ("-S4 Quittieren (blau)", "Sicherheit zurücksetzen nach Not-Halt oder offener Klappe"),
        ("-S0 Not-Halt", "Antriebe sofort sicher abgeschaltet (STO)"),
        ("Bedienpanel -A20", "Status je Mover, Zähler, Störungstexte, Einrichtbetrieb"),
        ("Alexa (optional)", "über MQTT: \"Alexa, schalte Bier ein\" = Öffnen"),
    ], 2.7, "Bedienung")
    y = Z.ueberschrift(S, y, "2.2 Abläufe")
    y = Z.liste(S, y, [
        "Bier holen: Öffnen drücken. Nach einem Takt steht die offene Flasche im linken Fach, "
        "Fachlicht an. Klappe öffnen, Flasche nach vorn herausziehen (die Klemme ist offen), schließen.",
        "Laden: Steht ein leerer Mover im rechten Fach, leuchtet das Fachlicht. Klappe öffnen, "
        "Flasche in die offene Klemme stellen, Klappe schließen, Quittieren. Jede Sorte ist erlaubt.",
        "Kronkorken leeren: Servicedeckel öffnen, Sammelturm am Griff drehen (Bajonett) und "
        "herausheben. Ohne Turm (-B13) oder bei vollem Turm (-B12) ist Öffnen gesperrt.",
        "Tropfwanne unter dem Kopf: bei offenem Deckel herausnehmen und spülen.",
    ], 2.8, True)
    y = Z.ueberschrift(S, y, "2.3 Sorten (keine Einstellung nötig)")
    zeilen = [(name, f"{D:.1f}", f"{H:.1f}", f"{A.zc_arbeit(H):.1f}", f"{A.backe_x(D):.1f}")
              for fid, name, H, D, _ in A.FLASCHEN]
    y = tab(S, 20, y, [("Sorte", 50), ("Ø mm", 20), ("Höhe mm", 22), ("Kopfhöhe ZC mm", 40), ("Backe zu (± mm)", 40)],
            zeilen, 2.5, "Sorten")
    Z.absatz(S, 20, y, 180, "Die Klemme zentriert jede Flasche auf die Bahn, der Laser misst die Höhe. "
             "\"Grenzmaß\" ist die Hüllflasche der Auslegung. Nur 26-mm-Kronkorken.", 2.5)


def funktion(pdf):
    S, y = kopf(pdf, "3  Funktion und Schrittkette")
    y = Z.absatz(S, 20, y, 180, "Prinzip Orbital-Entbördeln: Ein Kronkorken hält, weil seine 21 Zähne "
                 "unter den Wulst der Flasche gebogen sind. Statt ihn abzuhebeln, biegt der Kopf die Zähne "
                 "wieder auf. Drei gehärtete Rollen fahren 0,3 mm unter die Zahnkante und laufen auf dem "
                 "Rotor um den Hals. Am Ende der Zustellung steigen sie um 1,5 mm und biegen dabei immer "
                 "nur 2 bis 3 Zähne gleichzeitig auf, deshalb bleiben die Kräfte klein. Das Überband liegt "
                 "0,5 mm über dem Kronkorken: Es hält ihn gegen den Innendruck, das CO2 entweicht langsam "
                 "durch den Spalt (wenig Schaum). Danach hebt der Kopf 8 mm, der Kronkorken bleibt am "
                 "Magnetband hängen und wird ohne Greifer abtransportiert. Rotor und Ständer sind "
                 "geschlitzt: Die Flasche fährt auf der einen Seite hinein und auf der anderen heraus.", 2.75)
    y = Z.ueberschrift(S, y, "3.1 Schrittkette Öffnungsstation (je Flasche)")
    y = tab(S, 20, y, [("Schritt", 15), ("Name", 26), ("Weiterschaltbedingung", 104), ("Grenze", 35)],
            [(s, n, w, t) for s, n, a, w, t, f in SCHRITTE], 2.5, "Schrittkette")
    y = Z.ueberschrift(S, y, "3.2 Abweichungen")
    y = tab(S, 20, y, [("Schritt", 15), ("Name", 26), ("Abweichung und Reaktion", 139)],
            [(s, n, f) for s, n, a, w, t, f in SCHRITTE if f != "–"], 2.5, "Abweichungen")
    y = Z.ueberschrift(S, y, "3.3 Mover-Verwaltung")
    Z.liste(S, y, [
        "Jeder Mover hat einen Zustand (leer, voll, gemessen, offen) und kennt die Höhe seiner "
        "Flasche. Die Positionen liefert die Magnetbahn absolut, auch nach einem Stromausfall.",
        "Mover fahren nur in eine Station, wenn sie frei ist (Abstand mind. 180 mm). Bis zu zwei "
        "Mover warten vor dem Messen als Puffer.",
        "Eine Flasche ohne Kronkorken (Kamera) oder eine schon offene wird ohne Öffnen ausgegeben.",
    ], 2.55)


def grafcet(pdf):
    S = zeichnungsblatt(pdf, "Ablaufdiagramm", "TFO-A-E00", "Ablaufplan")
    S.text(25, 280, "GRAFCET nach DIN EN 60848 (vereinfacht): Öffnungsstation", 3.5, True)
    x, y, dy = 112, 268, 18.5
    schritte = [("0", "Grundstellung", "Achsen ein, Z oben, Rotor 0°, Zustellung 0"),
                ("1", "Bereit", "P1 grün, wartet auf gemessenen Mover"),
                ("2", "S1 Messen", "Mover unter -B3/-B4, Höhe und Verschluss"),
                ("3", "S2 Einstellen", "M1 auf ZC, M2 Schlitz 0°"),
                ("4", "S3 Einfahren", "Mover in den Kopf, 50 mm/s"),
                ("5", "S4 Entbördeln", "M2 2 Umdr., M3 Kurvenscheibe 0-100-0 %"),
                ("6", "S5 Entlüften", "warten 0,3 s"),
                ("7", "S6 Abheben", "M1 + 8 mm"),
                ("8", "S7 Ausfahren", "M2 Schlitz 180°, Mover weiter, M4 ein"),
                ("9", "S8 Abfuhr", "M4, M5 ein, Zähler +1 bei -B11"),
                ("10", "S9 Ausgabe", "Fachlicht Ausgabe, Klemme offen")]
    trans = ["Achsen bereit · TwinSAFE OK", "Öffnen (S1/Panel) · Turm da, nicht voll · Mover gemessen",
             "Höhe plausibel · -B4 Kronkorken", "M1, M2 in Position", "Mover in Position",
             "Kurvenscheibe fertig", "t > 0,3 s", "-B8 Kronkorken am Band", "Mover > 70 mm aus dem Kopf",
             "Flanke -B11", "-B6 = 0 (entnommen)"]
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
    yb = y - 10 * dy
    S.linie(x, yb - 6, x, yb - 12, 0.35)
    S.linie(x - 5, yb - 9, x + 5, yb - 9, 0.7)
    S.text(x - 7, yb - 10, trans[10], 2.3, ausr="r")
    xr = 22
    S.pfad([(x, yb - 12), (xr, yb - 12), (xr, y - dy + 9), (x, y - dy + 9)], 0.35)
    S.pfeil(x, y - dy + 9, 0)
    S.text(xr - 1.5, (yb + y) / 2, "nächste Flasche", 2.4, winkel=90)
    bx = 240
    S.text(bx, 280, "Parallele Abläufe (eigene Schrittketten)", 3.2, True)
    par = (("Mover-Disposition", "fährt jeden Mover zur nächsten freien Station, hält 180 mm Abstand"),
           ("Laden", "leerer Mover an der Ladestelle, Klemme offen, wartet auf -B7 und Klappe zu"),
           ("Ausgabe", "Fachlicht, wartet auf -B6 = 0, danach zum Laden"),
           ("Kronkorken-Abfuhr", "Bänder laufen nach, bis -B11 kommt oder 4 s vergangen sind"))
    yy = 272
    for k, t in par:
        S.text(bx, yy, k, 2.7, True)
        S.text(bx, yy - 4.5, t, 2.5)
        yy -= 12
    S.text(bx, 214, "Neben- und Fehlerzweige", 3.2, True)
    zw = (("aus 2", "kein Kronkorken (-B4) oder offen: ohne Öffnen zu 8 (Ausgabe)"),
          ("aus 2", "Höhe außerhalb 171 … 352 mm: Mover hält, Meldung, Bediener nimmt"),
          ("", "die Flasche an der Ausgabe heraus"),
          ("aus 5", "Momentgrenze Rotor/Zustellung: Rollen zurück, Störung, Quittieren"),
          ("aus 7", "-B8 = 0: Warnung \"Kronkorken nicht am Band\", weiter mit 8"),
          ("aus 9", "kein -B11 in 4 s: Warnung, Zähler unverändert"),
          ("jeder", "TwinSAFE: Not-Halt oder Klappe offen -> STO aller Antriebe,"),
          ("", "Magnetbahn-Leistung aus. Nach dem Schließen: Quittieren -S4,"),
          ("", "Positionen bleiben gültig (Absolutgeber)"),
          ("jeder", "Stopp (S3): nach dem laufenden Schritt anhalten"))
    for i, (k, t) in enumerate(zw):
        S.text(bx, 206 - i * 6, k, 2.6, True)
        S.text(bx + 15, 206 - i * 6, t, 2.6)
    S.text(bx, 130, "Legende", 3.0, True)
    for i, t in enumerate(("Doppelrahmen = Anfangsschritt, Rahmen = Schritt", "Querstrich = Transition mit Bedingung",
                           "Rechteck rechts = Aktion (solange der Schritt aktiv ist)", "· = logisches UND",
                           "Grenzzeiten siehe Schrittkette (Seite 4)")):
        S.text(bx, 124 - i * 5.5, t, 2.6)


def sicherheit(pdf):
    S, y = kopf(pdf, "4  Sicherheitskonzept")
    y = Z.absatz(S, 20, y, 180, "Grundlage: Maschinenverordnung (EU) 2023/1230, EN ISO 12100, EN ISO 13849-1, "
                 "EN ISO 14119, EN ISO 13850, EN ISO 13857, EN 60204-1. Die Sicherheitslogik läuft in einer "
                 "TwinSAFE-Logik (EL6910) über FSoE (Safety over EtherCAT). Die Einschätzung ist ein Entwurf "
                 "und ersetzt keine Risikobeurteilung durch eine fachkundige Person.", 2.8)
    y = Z.ueberschrift(S, y, "4.1 Gefährdungen und Maßnahmen")
    y = tab(S, 20, y, [("Gefährdung", 40), ("Ort", 44), ("Maßnahme", 96)], [
        ("Quetschen, Stoß", "Mover, Bahn", "Haube fest, Klappen und Deckel verriegelt"),
        ("Quetschen, Einziehen", "Rotor, Hebel, Bänder", "nur bei offenem Deckel erreichbar, STO"),
        ("Hineingreifen", "Fächer 150 × 430 mm", "Klappen RFID-verriegelt (B1a, B1b)"),
        ("Glasbruch, Splitter", "Öffnungsstation", "Haube PC 4 mm, Momentgrenzen M2/M3"),
        ("Magnetfeld", "Bänder, Mover", "Hinweisschild (Herzschrittmacher)"),
        ("Elektrischer Schlag", "Schaltschrank 230 V", "Schutzklasse I, PE, -Q1, Tür mit Werkzeug"),
        ("Unerwarteter Anlauf", "alle Antriebe", "Schließen startet nichts, Quittieren -S4"),
    ], 2.6, "Sicherheit")
    y = Z.ueberschrift(S, y, "4.2 Sicherheitsfunktionen")
    y = tab(S, 20, y, [("SF", 12), ("Auslöser", 52), ("Reaktion", 76), ("PLr (Entwurf)", 40)], [
        ("SF1", "Not-Halt -S0", "SS1: Bremsrampe, dann STO alle", "PL d, Kat. 3"),
        ("SF2", "Klappe Ausgabe -B1a offen", "STO Magnetbahn und Kopf", "PL d, Kat. 3"),
        ("SF3", "Klappe Laden -B1b offen", "wie SF2", "PL d, Kat. 3"),
        ("SF4", "Servicedeckel -B1c offen", "wie SF2", "PL d, Kat. 3"),
        ("SF5", "Wiederanlauf", "nur mit -S4 Quittieren", "manueller Start"),
    ], 2.6, "Sicherheit")
    y = Z.ueberschrift(S, y, "4.3 Umsetzung")
    Z.liste(S, y, [
        "Not-Halt -S0 zweikanalig auf EL1904. Sicherheitsschalter mit RFID-Codierung und OSSD-"
        "Ausgängen (Typ 4, hohe Codierung, EN ISO 14119) auf EL1904.",
        "EL6910 schaltet über EL2904 die Leistung der Magnetbahn ab und gibt das STO der drei "
        "Servoklemmen EL7221-9014 frei. Die Getriebemotoren der Bänder laufen über einen "
        "sicheren Ausgang.",
        "Die Z-Achse hat einen Motor mit Haltebremse: Der Kopf sinkt bei STO nicht ab.",
        "Mögliche Erweiterung: Zonen-STO. Bei offener Ladeklappe dürfte der Kopf weiterarbeiten, "
        "wenn nachgewiesen ist, dass kein Mover in die Ladezone fährt (Safe Position).",
        "Validierung: PL mit SISTEMA nachrechnen, TwinSAFE-Projekt prüfen und verifizieren.",
    ], 2.7)


def betriebsmittel(pdf):
    S, y = kopf(pdf, "5  Betriebsmittel")
    tab(S, 20, y, [("BMK", 14), ("Benennung", 52), ("Typ / Daten", 84), ("Anschluss", 30)],
        BETRIEBSMITTEL, 2.3, "Betriebsmittel")


def io_liste(pdf):
    S, y = kopf(pdf, "6  EtherCAT-I/O-Liste")
    y = Z.absatz(S, 20, y, 180, "Alle Signale laufen über EtherCAT. Standard-Ein- und Ausgänge auf EL1809 und "
                 "EL2809 (24 V, PNP), Höhe als 4 … 20 mA auf EL3052, Bandmotoren auf EL7332. Sichere Signale "
                 "siehe Kapitel 4 und Stromlaufplan Blatt 1.", 2.7)
    y = Z.ueberschrift(S, y, "6.1 Eingänge")
    y = tab(S, 20, y, [("Adr.", 12), ("Klemme", 24), ("BMK", 18), ("Signal", 62), ("Bemerkung", 64)],
            EINGAENGE, 2.4, "Eingänge")
    y = Z.ueberschrift(S, y, "6.2 Ausgänge")
    tab(S, 20, y, [("Adr.", 12), ("Klemme", 24), ("BMK", 18), ("Signal", 62), ("Bemerkung", 64)],
        AUSGAENGE, 2.4, "Ausgänge")


# ---------------------------------------------------------------- Stromlaufplan
def klemme(S, x, y, t=""):
    S.kreis(x, y, 0.8, 0.25, fuellen=1.0)
    if t:
        S.text(x + 1.2, y + 1.0, t, 1.8)


def oeffner(S, x, y, t=""):
    S.linie(x, y, x, y - 3, 0.35)
    S.linie(x, y - 7, x, y - 10, 0.35)
    S.linie(x - 3, y - 3, x + 0.6, y - 7.5, 0.35)
    S.linie(x, y - 3, x - 3, y - 3, 0.35)
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


def stromlauf_1(pdf):
    S = zeichnungsblatt(pdf, "Einspeisung, Sicherheit", "TFO-A-E01", "Stromlaufplan", "1/3")
    S.text(30, 278, "Einspeisung 230 V, Netzteile 24 V / 48 V, TwinSAFE (Not-Halt, Klappen, Deckel)", 3.5, True)
    for t, y in (("L", 255), ("N", 249), ("PE", 243)):
        klemme(S, 30, y, t)
        S.linie(30, y, 45, y, 0.35)
    S.rechteck(45, 240, 57, 258, 0.5)
    S.text(51, 260, "-Q1", 2.6, True, "m")
    S.linie(57, 255, 70, 255, 0.35)
    S.rechteck(70, 253.5, 80, 256.5, 0.35)
    S.text(75, 258, "-F1 C10A", 2.2, ausr="m")
    S.linie(80, 255, 95, 255, 0.35)
    S.linie(57, 249, 95, 249, 0.35)
    S.linie(45, 243, 95, 243, 0.35)
    for i, (bmk, txt, schiene, ys, sich) in enumerate((("-T1", "Netzteil\n24 V 20 A", "+24V", 225, "-F2 B6A"),
                                                       ("-T2", "Netzteil\n48 V 20 A", "+48V", 215, "-F3 B16A"))):
        x0 = 95 + i * 50
        t = geraet(S, x0, 232, x0 + 32, 262, bmk, txt, ("L", "N", "PE"), ("+", "-", "OK"))
        if i == 1:                       # -T2 parallel an L, N, PE (über -T1 hinweggeführt)
            for k, (p_, yy) in enumerate((("L", 255), ("N", 249), ("PE", 243))):
                xa, yo = 88 + k * 2, 266 + k * 2
                S.pfad([(xa, yy), (xa, yo), (x0 - 6 + k * 2, yo), (x0 - 6 + k * 2, t[p_][1]), t[p_]], 0.3)
        S.pfad([t["+"], (t["+"][0] + 8, t["+"][1]), (t["+"][0] + 8, ys)], 0.35)
        S.text(t["+"][0] + 10, ys + 8, sich, 2.0)
        S.pfad([t["-"], (t["-"][0] + 5, t["-"][1]), (t["-"][0] + 5, 106)], 0.35)
        S.linie(35 if i == 0 else 175, ys, 405, ys, 0.5)
        S.text(405, ys + 1.5, f"{schiene} ({'Steuerung, I/O' if i == 0 else 'Magnetbahn, Servos, über EL2904'})", 2.3, ausr="r")
    S.linie(35, 106, 405, 106, 0.5)
    S.text(405, 102.5, "0V (M)", 2.4, ausr="r")
    # TwinSAFE
    ec = geraet(S, 230, 140, 400, 190, "-A4", "TwinSAFE: EL6910 Logik · 2 × EL1904 · EL2904",
                pins_o=("1.1", "1.2", "1.3", "1.4", "2.1", "2.2", "2.3", "2.4"), pins_u=("O1", "O2", "O3", "O4"))
    sensoren = (("-S0", "1.1", "1.2", "Not-Halt"), ("-B1a", "1.3", "1.4", "Klappe Ausgabe"),
                ("-B1b", "2.1", "2.2", "Klappe Laden"), ("-B1c", "2.3", "2.4", "Deckel"))
    for bmk, a, b, txt in sensoren:
        xa, xb = ec[a][0], ec[b][0]
        if bmk == "-S0":
            S.pfad([(xa, 190), (xa, 208)], 0.3)
            oeffner(S, xa, 218, "")
            S.pfad([(xb, 190), (xb, 208)], 0.3)
            oeffner(S, xb, 218, "")
        else:
            S.rechteck(xa - 1.5, 198, xb + 1.5, 212, 0.4)
            S.text((xa + xb) / 2, 204, "OSSD", 1.9, ausr="m")
            S.linie(xa, 190, xa, 198, 0.3)
            S.linie(xb, 190, xb, 198, 0.3)
        S.text((xa + xb) / 2, 228 if bmk == "-S0" else 214, bmk, 2.2, True, "m")
        S.text((xa + xb) / 2, 194.5, txt, 1.7, ausr="m")
    for o, t in (("O1", "STO -A3 (3 Servos)"), ("O2", "Leistung Magnetbahn -A10"), ("O3", "+24 V Bandmotoren"),
                 ("O4", "Reserve")):
        x_, y_ = ec[o]
        S.linie(x_, y_, x_, y_ - 12, 0.3)
        S.text(x_, y_ - 15, t, 1.8, ausr="m")
    S.text(30, 180, "-S4 Quittieren: Standard-Eingang, in der TwinSAFE-Logik als Reset (Flanke) verwendet.", 2.3)
    S.text(30, 175, "EL6910 überwacht Querschluss und Gleichzeitigkeit der zwei Kanäle (Diskrepanzzeit 50 ms).", 2.3)
    S.text(30, 96, "Leitungsquerschnitte: 230 V 1,5 mm², 48 V 2,5 mm², 24 V 0,75 mm², Signale 0,25 mm². "
                   "PE an Deckplatte, Rahmen, Schaltschrank, Bahn.", 2.4)
    S.text(30, 91, "Sicherheitsschalter: Typ 4 mit RFID (hohe Codierung), OSSD-Ausgänge. Kanäle getrennt verlegen.", 2.4)


def stromlauf_2(pdf):
    S = zeichnungsblatt(pdf, "Antriebe", "TFO-A-E02", "Stromlaufplan", "2/3")
    S.text(30, 278, "Antriebe: Magnetbahn, Servos Z / Rotor / Zustellung, Bandmotoren", 3.5, True)
    yl, y24, y0v = 255, 245, 110
    S.linie(30, yl, 400, yl, 0.5)
    S.text(30, yl + 1.5, "+48V Leistung (über EL2904, Blatt 1)", 2.4)
    S.linie(30, y24, 400, y24, 0.5)
    S.text(30, y24 + 1.5, "+24V Bandmotoren (sicher geschaltet)", 2.4)
    S.linie(30, y0v, 400, y0v, 0.5)
    S.text(30, y0v - 3.5, "0V", 2.4)
    bahn = geraet(S, 35, 175, 105, 225, "-A10", "Magnetbahn\n6 Mover, 1428 mm", pins_o=("48V",), pins_u=("0V",),
                  pins_l=("ECAT",))
    S.linie(bahn["48V"][0], bahn["48V"][1], bahn["48V"][0], yl, 0.3)
    S.linie(bahn["0V"][0], bahn["0V"][1], bahn["0V"][0], y0v, 0.3)
    S.text(70, 168, "Einspeisung + Motormodule", 2.2, ausr="m")
    for j, (bmk, mot, name) in enumerate((("-A3.1", "-M1", "Z-Achse"), ("-A3.2", "-M2", "Rotor"),
                                          ("-A3.3", "-M3", "Zustellring"))):
        x = 130 + j * 62
        d = geraet(S, x, 180, x + 44, 225, bmk, f"EL7221-9014\n{name}", pins_o=("Up",), pins_u=("0V",),
                   pins_r=("U", "V", "W", "STO"))
        S.linie(d["Up"][0], d["Up"][1], d["Up"][0], yl, 0.3)
        S.linie(d["0V"][0], d["0V"][1], d["0V"][0], y0v, 0.3)
        mx, my = x + 22, 145
        S.kreis(mx, my, 9, 0.5)
        S.text(mx, my - 1.5, "M", 4, True, "m")
        S.text(mx, my - 14, f"{mot} Servo 48 V", 2.3, ausr="m")
        for k, p in enumerate(("U", "V", "W")):
            px, py = d[p]
            S.pfad([(px, py), (px + 4 + k * 2, py), (px + 4 + k * 2, 165), (mx - 4 + k * 4, 165), (mx - 4 + k * 4, my + 8)], 0.3)
        S.text(d["STO"][0] + 1, d["STO"][1] - 0.8, "<- EL2904 O1", 1.7)
    dc = geraet(S, 330, 185, 380, 225, "-A2", "EL7332\nDC-Motor 2-kanalig", pins_o=("24V",), pins_u=("0V",),
                pins_r=("M1+", "M1-", "M2+", "M2-"))
    S.linie(dc["24V"][0], dc["24V"][1], dc["24V"][0], y24, 0.3)
    S.linie(dc["0V"][0], dc["0V"][1], dc["0V"][0], y0v, 0.3)
    for k, (mot, txt, yy) in enumerate((("-M4", "Überband", 150), ("-M5", "Steigband", 128))):
        S.kreis(392, yy, 6, 0.5)
        S.text(392, yy - 1.2, "M", 3, True, "m")
        S.text(392, yy - 10, f"{mot} {txt}", 2.0, ausr="m")
        a, b = dc[f"M{k + 1}+"], dc[f"M{k + 1}-"]
        S.pfad([a, (386, a[1]), (386, yy + 3), (389, yy + 3)], 0.3)
        S.pfad([b, (384, b[1]), (384, yy - 3), (389, yy - 3)], 0.3)
    S.text(30, 95, "Servomotoren mit Ein-Kabel-Technik (Geber im Motorkabel), M1 mit Haltebremse 24 V.", 2.4)
    S.text(30, 90, "Zustellung über elektronische Kurvenscheibe M3 = f(M2) in TwinCAT NC (Phasenversatz Rotor / Zustellring).", 2.4)


def stromlauf_3(pdf):
    S = zeichnungsblatt(pdf, "Steuerung, EtherCAT", "TFO-A-E03", "Stromlaufplan", "3/3")
    S.text(25, 280, "EtherCAT-Strang, Standard-Ein- und Ausgänge, Ethernet", 3.5, True)
    pc = geraet(S, 25, 200, 75, 250, "-A1", "Embedded-PC\nTwinCAT 3", pins_r=("ECAT", "LAN 2"), pins_u=("24V",))
    S.text(50, 192, "LAN 2: Panel -A20, Kamera -B4, WLAN (MQTT)", 1.9, ausr="m")
    kette = [("-A2", "EK1100"), ("", "EL1809"), ("", "EL2809"), ("", "EL3052"), ("", "EL7332"),
             ("-A4", "EL6910"), ("", "EL1904"), ("", "EL1904"), ("", "EL2904"), ("-A3", "EL7221 ×3")]
    x = 95
    for i, (bmk, typ) in enumerate(kette):
        w = 26 if typ != "EL7221 ×3" else 34
        S.rechteck(x, 205, x + w, 245, 0.4)
        S.text(x + w / 2, 236, typ, 2.1, True, "m")
        if bmk:
            S.text(x + w / 2, 247.5, bmk, 2.0, ausr="m")
        x += w + 2
    S.pfad([pc["ECAT"], (95, pc["ECAT"][1])], 0.6)
    S.pfad([(x - 2, 225), (x + 8, 225), (x + 8, 185), (370, 185)], 0.6)
    S.rechteck(370, 175, 405, 195, 0.4)
    S.text(387.5, 186, "-A10", 2.4, True, "m")
    S.text(387.5, 181, "Magnetbahn", 1.9, ausr="m")
    S.text(100, 200, "E-Bus", 2.0)
    # Eingänge EL1809
    y = 165
    S.text(25, y + 8, "EL1809 (16 DI, 24 V)", 2.6, True)
    for i, (a, k, b, sig, bem) in enumerate([e for e in EINGAENGE if e[1].startswith("EL1809")]):
        xx = 30 + i * 15
        S.rechteck(xx - 2.8, y - 18, xx + 2.8, y - 8, 0.4)
        S.linie(xx - 2.8, y - 8, xx + 2.8, y - 18, 0.25)
        S.linie(xx, y - 8, xx, y, 0.3)
        S.text(xx, y - 22, b, 1.8, ausr="m")
        S.text(xx - 1, y - 26, sig[:14], 1.6, winkel=90)
        S.text(xx, y + 2, a, 1.8, ausr="m")
    S.text(25, 98, "Sensoren PNP 3-Leiter: BN +24 V, BU 0 V, BK Signal. Kamera mit Schaltausgängen.", 2.2)
    # Ausgänge EL2809 und Analog
    y2 = 165
    S.text(225, y2 + 8, "EL2809 (16 DO) · EL3052 (2 AI 4 … 20 mA)", 2.6, True)
    for i, (a, k, b, sig, bem) in enumerate([e for e in AUSGAENGE if e[1].startswith("EL2809")]):
        xx = 230 + i * 15
        S.kreis(xx, y2 - 13, 2.4, 0.35)
        S.linie(xx - 1.7, y2 - 14.7, xx + 1.7, y2 - 11.3, 0.25)
        S.linie(xx - 1.7, y2 - 11.3, xx + 1.7, y2 - 14.7, 0.25)
        S.linie(xx, y2 - 10.6, xx, y2, 0.3)
        S.text(xx, y2 - 20, b, 1.8, ausr="m")
        S.text(xx - 1, y2 - 24, sig[:14], 1.6, winkel=90)
        S.text(xx, y2 + 2, a, 1.8, ausr="m")
    S.rechteck(355, 140, 400, 160, 0.4)
    S.text(377.5, 152, "-B3 Laser", 2.2, True, "m")
    S.text(377.5, 146, "4 … 20 mA -> AI1", 1.9, ausr="m")
    S.text(225, 98, "Lasten zwischen Ausgang und 0 V (High-Side, EL2809). Schirm der Analogleitung einseitig an PE.", 2.2)


def ansichten(pdf, T):
    S = zeichnungsblatt(pdf, "Zusammenbau", "TFO-A-000", "Zeichnung", "1/2", "1:15")
    m = 1 / 15
    AV = Z.Ansicht(S, 75, 175, m)
    AD = Z.Ansicht(S, 75, 105, m)
    AL = Z.Ansicht(S, 190, 175, m)
    Z.zeichne_strecken(AV, Z.kanten_sichtbar(T, T, "vorne", res=0.8, eps=1.5), 0.22)
    Z.zeichne_strecken(AD, Z.kanten_sichtbar(T, T, "oben", res=0.8, eps=1.5), 0.22)
    Z.zeichne_strecken(AL, Z.kanten_sichtbar(T, T, "links", res=0.8, eps=1.5), 0.22)
    iso = Z.kanten_sichtbar(T, T, "iso", res=0.8, eps=1.5)
    AI = Z.einpassen(S, iso, 255, 62, 405, 272)
    Z.zeichne_strecken(AI, iso, 0.2)
    S.text(330, 278, "Isometrie (ohne Maßstab, ohne Scheiben)", 2.8, ausr="m")
    (b, t, h), (bx0, bx1, by0, by1, bz0, bz1) = masse()
    AV.mass((bx0, 0), (bx1, 0), "h", -7, text=f"{b:.0f}")
    AV.mass((bx0, bz0), (bx0, bz1), "v", -8, text=f"{h:.0f}")
    AD.mass((bx1, by0), (bx1, by1), "v", 8, text=f"{t:.0f}")
    AL.mass((-by1, 0), (-by0, 0), "h", -7, text=f"{t:.0f}")
    Z.notizen(S, 25, 52, [
        "Ansichten aus der STEP-Baugruppe TFO-A_Flaschenoeffner_Automatik.step (Scheiben ausgeblendet).",
        "Ausgabe vorn links, Laden vorn rechts, Öffnungsstation hinten Mitte, Turm hinten links.",
        "Alle Maße in mm. Dargestellt: 6 Mover an ihren Stationen, Kopf auf NRW 0,5 l, Rollen zurück.",
    ], 2.5, "Hinweise")


def stueckliste(pdf):
    S = zeichnungsblatt(pdf, "Stückliste", "TFO-A-000", "Stückliste", "2/2")
    eigen, kauf = stueckliste_daten()
    sp = [("Pos.", 13), ("Menge", 12), ("Benennung", 110), ("Werkstoff / Hinweis", 55)]
    zh = 3.4
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
            if Z.tb(str(t), 2.1, fett) > b - 2:
                WARNUNGEN.append(f"Stückliste: '{t}' zu lang")
            S.text(x + 1.2, y - zh + 1.0, str(t), 2.1, fett)
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
    y = Z.ueberschrift(S, y, "7.1 TwinCAT-Projekt")
    y = Z.liste(S, y, [
        "TwinCAT 3 XAE (Visual Studio Shell), neues Projekt, Zielsystem = Embedded-PC -A1. "
        "EtherCAT-Strang scannen, Klemmen und Magnetbahn übernehmen.",
        "Quelltexte aus dem Ordner sps/ als POUs anlegen (Structured Text): GVL_Anlage, "
        "FB_Mover, FB_Oeffnungsstation, MAIN. Achsen in der NC anlegen und verknüpfen.",
        "TwinSAFE-Projekt mit SF1 bis SF5 (Kapitel 4) erstellen, auf die EL6910 laden, verifizieren.",
        "Panel -A20: TwinCAT HMI oder Web-Visualisierung. Alexa über MQTT (Tc3_IotBase).",
    ], 2.6, True)
    y = Z.ueberschrift(S, y, "7.2 Erstinbetriebnahme (Deckel offen, Leistung aus)")
    y = Z.liste(S, y, [
        "Verdrahtung nach Stromlaufplan, Isolationsmessung, PE-Durchgang. Netzteile einzeln prüfen.",
        "Sicherheitsfunktionen SF1 bis SF5 mit Prüfprotokoll testen (Querschluss, Diskrepanz).",
        "Magnetbahn: Mover-Erkennung, Fahrrichtung gegen den Uhrzeigersinn, Stationspositionen "
        "(Ausgabe, Laden, Messen, Öffnen) einteachen. Abstand zwischen Movern mind. 180 mm.",
        "Klemmen: Kurvenschienen so einstellen, dass die Backen an Ausgabe und Laden ganz öffnen.",
        "Laser -B3 mit Lehre kalibrieren (zwei Höhen), Kamera -B4 auf Kronkorken / Bügel einlernen.",
        "Kopf: ZC-Bezug mit Einstellflasche ermitteln. Rotor-Nullpunkt = Schlitz bei +x (Einfahrt). "
        "Zustellung: Rollenkante 0,25 mm neben dem Glas (Fühlerlehre), Anstieg 1,5 mm prüfen.",
        "Probelauf mit leeren, verschlossenen Flaschen der kleinsten und größten Sorte: "
        "Moment M2/M3 aufzeichnen, Momentgrenzen setzen, Takt optimieren.",
    ], 2.55, True)
    y = Z.ueberschrift(S, y, "7.3 Offene Punkte (Prototyp)")
    Z.liste(S, y, [
        "Orbital-Entbördeln ist eine Neuentwicklung: Rollenform, Zustellweg, Drehzahl und Zahl "
        "der Umdrehungen am Versuchsstand ermitteln (Kronkorken verschiedener Hersteller).",
        "Haltekraft des Überbands gegen den Innendruck (bis ca. 3 bar) und Entlüftungsspalt prüfen.",
        "Übergabe Überband -> Steigband bei allen Kopfhöhen testen.",
        "Steuerungsprogramm ist ungetestet (Gerüst, nicht übersetzt).",
        "Risikobeurteilung und PL-Nachweis (SISTEMA) durch eine Fachkraft.",
    ], 2.55)


def main():
    A.aufbauen()
    print("Lese STEP-Baugruppe und berechne Ansichten …")
    T = step_dreiecke()
    iso = Z.kanten_sichtbar(T, T, "iso", res=0.9, eps=1.5)
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
