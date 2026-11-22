"""
Detaillierte STEP-Baugruppe (AP214, mit Namen und Farben) des automatischen
Flaschenöffners TFO-A, aufgebaut mit CadQuery (OpenCascade, exakte B-Rep-Geometrie).

  - Baugruppenstruktur: Gestell, Sternrad, Z-Achse, Öffnerkopf, Abfuhr, Sensorik,
    Haube, Bedienung, Elektro, Flaschen
  - Systemprofile mit Nuten und Kernbohrung, Eigenfertigungsteile mit Bohrungen,
    Senkungen und Kernlöchern (Gewinde als Kernlochbohrung dargestellt)
  - Kaufteile vereinfacht, aber maßlich richtig (NEMA17, MGN12, TR8, Sensoren, …)

Maße und Lage stammen aus erzeuge_automatik.py (eine gemeinsame Quelle).
Aufruf:  python erzeuge_step.py      ->  TFO-A_Flaschenoeffner_Automatik.step
"""
import math
import sys
from pathlib import Path

import cadquery as cq
from cadquery import Color, Location, Vector

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent))
import erzeuge_automatik as A  # noqa: E402
import erzeuge_stl as M        # noqa: E402

AUSGABE = HIER / "TFO-A_Flaschenoeffner_Automatik.step"
V = Vector

FARBEN = {
    "alu": (0.78, 0.80, 0.84, 1), "alu_eloxiert": (0.25, 0.53, 0.84, 1), "stahl": (0.42, 0.44, 0.48, 1),
    "stahl_hell": (0.66, 0.68, 0.70, 1), "schwarz": (0.12, 0.12, 0.14, 1), "pe": (0.93, 0.93, 0.90, 1),
    "pe_blau": (0.30, 0.55, 0.85, 1), "gummi": (0.10, 0.10, 0.11, 1), "messing": (0.80, 0.65, 0.25, 1),
    "sensor": (0.15, 0.55, 0.75, 1), "rot": (0.80, 0.12, 0.14, 1), "gruen": (0.15, 0.65, 0.30, 1),
    "gelb": (0.95, 0.75, 0.10, 1), "blau": (0.15, 0.40, 0.80, 1), "grau": (0.55, 0.57, 0.60, 1),
    "pc": (0.70, 0.85, 0.95, 0.25), "glas": (0.43, 0.24, 0.08, 0.85), "etikett": (0.92, 0.90, 0.84, 1),
    "kronkorken": (0.83, 0.69, 0.22, 1), "kabel": (0.20, 0.22, 0.25, 1), "feder": (0.70, 0.72, 0.75, 1),
}


def farbe(n):
    return Color(*FARBEN[n])


# ================================================================ Grundformen
def kasten(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def zyl(achse, mitte, a0, a1, r):
    """Zylinder entlang Achse; mitte = Punkt auf der Achse bei a = 0."""
    d = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}[achse]
    p = V(*mitte) + d * a0
    return cq.Solid.makeCylinder(r, a1 - a0, p, d)


def bohren(teil, achse, mitte, a0, a1, d):
    return teil.cut(zyl(achse, mitte, a0 - 0.1, a1 + 0.1, d / 2))


def senkung(teil, x, y, z_oben, d_kopf, d_loch, dicke, oben=True):
    """Kegelsenkung 90° für Senkschraube, von oben (oder unten) in eine Platte."""
    h = (d_kopf - d_loch) / 2
    if oben:
        kegel = cq.Solid.makeCone(d_loch / 2, d_kopf / 2, h + 0.01, V(x, y, z_oben - h), V(0, 0, 1))
        return bohren(teil, "z", (x, y, 0), z_oben - dicke, z_oben, d_loch).cut(kegel)
    kegel = cq.Solid.makeCone(d_kopf / 2, d_loch / 2, h + 0.01, V(x, y, z_oben - dicke - 0.01), V(0, 0, 1))
    return bohren(teil, "z", (x, y, 0), z_oben - dicke, z_oben, d_loch).cut(kegel)


def zylsenkung(teil, x, y, z_unten, d_kopf, t_kopf, d_loch, dicke):
    """Zylindersenkung von unten (DIN 974) für Zylinderschraube."""
    teil = bohren(teil, "z", (x, y, 0), z_unten, z_unten + dicke, d_loch)
    return teil.cut(zyl("z", (x, y, 0), z_unten - 0.1, z_unten + t_kopf, d_kopf / 2))


def sechskant(achse, mitte, a0, a1, sw):
    """Sechskantprisma (Schlüsselweite sw) entlang Achse von a0 bis a1, wie zyl()."""
    r = sw / math.sqrt(3)
    s = cq.Workplane("XY").polygon(6, 2 * r).extrude(a1 - a0).val().translate(V(0, 0, a0))
    if achse == "x":
        s = s.rotate(V(0, 0, 0), V(0, 1, 0), 90)
    elif achse == "y":
        s = s.rotate(V(0, 0, 0), V(1, 0, 0), -90)
    return s.translate(V(*mitte))


def nutprofil(breite, hoehe, laenge, achse, ecke):
    """Systemprofil Nut 8 (Raster 40), Querschnitt mit T-Nuten und Kernbohrungen.
    ecke = Punkt mit kleinsten Koordinaten."""
    sk = cq.Sketch().rect(breite, hoehe)
    for i in range(int(breite // 40)):
        cx = -breite / 2 + 20 + 40 * i
        for sgn in (1, -1):
            sk = sk.push([(cx, sgn * (hoehe / 2 - 2.15))]).rect(8.2, 4.3, mode="s").reset()
            sk = sk.push([(cx, sgn * (hoehe / 2 - 4.3 - 4.6))]).rect(14, 9.2, mode="s").reset()
    for j in range(int(hoehe // 40)):
        cy = -hoehe / 2 + 20 + 40 * j
        for sgn in (1, -1):
            sk = sk.push([(sgn * (breite / 2 - 2.15), cy)]).rect(4.3, 8.2, mode="s").reset()
            sk = sk.push([(sgn * (breite / 2 - 4.3 - 4.6), cy)]).rect(9.2, 14, mode="s").reset()
    for i in range(int(breite // 40)):
        for j in range(int(hoehe // 40)):
            sk = sk.push([(-breite / 2 + 20 + 40 * i, -hoehe / 2 + 20 + 40 * j)]).circle(3.4, mode="s").reset()
    s = cq.Workplane("XY").placeSketch(sk).extrude(laenge).val()
    s = s.translate(V(breite / 2, hoehe / 2, 0))
    if achse == "x":   # Länge entlang X, Querschnitt (breite in Y, hoehe in Z)
        s = s.rotate(V(0, 0, 0), V(0, 1, 0), 90).rotate(V(0, 0, 0), V(1, 0, 0), 90)
        s = s.translate(V(0, 0, 0))
        bb = s.BoundingBox()
        s = s.translate(V(-bb.xmin, -bb.ymin, -bb.zmin))
    elif achse == "y":
        s = s.rotate(V(0, 0, 0), V(1, 0, 0), -90)
        bb = s.BoundingBox()
        s = s.translate(V(-bb.xmin, -bb.ymin, -bb.zmin))
    return s.translate(V(*ecke))


def revolve_profil(pts, mitte=(0, 0, 0)):
    """Rotationskörper um die Z-Achse aus Profil [(r, z), ...] (geschlossen über die Achse)."""
    wp = cq.Workplane("XZ").polyline([(0, pts[0][1])] + list(pts) + [(0, pts[-1][1])]).close()
    return wp.revolve(360, (0, 0, 0), (0, 1, 0)).val().translate(V(*mitte))


# ================================================================ Baugruppe
ASM = cq.Assembly(name="TFO-A_Flaschenoeffner_Automatik")
GRUPPEN = {}
ZAEHLER = {}


def teil(gruppe, name, form, f, loc=None):
    if gruppe not in GRUPPEN:
        GRUPPEN[gruppe] = cq.Assembly(name=gruppe)
    n = ZAEHLER.get(name, 0) + 1
    ZAEHLER[name] = n
    GRUPPEN[gruppe].add(form, name=name if n == 1 else f"{name}_{n}", color=farbe(f), loc=loc)


YS = A.YS
Y = A.Y
ZP = A.ZP
SX, SY = 60.0, Y(A.SAEULE_Y0)


# ---------------------------------------------------------------- Gestell
def gestell():
    x0, x1, y0, y1 = A.RAHMEN
    for i, y in enumerate((y0, y1 - 40)):
        teil("01_Gestell", "Profil_40x80_L600", nutprofil(40, 80, x1 - x0, "x", (x0, y, 0)), "alu")
    for x in (x0, x1 - 40):
        teil("01_Gestell", "Profil_40x80_L480", nutprofil(40, 80, y1 - y0 - 80, "y", (x, y0 + 40, 0)), "alu")
    for x in (x0 + 25, x1 - 25):
        for y in (y0 + 25, y1 - 25):
            fuss = zyl("z", (x, y, 0), -8, 0, 18).fuse(zyl("z", (x, y, 0), 0, 12, 4))
            teil("01_Gestell", "Geraetefuss_D36_M8", fuss, "gummi")
    deck = kasten(x0, x1, y0, y1, 80, A.DECK)
    deck = bohren(deck, "z", (0, 0, 0), 80, A.DECK, 16)                          # Welle
    for dx, dy in ((-17, -17), (17, 17)):
        deck = bohren(deck, "z", (dx, dy, 0), 80, A.DECK, 6.6)                   # Flanschlager
    for x, y in ((SX - 20, SY + 20), (SX + 60, SY + 20)):
        deck = bohren(deck, "z", (x, y, 0), 80, A.DECK, 6.6)                     # Säulenfuß
    for x in (x0 + 20, x1 - 20):
        for y in (y0 + 20, 0, y1 - 20):
            deck = senkung(deck, x, y, A.DECK, 12.4, 6.6, 8)                    # auf Rahmen
    deck = bohren(deck, "z", (120, 0, 0), 80, A.DECK, 12)                        # Sensor Sternrad
    for x, y in ((-240, 240), (-200, 270)):
        deck = bohren(deck, "z", (x, y, 0), 80, A.DECK, 5.5)
    teil("01_Gestell", "A01_Deckplatte_EN-AW-5754_8mm", deck, "alu")
    gleit = zyl("z", (0, 0, 0), A.DECK, A.Z0, A.R_GLEIT)
    gleit = bohren(gleit, "z", (0, 0, 0), A.DECK, A.Z0, 40)
    for k in range(6):
        a = math.radians(30 + 60 * k)
        gleit = senkung(gleit, 210 * math.cos(a), 210 * math.sin(a), A.Z0, 8.4, 4.5, 6)
    gleit = bohren(gleit, "z", (120, 0, 0), A.DECK, A.Z0, 14)
    teil("01_Gestell", "A02_Gleitplatte_PE-UHMW_6mm", gleit, "pe")


# ---------------------------------------------------------------- Antrieb + Sternrad
def sternrad():
    g = "02_Sternrad"
    # NEMA17 unter der Deckplatte, Welle nach oben
    teil(g, "Schrittmotor_NEMA17_Sternrad", nema17((0, -90, 56), oben=True), "schwarz")
    teil(g, "Zahnriemenscheibe_GT2_20Z", zyl("z", (0, -90, 0), 56, 70, 7).cut(zyl("z", (0, -90, 0), 55, 71, 2.5)), "alu")
    teil(g, "Zahnriemenscheibe_GT2_100Z", zyl("z", (0, 0, 0), 56, 70, 32).cut(zyl("z", (0, 0, 0), 55, 71, 7.5)), "alu")
    riemen = cq.Workplane("XY").workplane(offset=60).polyline([(-32.5, 0), (32.5, 0), (7.5, -90), (-7.5, -90)]).close() \
        .extrude(6).val().cut(cq.Workplane("XY").workplane(offset=59).polyline(
            [(-30.5, 0), (30.5, 0), (5.5, -88), (-5.5, -88)]).close().extrude(8).val())
    teil(g, "Zahnriemen_GT2_6mm", riemen, "schwarz")
    halter = kasten(-30, 30, -125, -55, 74, 80)
    halter = bohren(halter, "z", (0, -90, 0), 74, 80, 23)
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5):
            halter = bohren(halter, "z", (dx, -90 + dy, 0), 74, 80, 3.4)
    teil(g, "Motorhalter_Stahl_6mm", halter, "stahl")
    lager = kasten(-26, 26, -12, 12, A.DECK, A.DECK + 11).fuse(zyl("z", (0, 0, 0), A.DECK, A.DECK + 26, 14))
    lager = lager.rotate(V(0, 0, 0), V(0, 0, 1), 45)
    lager = bohren(lager, "z", (0, 0, 0), A.DECK, A.DECK + 26, 15)
    teil(g, "Flanschlager_KFL002_d15", lager, "stahl_hell")
    teil(g, "Flanschlager_KFL002_d15_unten", lager.translate(V(0, 0, -A.DECK + 6)).rotate(V(0, 0, 6), V(1, 0, 0), 0), "stahl_hell")
    welle = zyl("z", (0, 0, 0), 20, A.Z0 + 150, 7.5)
    teil(g, "Welle_D15_h6_C45", welle, "stahl_hell")
    # Sternradscheiben
    for (za, zb), nr in zip(A.STERN_Z, ("unten", "oben")):
        teil(g, f"A03_Sternrad_{nr}_PE-HD_10mm", sternscheibe(A.Z0 + za, A.Z0 + zb), "pe_blau")
    nabe = zyl("z", (0, 0, 0), A.Z0 + 10, A.Z0 + 110, 22).cut(zyl("z", (0, 0, 0), A.Z0, A.Z0 + 120, 7.5))
    nabe = nabe.cut(kasten(-2.5, 2.5, 7.5 - 1, 7.5 + 3, A.Z0 + 10, A.Z0 + 110))       # Passfedernut
    teil(g, "Nabe_Stahl_D44", nabe, "stahl")
    for k in range(4):
        a = math.radians(45 + 90 * k)
        teil(g, "Distanzrohr_D12x70", zyl("z", (60 * math.cos(a), 60 * math.sin(a), 0), A.Z0 + 25, A.Z0 + 95, 6)
             .cut(zyl("z", (60 * math.cos(a), 60 * math.sin(a), 0), A.Z0 + 24, A.Z0 + 96, 3.2)), "stahl_hell")
    teil(g, "Referenzfahne_Schraube_M10", sechskant("z", (120, 0, 0), A.Z0 + 11, A.Z0 + 15, 16), "stahl")


def sternscheibe(z0, z1):
    R, RA, n = A.R_STERN, A.R_SCHEITEL, A.N_TASCHEN
    pts = []
    wp = None
    for k in range(n):
        a = math.radians(90 + k * 360 / n)
        apex = (RA * math.cos(a), RA * math.sin(a))
        w_minus = A.winkel_flanke(a, -1)
        w_plus = A.winkel_flanke(a, +1)
        if k == 0:                          # spätere Flankenanfänge = Ende des vorigen Bogens
            pts.append(("l", (R * math.cos(w_minus), R * math.sin(w_minus))))
        pts.append(("l", apex))
        pts.append(("l", (R * math.cos(w_plus), R * math.sin(w_plus))))
        a_next = math.radians(90 + (k + 1) * 360 / n)
        w_next = A.winkel_flanke(a_next, -1)
        wm = (w_plus + w_next) / 2 if w_next > w_plus else (w_plus + w_next + 2 * math.pi) / 2
        pts.append(("a", (R * math.cos(wm), R * math.sin(wm)), (R * math.cos(w_next), R * math.sin(w_next))))
    wp = cq.Workplane("XY").workplane(offset=z0).moveTo(*pts[0][1])
    for p in pts[1:]:
        if p[0] == "l":
            wp = wp.lineTo(*p[1])
        else:
            wp = wp.threePointArc(p[1], p[2])
    s = wp.close().extrude(z1 - z0).val()
    s = s.cut(zyl("z", (0, 0, 0), z0, z1, 7.6))
    for k in range(4):
        a = math.radians(45 + 90 * k)
        s = bohren(s, "z", (60 * math.cos(a), 60 * math.sin(a), 0), z0, z1, 6.4)
    for k in range(6):
        a = math.radians(k * 60)
        s = bohren(s, "z", (32 * math.cos(a), 32 * math.sin(a), 0), z0, z1, 5.5)
    return s


def nema17(pos, oben=True, gruppe=None):
    """NEMA17, Flansch bei pos (z), Welle nach oben (oben=True) oder unten."""
    x, y, z = pos
    k = cq.Workplane("XY").rect(42.3, 42.3).extrude(48).edges("|Z").chamfer(4).val()
    if oben:
        k = k.translate(V(x, y, z - 48))
        k = k.fuse(zyl("z", (x, y, 0), z, z + 2, 11))
        welle = zyl("z", (x, y, 0), z + 2, z + 24, 2.5).cut(kasten(x + 2, x + 3, y - 3, y + 3, z + 9, z + 25))
    else:
        k = k.translate(V(x, y, z))
        k = k.fuse(zyl("z", (x, y, 0), z - 2, z, 11))
        welle = zyl("z", (x, y, 0), z - 24, z - 2, 2.5).cut(kasten(x + 2, x + 3, y - 3, y + 3, z - 25, z - 9))
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5):
            k = k.cut(zyl("z", (x + dx, y + dy, 0), z - 6 if oben else z, z if oben else z + 6, 1.5))
    return k.fuse(welle)


def fuehrung():
    g = "02_Sternrad"
    z0, z1 = A.Z0 + 55, A.Z0 + 75
    band = cq.Workplane("XZ").center(203, (z0 + z1) / 2).rect(2, z1 - z0).revolve(300, (-203, 0, 0), (-203, 1, 0)).val()
    band = band.rotate(V(0, 0, 0), V(0, 0, 1), -60)
    teil(g, "Fuehrungsbogen_Federband_1.4310_2x20", band, "stahl_hell")
    for a in (-45, 0, 45, 135, 180, 225):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        teil(g, "Haltebolzen_D10", zyl("z", (222 * c, 222 * s, 0), A.DECK, z1, 5), "stahl")
        feder = zyl("x", (0, 0, 0), 0, 17, 4).rotate(V(0, 0, 0), V(0, 0, 1), a + 180).translate(
            V(222 * c, 222 * s, (z0 + z1) / 2))
        teil(g, "Druckfeder_D8_L17", feder, "feder")


# ---------------------------------------------------------------- Z-Achse
def z_achse():
    g = "03_Z-Achse"
    teil(g, "Profil_40x40_L432_Saeule", nutprofil(40, 40, 432, "z", (SX, SY, A.DECK)), "alu")
    fuss = kasten(SX - 30, SX + 70, SY, SY + 40, A.DECK, A.DECK + 6)
    for x in (SX - 20, SX + 60):
        fuss = bohren(fuss, "z", (x, SY + 20, 0), A.DECK, A.DECK + 6, 6.6)
    fuss = bohren(fuss, "z", (SX + 20, SY + 20, 0), A.DECK, A.DECK + 6, 8.5)
    teil(g, "Saeulenfuss_Stahl_6mm", fuss, "stahl")
    schiene = kasten(74, 86, Y(21), Y(29), 120, 515)
    for zz in range(130, 515, 25):
        schiene = schiene.cut(zyl("y", (80, 0, zz), Y(21), Y(29), 1.75))
        schiene = schiene.cut(zyl("y", (80, 0, zz), Y(21), Y(25.5), 3.0))
    teil(g, "Linearfuehrung_MGN12_L395", schiene, "stahl_hell")
    xs, ys = A.SPINDEL
    platte = kasten(SX - 5, xs + 25, SY, Y(ys + 25), 520, 528)
    platte = bohren(platte, "z", (xs, Y(ys), 0), 520, 528, 22.5)
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5):
            platte = bohren(platte, "z", (xs + dx, Y(ys) + dy, 0), 520, 528, 3.4)
    platte = bohren(platte, "z", (SX + 20, SY + 20, 0), 520, 528, 8.5)
    teil(g, "Motorplatte_Alu_8mm", platte, "alu")
    teil(g, "Schrittmotor_NEMA17_Z", nema17((xs, Y(ys), 528), oben=False), "schwarz")
    kupplung = zyl("z", (xs, Y(ys), 0), 500, 520, 10).cut(zyl("z", (xs, Y(ys), 0), 499, 521, 2.6))
    for zz in (504, 510, 516):
        kupplung = kupplung.cut(kasten(xs - 11, xs + 11, Y(ys) - 0.4, Y(ys) + 0.4, zz, zz + 1.2))
    teil(g, "Kupplung_5x8_D20", kupplung, "alu")
    teil(g, "Trapezgewindespindel_TR8x2_L340", zyl("z", (xs, Y(ys), 0), 160, 500, 4), "stahl_hell")
    bock = kasten(xs - 15, xs + 15, Y(ys - 12), Y(ys + 12), 150, 162).cut(zyl("z", (xs, Y(ys), 0), 150, 162, 11))
    teil(g, "Lagerbock_KFL08", bock, "stahl_hell")
    teil(g, "Lagerwinkel_Stahl", kasten(SX + 40, xs - 6, Y(ys - 8), Y(ys + 8), 150, 156), "stahl")
    teil(g, "Sensor_induktiv_M8_Z-Referenz", sensor("x", (0, Y(ys - 30), 505), 100, 8, 30), "sensor")


def sensor(achse, mitte, a0, d, laenge):
    """Zylindrischer Näherungsschalter mit zwei Muttern und Stecker."""
    k = zyl(achse, mitte, a0, a0 + laenge, d / 2)
    k = k.fuse(zyl(achse, mitte, a0 + laenge, a0 + laenge + 10, d / 2 * 0.8))
    for t in (0.3, 0.6):
        aa = a0 + laenge * t
        k = k.fuse(zyl(achse, mitte, aa, aa + d * 0.4, d * 0.9))
    return k


# ---------------------------------------------------------------- Öffnerkopf
def kopf():
    g = "04_Oeffnerkopf"
    z = ZP
    wagen = kasten(67, 93, Y(16), Y(29), z - 22, z + 22)
    wagen = wagen.cut(kasten(73.8, 86.2, Y(20.8), Y(29.1), z - 23, z + 23))
    teil(g, "Fuehrungswagen_MGN12H", wagen, "stahl_hell")
    kp = kasten(50, 110, Y(A.SP_Y0), Y(A.SP_Y1), z - 60, z + 50)
    kp = bohren(kp, "y", (80, 0, z), Y(A.SP_Y0), Y(A.SP_Y1), 6.8)                  # M8 Drehachse
    for dz in (-15, 15):
        for dx in (-10, 10):
            kp = bohren(kp, "y", (80 + dx, 0, z + dz + (-35 if dz < 0 else 0)), Y(A.SP_Y0), Y(A.SP_Y1), 3.4)
    for dz in (-55, -40):
        kp = bohren(kp, "y", (102, 0, z + dz + 5), Y(A.SP_Y0), Y(A.SP_Y1), 4.2)     # Aktorhalter M5
    teil(g, "A05_Kopfplatte_EN-AW-5754_10mm", kp, "alu_eloxiert")
    mh = kasten(110, 132, Y(A.SP_Y0), Y(52), z + 30, z + 40)
    mh = bohren(mh, "z", (A.SPINDEL[0], Y(A.SPINDEL[1]), 0), z + 30, z + 40, 10.5)
    teil(g, "A06_Mutternhalter_Alu_10mm", mh, "alu_eloxiert")
    mutter = zyl("z", (A.SPINDEL[0], Y(A.SPINDEL[1]), 0), z + 20, z + 30, 5.1).fuse(
        zyl("z", (A.SPINDEL[0], Y(A.SPINDEL[1]), 0), z + 30, z + 33.5, 11)).cut(
        zyl("z", (A.SPINDEL[0], Y(A.SPINDEL[1]), 0), z + 19, z + 34, 4))
    teil(g, "Spindelmutter_TR8x2_Messing", mutter, "messing")
    # Hebel mit Bohrungen
    hb = kasten(20, 245, Y(A.HY0), Y(A.HY1), z - 15, z + 15)
    hb = bohren(hb, "y", (A.PX, 0, z), Y(A.HY0), Y(A.HY1), 12)
    hb = bohren(hb, "y", (A.AKTOR_X, 0, z - 8), Y(A.HY0), Y(A.HY1), 8.2)
    for x in A.HAKEN_X if hasattr(A, "HAKEN_X") else (30, 42):
        sl = cq.Workplane("XY").workplane(offset=z - 16).center(x, Y(-3)).slot2D(8.5, 4.5).extrude(32).val()
        hb = hb.cut(sl)
    teil(g, "A11_Hebel_S235_30x12", hb, "alu_eloxiert", )
    hk = cq.Workplane("XZ").polyline([(13.4, z - 15), (48.4, z - 15), (48.4, z - 25), (19.17, z - 25)]).close() \
        .extrude(-42).val().translate(V(0, Y(-20), 0))
    for x in (30, 42):
        hk = bohren(hk, "z", (x, Y(-3), 0), z - 25, z - 15, 3.3)
    teil(g, "A12_Hakenleiste_C45_gehaertet", hk, "stahl")
    teil(g, "Passschraube_ISO7379_10x16_M8", zyl("y", (A.PX, 0, z), Y(A.HY0 - 11), Y(A.HY0 - 1), 8)
         .fuse(zyl("y", (A.PX, 0, z), Y(A.HY0 - 1), Y(A.SP_Y0), 5))
         .cut(sechskant("y", (A.PX, 0, z), Y(A.HY0 - 11.2), Y(A.HY0 - 6), 5)), "schwarz")
    for y0_, y1_ in ((A.HY0 - 1, A.HY0 + 5), (A.HY1 - 5, A.HY1 + 1)):
        bb = zyl("y", (A.PX, 0, z), Y(y0_), Y(y1_), 6).cut(zyl("y", (A.PX, 0, z), Y(y0_), Y(y1_), 5))
        bund = zyl("y", (A.PX, 0, z), Y(y0_ if y0_ < A.HY0 else y1_ - 1), Y((y0_ if y0_ < A.HY0 else y1_ - 1) + 1), 9) \
            .cut(zyl("y", (A.PX, 0, z), Y(y0_ - 1), Y(y1_ + 1), 5))
        teil(g, "Bundbuchse_iglidur_G_10x12x6", bb.fuse(bund), "gelb")
    # Stempelarm mit Magnetstempel
    arm = kasten(-14, 55, Y(5), Y(21), z + 4, z + 12).fuse(kasten(-14, 6, Y(-12), Y(21), z + 4, z + 12))
    arm = bohren(arm, "z", (0, YS, 0), z + 4, z + 12, 6.2)
    arm = bohren(arm, "z", (-20, Y(-4), 0), z + 4, z + 12, 4.5)
    teil(g, "A07_Stempelarm_S235_8mm", arm, "alu_eloxiert")
    buchse = zyl("z", (0, YS, 0), z - 3, z + 4, 10).cut(zyl("z", (0, YS, 0), z - 4, z + 5, 3.1))
    teil(g, "Fuehrungsbuchse_Messing_D20", buchse, "messing")
    teil(g, "Flachgreifer_Magnet_D16_M4", zyl("z", (0, YS, 0), z - 7, z - 2.5, 8), "stahl_hell")
    teil(g, "Stoessel_D6", zyl("z", (0, YS, 0), z - 2.5, z + 22, 3), "stahl_hell")
    teil(g, "Druckfeder_D11_L8", zyl("z", (0, YS, 0), z + 12, z + 20, 5.5).cut(zyl("z", (0, YS, 0), z + 11, z + 21, 4.5)), "feder")
    teil(g, "Sensor_induktiv_M8_Stempel", sensor("z", (0, YS, 0), z + 26, 8, 30), "sensor")
    teil(g, "Schaltfahne_Stahl", kasten(-8, 8, Y(-6), Y(6), z + 24, z + 26), "stahl")
    # Servo-Abstreifer
    servo = kasten(10, 30, Y(20), Y(60), z + 12, z + 48).fuse(kasten(10, 30, Y(14), Y(66), z + 38, z + 41))
    teil(g, "Servo_MG996R_6V", servo, "schwarz")
    teil(g, "Servowelle_D6", zyl("z", (20, Y(40), 0), z - 12, z + 12, 3), "stahl_hell")
    ab = kasten(-3, 3, Y(40), Y(110), z - 12, z - 8).fuse(zyl("z", (20 - 20, Y(40), 0), z - 12, z - 8, 0.01))
    ab = kasten(17, 23, Y(40), Y(110), z - 12, z - 8)
    teil(g, "A08_Abstreifer_1.4301_4mm", ab, "stahl_hell")
    # Trichter (Schale) + Halter + Gabellichtschranke
    tx, ty = -40.0, Y(-8)
    tr = cq.Workplane("XZ").polyline([(9, 0), (15, 26), (16.5, 26), (10.5, 0)]).close() \
        .revolve(360, (0, 0, 0), (0, 1, 0)).val().translate(V(tx, ty, z - 42))
    teil(g, "A09_Trichter_PETG", tr, "pe")
    teil(g, "A09_Trichterhalter_S235", kasten(-26, -14, Y(-12), Y(4), z - 22, z + 4), "alu_eloxiert")
    gabel = kasten(tx - 16, tx + 16, ty - 4, ty + 4, z - 36, z - 30).cut(kasten(tx - 12, tx + 12, ty - 5, ty + 5, z - 34.5, z - 31))
    teil(g, "Gabellichtschranke_30mm", gabel, "sensor")
    # Aktorhalter + Linearantrieb
    ah = kasten(94, 110, Y(A.SP_Y0 - 8), Y(A.SP_Y0), z - 160, z - 50).fuse(
        kasten(94, 245, Y(A.HY0 - 2), Y(A.SP_Y0), z - 160, z - 152))
    ah = bohren(ah, "y", (102, 0, z - 50 - 0), Y(A.SP_Y0 - 8), Y(A.SP_Y0), 5.5)
    ah = bohren(ah, "y", (102, 0, z - 35 - 20), Y(A.SP_Y0 - 8), Y(A.SP_Y0), 5.5)
    ah = bohren(ah, "z", (A.AKTOR_X, Y(-3), 0), z - 160, z - 152, 8.2)
    teil(g, "A10_Aktorhalter_S235_8mm", ah, "alu_eloxiert")
    akt = kasten(A.AKTOR_X - 14, A.AKTOR_X + 14, Y(-15), Y(9), z - 150, z - 45)
    akt = akt.fuse(zyl("y", (A.AKTOR_X, 0, z - 152), Y(-8), Y(2), 5))
    teil(g, "Linearantrieb_24V_Hub50_200N", akt, "schwarz")
    teil(g, "Kolbenstange_D10", zyl("z", (A.AKTOR_X, Y(-3), 0), z - 45, z - 15, 5), "stahl_hell")
    teil(g, "Gabelkopf_M8", kasten(A.AKTOR_X - 6, A.AKTOR_X + 6, Y(-12), Y(6), z - 20, z - 12), "stahl")


# ---------------------------------------------------------------- Abfuhr, Sensorik, Elektro
def abfuhr():
    g = "05_Kronkorken-Abfuhr"
    beh = kasten(-290, -185, 185, 292, A.DECK, A.DECK + 150).cut(kasten(-287, -188, 188, 289, A.DECK + 3, A.DECK + 151))
    teil(g, "A13_Sammelbehaelter_PP", beh, "pe")
    for x in (-280, -195):
        teil(g, "Einweglichtschranke_M18", sensor("y", (x, 0, A.DECK + 135), 160, 18, 20), "sensor")
    pts = [V(*p) for p in A.schlauch_pfad(ZP)]
    pfad = cq.Workplane("XY").spline([(p.x, p.y, p.z) for p in pts]).val()
    plane = cq.Plane(origin=pts[0], normal=(pts[1] - pts[0]).normalized())
    rohr = cq.Workplane(plane).circle(11).circle(9).sweep(cq.Workplane("XY").add(pfad)).val()
    teil(g, "Spiralschlauch_PVC_D22", rohr, "kabel")


def sensorik_elektro():
    g = "06_Sensorik"
    teil(g, "Reflexlichttaster_M18_Flasche", sensor("x", (0, 205, A.Z0 + 55), -65, 18, 40)
         .rotate(V(-65, 205, A.Z0 + 55), V(0, 0, 1), -48), "sensor")
    teil(g, "Sensorhalter", kasten(-75, -55, 195, 215, A.DECK, A.Z0 + 45), "stahl")
    teil(g, "Sensor_induktiv_M12_Sternrad", sensor("z", (120, 0, 0), A.Z0 - 30, 12, 32), "sensor")
    g = "09_Elektro"
    sk = kasten(140, 290, 228, 292, A.DECK, A.DECK + 200).cut(kasten(143, 287, 231, 289, A.DECK + 3, A.DECK + 197))
    teil(g, "Schaltkasten_Stahlblech_150x64x200", sk, "grau")
    teil(g, "Schaltkastentuer", kasten(150, 280, 226, 228, A.DECK + 10, A.DECK + 190), "grau")
    for x in (160, 180, 200):
        teil(g, "Kabelverschraubung_M16", zyl("z", (x, 260, 0), A.DECK + 200, A.DECK + 210, 6)
             .fuse(sechskant("z", (x, 260, 0), A.DECK + 200, A.DECK + 204, 19)), "schwarz")
    for i, (n, dx, dz, w, h) in enumerate((("Netzteil_24V_150W", 0, 10, 60, 100), ("ESP32_DevKit_mit_Traegerplatine", 70, 120, 60, 50),
                                           ("Sicherheitsrelais_2-kanalig", 70, 10, 22, 100), ("TMC2209_Treiber_x2", 100, 10, 40, 40),
                                           ("H-Bruecke_24V", 100, 60, 30, 30), ("Optokoppler_11-fach", 70, 175, 70, 20))):
        teil(g, n, kasten(146 + dx, 146 + dx + w, 270, 287, A.DECK + dz, A.DECK + dz + h), "gruen" if "ESP" in n or "TMC" in n or "Opto" in n else "grau")


def haube_bedienung():
    g = "07_Schutzhaube"
    x0, x1, y0, y1 = A.RAHMEN
    xa, xb, ya, yb = x0 + 5, x1 - 25, y0, y1 - 20
    H = A.HAUBE_Z
    for x in (xa, xb):
        for y in (ya, yb):
            teil(g, "Profil_20x20_Pfosten", nutprofil20(H - A.DECK, "z", (x, y, A.DECK)), "alu")
    for y in (ya, yb):
        teil(g, "Profil_20x20_Riegel_X", nutprofil20(xb - xa + 20, "x", (xa, y, H)), "alu")
    for x in (xa, xb):
        teil(g, "Profil_20x20_Riegel_Y", nutprofil20(yb - ya - 20, "y", (x, ya + 20, H)), "alu")
    teil(g, "Scheibe_PC_links_4mm", kasten(xa + 8, xa + 12, ya + 20, yb, A.DECK, H), "pc")
    teil(g, "Scheibe_PC_rechts_4mm", kasten(xb + 8, xb + 12, ya + 20, yb, A.DECK, H), "pc")
    teil(g, "Scheibe_PC_hinten_4mm", kasten(xa + 20, xb, yb + 8, yb + 12, A.DECK, H), "pc")
    teil(g, "Scheibe_PC_Dach_4mm", kasten(xa + 20, xb, ya + 20, yb, H + 16, H + 20), "pc")
    tuer = kasten(xa + 20, xb, ya - 4, ya, A.DECK + 4, H)
    tuer = tuer.fuse(kasten(-60, 60, ya - 15, ya - 4, A.DECK + 60, A.DECK + 75))
    teil(g, "Klappe_PC_4mm_mit_Griffleiste", tuer, "pc")
    for x in (-200, 200):
        teil(g, "Scharnier_Zn_20", zyl("x", (x, ya - 2, H + 5), -20, 20, 6).cut(zyl("x", (x, ya - 2, H + 5), -21, 21, 2)), "schwarz")
    ts = kasten(xb - 40, xb, ya - 12, ya, H - 50, H - 10)
    teil(g, "Sicherheitstuerschalter_EN-ISO-14119_Typ2", ts, "gelb")
    teil(g, "Betaetiger_Tuerschalter", kasten(xb - 34, xb - 6, ya - 18, ya - 12, H - 45, H - 15), "stahl")
    g = "08_Bedienung"
    px0, px1 = xb - 50, xb + 20
    teil(g, "Bediengehaeuse_ABS", kasten(px0, px1, ya - 40, ya, A.DECK + 140, A.DECK + 260)
         .cut(kasten(px0 + 3, px1 - 3, ya - 37, ya - 3, A.DECK + 143, A.DECK + 257)), "grau")
    for n, x, zz, f in (("Drucktaster_Start_gruen_D22", px0 + 18, A.DECK + 230, "gruen"),
                        ("Drucktaster_Stopp_rot_D22", px1 - 18, A.DECK + 230, "rot"),
                        ("Drucktaster_Reset_blau_D22", px0 + 18, A.DECK + 185, "blau")):
        teil(g, n, zyl("y", (x, 0, zz), ya - 46, ya - 40, 11).fuse(zyl("y", (x, 0, zz), ya - 40, ya, 14)), f)
    teil(g, "Not-Halt_Pilztaster_D40", cq.Workplane("XZ").polyline([(0, 0), (14, 0), (14, 6), (20, 9), (20, 15), (0, 15)]).close()
         .revolve(360, (0, 0, 0), (0, 1, 0)).val().rotate(V(0, 0, 0), V(1, 0, 0), 90)
         .translate(V(px1 - 18, ya - 43, A.DECK + 180)), "rot")
    teil(g, "Not-Halt_Schild_gelb", zyl("y", (px1 - 18, 0, A.DECK + 180), ya - 43, ya - 40, 18), "gelb")
    sx, sy = xa + 30, yb - 10
    teil(g, "Signalsaeule_Fuss", zyl("z", (sx, sy, 0), H + 20, H + 50, 6), "schwarz")
    for i, f in enumerate(("gruen", "gelb", "rot")):
        teil(g, f"Signalsaeule_Element_{f}", zyl("z", (sx, sy, 0), H + 50 + i * 26, H + 74 + i * 26, 17), f)
    teil(g, "Signalsaeule_Deckel", zyl("z", (sx, sy, 0), H + 128, H + 134, 17), "schwarz")


def nutprofil20(laenge, achse, ecke):
    s = nutprofil(40, 40, laenge, achse, (0, 0, 0))
    m = cq.Matrix()
    sc = {"z": (0.5, 0.5, 1), "x": (1, 0.5, 0.5), "y": (0.5, 1, 0.5)}[achse]
    s = s.transformGeometry(cq.Matrix([[sc[0], 0, 0, 0], [0, sc[1], 0, 0], [0, 0, sc[2], 0]]))
    return s.translate(V(*ecke))


# ---------------------------------------------------------------- Flaschen
def flaschen():
    g = "10_Flaschen_NRW_0.5l"
    fid, name, H, D, form = A.REF
    pr = M.flasche_profil(H, D, form)
    R = D / 2
    wp = cq.Workplane("XZ").moveTo(0, 0).lineTo(pr[0][0], 0).lineTo(*pr[1]).lineTo(*pr[2])
    wp = wp.spline([p for p in pr[3:13]], includeCurrent=True)
    for p in pr[13:]:
        wp = wp.lineTo(*p)
    glas = wp.lineTo(0, H).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    innen = cq.Workplane("XZ").polyline([(0, 3), (R - 4, 3), (R - 4, pr[2][1]), (11, H - 20), (9.5, H - 1), (0, H - 1)]) \
        .close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    glas = glas.cut(innen).translate(V(0, 0, A.Z0))
    etik = cq.Workplane("XZ").center(R + 0.15, 0.35 * H).rect(0.3, 0.2 * H).revolve(360, (-R - 0.15, 0, 0), (-R - 0.15, 1, 0)) \
        .val().translate(V(0, 0, A.Z0))
    z0, z1 = A.Z0 + H - 4.5, A.Z0 + H + 1.5
    stern_pts = [(r * math.cos(2 * math.pi * k / 42), r * math.sin(2 * math.pi * k / 42))
                 for k, r in enumerate([14.4 if k % 2 == 0 else 14.9 for k in range(42)])]
    kork = cq.Workplane("XY").workplane(offset=z0).polyline(stern_pts).close().extrude(z1 - z0 - 1).val()
    kork = kork.fuse(zyl("z", (0, 0, 0), z1 - 1, z1, 14.2)).cut(zyl("z", (0, 0, 0), z0 - 1, z1 - 1.2, 13.2))
    r = A.flaschen_r(D)
    for i in range(A.N_TASCHEN):
        a = 90 + i * 360 / A.N_TASCHEN
        loc = Location(V(r * math.cos(math.radians(a)), r * math.sin(math.radians(a)), 0))
        teil(g, "Flasche_NRW_0.5l_Glas", glas, "glas", loc)
        teil(g, "Flasche_NRW_0.5l_Etikett", etik, "etikett", loc)
        teil(g, "Kronkorken_26mm_DIN-EN-17177", kork, "kronkorken", loc)


# ================================================================
def main():
    schritte = [("Gestell", gestell), ("Sternrad", sternrad), ("Führungsbogen", fuehrung),
                ("Z-Achse", z_achse), ("Öffnerkopf", kopf), ("Abfuhr", abfuhr),
                ("Sensorik/Elektro", sensorik_elektro), ("Haube/Bedienung", haube_bedienung),
                ("Flaschen", flaschen)]
    for n, f in schritte:
        print(f"  baue {n} …", flush=True)
        f()
    for n in sorted(GRUPPEN):
        ASM.add(GRUPPEN[n], name=n)
    anzahl = sum(len(g.children) for g in GRUPPEN.values())
    print(f"  {len(GRUPPEN)} Unterbaugruppen, {anzahl} Teile – schreibe STEP …", flush=True)
    if hasattr(ASM, "export"):
        ASM.export(str(AUSGABE))
    else:
        ASM.save(str(AUSGABE))
    # Dateikopf: sprechender Modellname statt Standardtext (keine Personen- oder Pfadangaben)
    txt = AUSGABE.read_text(encoding="latin-1")
    txt = txt.replace("FILE_NAME('Open CASCADE Shape Model'", "FILE_NAME('TFO-A Flaschenoeffner Automatik'", 1)
    txt = txt.replace("FILE_DESCRIPTION(('Open CASCADE Model')",
                      "FILE_DESCRIPTION(('TFO-A Flaschenoeffner Automatik, Baugruppe')", 1)
    AUSGABE.write_text(txt, encoding="latin-1", newline="\n")
    print(f"{AUSGABE.name}: {AUSGABE.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
