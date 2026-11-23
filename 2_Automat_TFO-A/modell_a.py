"""
Geometriemodell des Flaschenöffner-Automaten TFO-A (Änderungsindex B) – einzige Quelle
für STEP, STL, Vorschau, Kollisionsprüfung und Dokumentation.

Bedienkonzept (Ausgabeautomat):
  - Befüllen und Entnehmen durch das Bedienfach vorn (Tasche bei 270°) mit verriegelter
    Klappe. Die Haube (Deckel) ist nur Servicezugang.
  - "Öffnen": nächste verschlossene Flasche zur Station (90°), Kopf tastet mit dem
    Stempel an, induktiver Sensor prüft auf Kronkorken, Linearantrieb hebelt ab,
    Elektro-Haftmagnet hält den Kronkorken, Kopf fährt in sichere Höhe, Servo klappt
    die Fangschale unter, Magnet lässt los, Kronkorken rutscht in den festen Trichter
    und über die Rutsche in die Schublade (seitlich, ohne Maschinenstopp zu leeren).
    Danach fährt die geöffnete Flasche ins Bedienfach.
  - "Laden": nächste leere Tasche ins Bedienfach.
  - Formatverstellung: Geländerring aus 3 Segmenten an Stellarmen mit Skala und Feder.

Koordinaten in mm: Z = 0 Tischoberfläche, Bediener bei -Y, Sternradmitte bei x = y = 0.
Jedes Teil trägt Gruppe, Name, Farbe und Bewegungsklasse (für Vorschau und Prüfung).
"""
import math
import sys
from dataclasses import dataclass, field
from pathlib import Path

import cadquery as cq
from cadquery import Color, Location, Vector

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent / "gemeinsam"))
import erzeuge_stl as M  # noqa: E402  (Flaschendaten und -profile)

V = Vector

# ================================================================ Hauptmaße
RAHMEN = (-300.0, 300.0, -260.0, 300.0)
DECK = 88.0                 # Oberkante Deckplatte
Z0 = 94.0                   # Standfläche der Flaschen
R_GLEIT = 230.0
N_TASCHEN = 8
R_SCHEITEL = 102.0          # Scheitel der 90°-Tasche
R_STERN = 175.0
STERN_Z = ((15, 25), (95, 105))
YS = 150.0                  # Station (90°): nominelle Flaschenmitte
PX = 80.0                   # Drehachse Hebel
HY0, HY1 = -9.0, 3.0        # Hebel relativ zu YS
SP_Y0, SP_Y1 = 6.0, 16.0    # Kopfplatte relativ zu YS
SAEULE_Y0 = 49.0            # Säule 20 mm nach hinten: dicke Flaschen laufen frei vorbei
SPINDEL = (118.0, 59.0)
AKTOR_X = 230.0
HAUBE_Z = 660.0
ZP_SICHER = 400.0           # Drehachse in sicherer Höhe (Takten, Abwurf)
Z_REFERENZ = 455.0
LIPPE_DZ = 2.0              # Hakenlippe 2 mm über der Drehachse
C_OFFSET = LIPPE_DZ + 1.5 + 6.0     # Kronkorken-Oberkante über der Drehachse (9,5)
SCHWENK = (-43.0, 150.0)    # senkrechte Schwenkachse des Stempelarms
SCHWENK_WINKEL = 90.0       # Schwenk zum Trichter (Gegenuhrzeigersinn)
TRICHTER_OK = 400.0         # Oberkante Kronkorken-Trichter
REF = M.FLASCHEN[0]                    # NRW 0,5 l
D_FORMAT = REF[3]                      # Geländer eingestellt auf diesen Durchmesser
FACH_X = (-65.0, 65.0)      # Öffnung Bedienfach
R_REF = 75.0                # Referenzfahne/-sensor Sternrad innerhalb der Flaschenbahn
SEGMENTE = ((285.0, 390.0), (30.0, 150.0), (150.0, 255.0))   # Geländer, vorn offen


def Y(y):
    return YS + y


def zp_arbeit(H):
    """Drehachse in Arbeitsstellung: Hakenoberkante 1,5 mm unter dem Kronkorkenrand."""
    return Z0 + H - 4.5 - 1.5 - LIPPE_DZ


ZP = zp_arbeit(REF[2])       # Modellstellung (346)


def flaschen_r(D):
    return R_SCHEITEL + D / 2 * math.sqrt(2)


def gelaender_r(D):
    """Innenradius des Geländers für Durchmesser D (0,5 mm Luft, Feder gleicht aus)."""
    return flaschen_r(D) + D / 2 + 0.5


# ================================================================ Grundformen
def kasten(x0, x1, y0, y1, z0, z1):
    return cq.Solid.makeBox(x1 - x0, y1 - y0, z1 - z0, V(x0, y0, z0))


def zyl(achse, mitte, a0, a1, r):
    d = {"x": V(1, 0, 0), "y": V(0, 1, 0), "z": V(0, 0, 1)}[achse]
    return cq.Solid.makeCylinder(r, a1 - a0, V(*mitte) + d * a0, d)


def bohren(teil, achse, mitte, a0, a1, d):
    return teil.cut(zyl(achse, mitte, a0 - 0.1, a1 + 0.1, d / 2))


def senkung(teil, x, y, z_oben, d_kopf, d_loch, dicke):
    h = (d_kopf - d_loch) / 2
    kegel = cq.Solid.makeCone(d_loch / 2, d_kopf / 2, h + 0.01, V(x, y, z_oben - h), V(0, 0, 1))
    return bohren(teil, "z", (x, y, 0), z_oben - dicke, z_oben, d_loch).cut(kegel)


def sechskant(achse, mitte, a0, a1, sw):
    s = cq.Workplane("XY").polygon(6, 2 * sw / math.sqrt(3)).extrude(a1 - a0).val().translate(V(0, 0, a0))
    if achse == "x":
        s = s.rotate(V(0, 0, 0), V(0, 1, 0), 90)
    elif achse == "y":
        s = s.rotate(V(0, 0, 0), V(1, 0, 0), -90)
    return s.translate(V(*mitte))


def nutprofil(breite, hoehe, laenge, achse, ecke):
    sk = cq.Sketch().rect(breite, hoehe)
    for i in range(int(breite // 40)):
        cx = -breite / 2 + 20 + 40 * i
        for sg in (1, -1):
            sk = sk.push([(cx, sg * (hoehe / 2 - 2.15))]).rect(8.2, 4.3, mode="s").reset()
            sk = sk.push([(cx, sg * (hoehe / 2 - 8.9))]).rect(14, 9.2, mode="s").reset()
    for j in range(int(hoehe // 40)):
        cy = -hoehe / 2 + 20 + 40 * j
        for sg in (1, -1):
            sk = sk.push([(sg * (breite / 2 - 2.15), cy)]).rect(4.3, 8.2, mode="s").reset()
            sk = sk.push([(sg * (breite / 2 - 8.9), cy)]).rect(9.2, 14, mode="s").reset()
    for i in range(int(breite // 40)):
        for j in range(int(hoehe // 40)):
            sk = sk.push([(-breite / 2 + 20 + 40 * i, -hoehe / 2 + 20 + 40 * j)]).circle(3.4, mode="s").reset()
    s = cq.Workplane("XY").placeSketch(sk).extrude(laenge).val().translate(V(breite / 2, hoehe / 2, 0))
    if achse == "x":
        s = s.rotate(V(0, 0, 0), V(0, 1, 0), 90).rotate(V(0, 0, 0), V(1, 0, 0), 90)
    elif achse == "y":
        s = s.rotate(V(0, 0, 0), V(1, 0, 0), -90)
    bb = s.BoundingBox()
    return s.translate(V(ecke[0] - bb.xmin, ecke[1] - bb.ymin, ecke[2] - bb.zmin))


def nutprofil20(laenge, achse, ecke):
    s = nutprofil(40, 40, laenge, achse, (0, 0, 0))
    sc = {"z": (0.5, 0.5, 1), "x": (1, 0.5, 0.5), "y": (0.5, 1, 0.5)}[achse]
    s = s.transformGeometry(cq.Matrix([[sc[0], 0, 0, 0], [0, sc[1], 0, 0], [0, 0, sc[2], 0]]))
    return s.translate(V(*ecke))


def revolve_profil(pts, mitte=(0, 0, 0)):
    wp = cq.Workplane("XZ").polyline([(0, pts[0][1])] + list(pts) + [(0, pts[-1][1])]).close()
    return wp.revolve(360, (0, 0, 0), (0, 1, 0)).val().translate(V(*mitte))


def bogenband(r_innen, dicke, z0, z1, w0, w1):
    """Ringsegment (Geländerband) von Winkel w0 bis w1 (Grad)."""
    s = cq.Workplane("XZ").center(r_innen + dicke / 2, (z0 + z1) / 2).rect(dicke, z1 - z0) \
        .revolve(w1 - w0, (-(r_innen + dicke / 2), 0, 0), (-(r_innen + dicke / 2), 1, 0)).val()
    return s.rotate(V(0, 0, 0), V(0, 0, 1), w0)


def polarpunkt(r, w, z=0.0):
    return (r * math.cos(math.radians(w)), r * math.sin(math.radians(w)), z)


def sensor_zyl(achse, mitte, a0, d, laenge, muttern=True):
    k = zyl(achse, mitte, a0, a0 + laenge, d / 2)
    k = k.fuse(zyl(achse, mitte, a0 + laenge, a0 + laenge + 10, d / 2 * 0.8))
    for t in ((0.3, 0.6) if muttern else ()):
        aa = a0 + laenge * t
        k = k.fuse(zyl(achse, mitte, aa, aa + d * 0.4, d * 0.9))
    return k


def nema17(pos, oben=True):
    x, y, z = pos
    k = cq.Workplane("XY").rect(42.3, 42.3).extrude(48).edges("|Z").chamfer(4).val()
    if oben:
        k = k.translate(V(x, y, z - 48)).fuse(zyl("z", (x, y, 0), z, z + 2, 11))
        welle = zyl("z", (x, y, 0), z + 2, z + 24, 2.5).cut(kasten(x + 2, x + 3, y - 3, y + 3, z + 9, z + 25))
    else:
        k = k.translate(V(x, y, z)).fuse(zyl("z", (x, y, 0), z - 2, z, 11))
        welle = zyl("z", (x, y, 0), z - 24, z - 2, 2.5).cut(kasten(x + 2, x + 3, y - 3, y + 3, z - 25, z - 9))
    for dx in (-15.5, 15.5):
        for dy in (-15.5, 15.5):
            k = k.cut(zyl("z", (x + dx, y + dy, 0), z - 6 if oben else z, z if oben else z + 6, 1.5))
    return k.fuse(welle)


# ================================================================ Teileliste
FARBEN = {
    "alu": (0.78, 0.80, 0.84, 1), "alu_eloxiert": (0.25, 0.53, 0.84, 1), "stahl": (0.42, 0.44, 0.48, 1),
    "stahl_hell": (0.66, 0.68, 0.70, 1), "schwarz": (0.12, 0.12, 0.14, 1), "pe": (0.93, 0.93, 0.90, 1),
    "pe_blau": (0.30, 0.55, 0.85, 1), "gummi": (0.10, 0.10, 0.11, 1), "messing": (0.80, 0.65, 0.25, 1),
    "sensor": (0.15, 0.55, 0.75, 1), "rot": (0.80, 0.12, 0.14, 1), "gruen": (0.15, 0.65, 0.30, 1),
    "gelb": (0.95, 0.75, 0.10, 1), "blau": (0.15, 0.40, 0.80, 1), "grau": (0.55, 0.57, 0.60, 1),
    "weiss": (0.95, 0.95, 0.95, 1), "pc": (0.70, 0.85, 0.95, 0.25), "feder": (0.70, 0.72, 0.75, 1),
    "led": (0.95, 0.95, 0.70, 1),
}


@dataclass
class Teil:
    gruppe: str
    name: str
    form: object
    farbe: str
    klasse: str = ""          # "" fest | st Sternrad | z Kopf | h Hebel | r Kolbenstange | s Schwenkarm
    nr: str = ""              # | k Bedienklappe | d Servicedeckel
    loc: object = None


TEILE: list = []


def teil(gruppe, name, form, farbe, klasse="", nr=""):
    n = sum(1 for t in TEILE if t.name == name or t.name.startswith(name + "_"))
    TEILE.append(Teil(gruppe, name if n == 0 else f"{name}_{n + 1}", form, farbe, klasse, nr))


SX, SY = 60.0, Y(SAEULE_Y0)


# ---------------------------------------------------------------- 01 Gestell
def gestell():
    g = "01_Gestell"
    x0, x1, y0, y1 = RAHMEN
    for y in (y0, y1 - 40):
        teil(g, "Profil_40x80_L600", nutprofil(40, 80, x1 - x0, "x", (x0, y, 0)), "alu")
    for x in (x0, x1 - 40):
        teil(g, "Profil_40x80_L480", nutprofil(40, 80, y1 - y0 - 80, "y", (x, y0 + 40, 0)), "alu")
    for x in (x0 + 25, x1 - 25):
        for y in (y0 + 25, y1 - 25):
            teil(g, "Geraetefuss_D36_M8", zyl("z", (x, y, 0), -8, 0, 18).fuse(zyl("z", (x, y, 0), 0, 12, 4)), "gummi")
    deck = kasten(x0, x1, y0, y1, 80, DECK)
    deck = bohren(deck, "z", (0, 0, 0), 80, DECK, 16)
    for x, y in ((SX - 20, SY + 20), (SX + 60, SY + 20)):
        deck = bohren(deck, "z", (x, y, 0), 80, DECK, 6.6)
    for x in (x0 + 20, x1 - 20):
        for y in (y0 + 20, 0, y1 - 20):
            deck = senkung(deck, x, y, DECK, 12.4, 6.6, 8)
    deck = bohren(deck, "z", (R_REF, 0, 0), 80, DECK, 12.5)
    teil(g, "A01_Deckplatte_EN-AW-5754_8mm", deck, "alu", nr="A01")
    gleit = zyl("z", (0, 0, 0), DECK, Z0, R_GLEIT).cut(zyl("z", (0, 0, 0), DECK - 1, Z0 + 1, 20))
    gleit = gleit.cut(kasten(-50, 50, -215, -105, DECK - 1, Z0 + 1))           # Aussparung Tropfgitter
    gleit = bohren(gleit, "z", (R_REF, 0, 0), DECK, Z0, 14)
    for k in range(6):
        x, y, _ = polarpunkt(212, 30 + 60 * k)
        gleit = senkung(gleit, x, y, Z0, 8.4, 4.5, 6)
    teil(g, "A02_Gleitplatte_PE-UHMW_6mm", gleit, "pe", nr="A02")
    schale = kasten(-48, 48, -213, -107, DECK, DECK + 4).cut(kasten(-46, 46, -211, -109, DECK + 1.5, DECK + 5))
    teil(g, "A14_Tropfschale_PP", schale, "weiss", nr="A14")
    gitter = kasten(-47, 47, -212, -108, DECK + 4, Z0)
    for x in range(-40, 41, 8):
        gitter = gitter.cut(kasten(x - 2, x + 2, -205, -115, DECK + 3, Z0 + 1))
    teil(g, "A15_Tropfgitter_PE", gitter, "pe", nr="A15")


# ---------------------------------------------------------------- 02 Sternrad
def sternscheibe(z0, z1):
    R, RA, n = R_STERN, R_SCHEITEL, N_TASCHEN

    def w_flanke(a, s):
        ax, ay = RA * math.cos(a), RA * math.sin(a)
        d = a + s * math.radians(45)
        dx, dy = math.cos(d), math.sin(d)
        b = ax * dx + ay * dy
        t = -b + math.sqrt(b * b - (RA ** 2 - R ** 2))
        return math.atan2(ay + t * dy, ax + t * dx)

    pts = []
    for k in range(n):
        a = math.radians(90 + k * 360 / n)
        if k == 0:
            w = w_flanke(a, -1)
            pts.append(("l", (R * math.cos(w), R * math.sin(w))))
        pts.append(("l", (RA * math.cos(a), RA * math.sin(a))))
        wp_ = w_flanke(a, +1)
        pts.append(("l", (R * math.cos(wp_), R * math.sin(wp_))))
        wn = w_flanke(math.radians(90 + (k + 1) * 360 / n), -1)
        wm = (wp_ + wn) / 2 if wn > wp_ else (wp_ + wn + 2 * math.pi) / 2
        pts.append(("a", (R * math.cos(wm), R * math.sin(wm)), (R * math.cos(wn), R * math.sin(wn))))
    wp = cq.Workplane("XY").workplane(offset=z0).moveTo(*pts[0][1])
    for p in pts[1:]:
        wp = wp.lineTo(*p[1]) if p[0] == "l" else wp.threePointArc(p[1], p[2])
    s = wp.close().extrude(z1 - z0).val().cut(zyl("z", (0, 0, 0), z0, z1, 7.6))
    for k in range(4):
        x, y, _ = polarpunkt(60, 45 + 90 * k)
        s = bohren(s, "z", (x, y, 0), z0, z1, 6.4)
    for k in range(6):
        x, y, _ = polarpunkt(32, 60 * k)
        s = bohren(s, "z", (x, y, 0), z0, z1, 5.5)
    return s


def sternrad():
    g = "02_Sternrad"
    teil(g, "Schrittmotor_NEMA17_Sternrad_M2", nema17((0, -90, 56), oben=True), "schwarz")
    teil(g, "Zahnriemenscheibe_GT2_20Z", zyl("z", (0, -90, 0), 56, 70, 7).cut(zyl("z", (0, -90, 0), 55, 71, 2.5)), "alu")
    teil(g, "Zahnriemenscheibe_GT2_100Z", zyl("z", (0, 0, 0), 56, 70, 32).cut(zyl("z", (0, 0, 0), 55, 71, 7.5)), "alu", "st")
    riemen = cq.Workplane("XY").workplane(offset=60).polyline([(-32.5, 0), (32.5, 0), (7.5, -90), (-7.5, -90)]).close() \
        .extrude(6).val().cut(cq.Workplane("XY").workplane(offset=59).polyline(
            [(-30.5, 0), (30.5, 0), (5.5, -88), (-5.5, -88)]).close().extrude(8).val())
    teil(g, "Zahnriemen_GT2_6mm", riemen, "schwarz")
    halter = kasten(-30, 30, -125, -55, 74, 80).cut(zyl("z", (0, -90, 0), 73, 81, 11.5))
    teil(g, "Motorhalter_Stahl_6mm", halter, "stahl")
    lager = kasten(-26, 26, -12, 12, DECK, DECK + 11).fuse(zyl("z", (0, 0, 0), DECK, DECK + 26, 14)) \
        .rotate(V(0, 0, 0), V(0, 0, 1), 45).cut(zyl("z", (0, 0, 0), DECK - 1, DECK + 27, 7.5))
    teil(g, "Flanschlager_KFL002_d15", lager, "stahl_hell")
    teil(g, "Welle_D15_h6_C45", zyl("z", (0, 0, 0), 20, Z0 + 150, 7.5), "stahl_hell", "st")
    for (za, zb), nr in zip(STERN_Z, ("unten", "oben")):
        teil(g, f"A03_Sternrad_{nr}_PE-HD_10mm", sternscheibe(Z0 + za, Z0 + zb), "pe_blau", "st", "A03")
    nabe = zyl("z", (0, 0, 0), Z0 + 10, Z0 + 110, 22).cut(zyl("z", (0, 0, 0), Z0, Z0 + 120, 7.5))
    teil(g, "Nabe_Stahl_D44", nabe, "stahl", "st")
    for k in range(4):
        x, y, _ = polarpunkt(60, 45 + 90 * k)
        teil(g, "Distanzrohr_D12x70", zyl("z", (x, y, 0), Z0 + 25, Z0 + 95, 6)
             .cut(zyl("z", (x, y, 0), Z0 + 24, Z0 + 96, 3.2)), "stahl_hell", "st")
    teil(g, "Referenzfahne_M10", sechskant("z", (R_REF, 0, 0), Z0 + 11, Z0 + 15, 16), "stahl", "st")


# ---------------------------------------------------------------- 03 Geländer (Format)
def gelaender():
    g = "03_Gelaender"
    r = gelaender_r(D_FORMAT)
    z0, z1 = Z0 + 55, Z0 + 75
    for i, (w0, w1) in enumerate(SEGMENTE, 1):
        band = bogenband(r, 2, z0, z1, w0, w1)
        # Einlaufschrägen an den Enden zum Bedienfach (10° nach außen)
        teil(g, f"A16_Gelaenderband_{i}_1.4310_2x20", band, "stahl_hell", nr="A16")
        wm = (w0 + w1) / 2
        rot = lambda s: s.rotate(V(0, 0, 0), V(0, 0, 1), wm)
        sockel = kasten(r + 30, r + 66, -12, 12, DECK, DECK + 12).cut(kasten(r + 36, r + 60, -3.3, 3.3, DECK - 1, DECK + 13))
        teil(g, f"A17_Stellarm_Sockel_{i}", rot(sockel), "alu_eloxiert", nr="A17")
        schieber = kasten(r + 2, r + 14, -8, 8, DECK + 12, z1).fuse(kasten(r + 2, r + 50, -8, 8, DECK + 12, DECK + 20))
        teil(g, f"A18_Stellarm_Schieber_{i}", rot(schieber), "alu_eloxiert", nr="A18")
        teil(g, f"Klemmhebel_M6_{i}", rot(zyl("z", (r + 44, 0, 0), DECK + 20, DECK + 32, 9)
                                         .fuse(kasten(r + 44, r + 70, -4, 4, DECK + 28, DECK + 32))), "schwarz")
        teil(g, f"Skala_Formatring_{i}", rot(kasten(r + 30, r + 66, 12, 13, DECK + 2, DECK + 12)), "gelb")
        teil(g, f"Druckfeder_Gelaender_{i}", rot(zyl("x", (0, 0, (z0 + z1) / 2), r + 2, r + 2.01, 1)
                                                .fuse(zyl("x", (0, 6, (z0 + z1) / 2), r + 14, r + 22, 4))), "feder")


# ---------------------------------------------------------------- 04 Z-Achse
def z_achse():
    g = "04_Z-Achse"
    teil(g, "Profil_40x40_L432_Saeule", nutprofil(40, 40, 432, "z", (SX, SY, DECK)), "alu")
    fuss = kasten(SX - 30, SX + 70, SY, SY + 40, DECK, DECK + 6)
    for x in (SX - 20, SX + 60):
        fuss = bohren(fuss, "z", (x, SY + 20, 0), DECK, DECK + 6, 6.6)
    teil(g, "Saeulenfuss_Stahl_6mm", fuss, "stahl")
    schiene = kasten(74, 86, SY - 8, SY, 120, 515)
    for zz in range(130, 515, 25):
        schiene = schiene.cut(zyl("y", (80, 0, zz), SY - 8, SY, 1.75))
    teil(g, "Linearfuehrung_MGN12_L395", schiene, "stahl_hell")
    xs, ys = SPINDEL
    platte = kasten(SX - 5, xs + 25, SY, Y(ys + 25), 520, 528).cut(zyl("z", (xs, Y(ys), 0), 519, 529, 11.25))
    teil(g, "Motorplatte_Alu_8mm", platte, "alu")
    teil(g, "Schrittmotor_NEMA17_Z_M1", nema17((xs, Y(ys), 528), oben=False), "schwarz")
    teil(g, "Kupplung_5x8_D20", zyl("z", (xs, Y(ys), 0), 500, 520, 10).cut(zyl("z", (xs, Y(ys), 0), 499, 521, 2.6)), "alu")
    teil(g, "Trapezgewindespindel_TR8x2_L340", zyl("z", (xs, Y(ys), 0), 160, 500, 4), "stahl_hell")
    teil(g, "Lagerbock_KFL08", kasten(xs - 15, xs + 15, Y(ys - 12), Y(ys + 12), 150, 162)
         .cut(zyl("z", (xs, Y(ys), 0), 149, 163, 11)), "stahl_hell")
    teil(g, "Lagerwinkel_Stahl", kasten(SX + 40, xs - 6, Y(ys - 8), Y(ys + 8), 150, 156), "stahl")
    teil(g, "Sensor_induktiv_M8_Z-Referenz_B2", sensor_zyl("x", (0, SY + 30, Z_REFERENZ + 50), 100, 8, 30), "sensor")


# ---------------------------------------------------------------- 05 Öffnerkopf
def kopf():
    g = "05_Oeffnerkopf"
    z = ZP
    c = z + C_OFFSET                     # Oberkante Kronkorken in Arbeitsstellung
    k = "z"
    teil(g, "Fuehrungswagen_MGN12H", kasten(67, 93, SY - 21, SY - 8, z - 22, z + 22)
         .cut(kasten(73.8, 86.2, SY - 16.2, SY - 7.9, z - 23, z + 23)), "stahl_hell", k)
    teil(g, "A25_Distanzplatte_Alu_20mm", kasten(62, 98, Y(SP_Y1), SY - 21, z - 30, z + 30), "alu_eloxiert", k, "A25")
    kp = kasten(50, 110, Y(SP_Y0), Y(SP_Y1), z - 60, z + 50)
    kp = bohren(kp, "y", (PX, 0, z), Y(SP_Y0), Y(SP_Y1), 6.8)
    teil(g, "A05_Kopfplatte_EN-AW-5754_10mm", kp, "alu_eloxiert", k, "A05")
    xs, ys = SPINDEL
    mh = kasten(110, 132, Y(SP_Y0), Y(ys + 13), z + 30, z + 40).cut(zyl("z", (xs, Y(ys), 0), z + 29, z + 41, 5.25))
    teil(g, "A06_Mutternhalter_Alu_10mm", mh, "alu_eloxiert", k, "A06")
    teil(g, "Spindelmutter_TR8x2_Messing", zyl("z", (xs, Y(ys), 0), z + 20, z + 30, 5.1)
         .fuse(zyl("z", (xs, Y(ys), 0), z + 30, z + 33.5, 11)).cut(zyl("z", (xs, Y(ys), 0), z + 19, z + 34, 4)), "messing", k)
    # Hebel mit Hakenleiste: Lippe 2 mm ÜBER der Drehachse -> beim Anheben keine Bewegung zum Glas hin
    hb = kasten(30, 245, Y(HY0), Y(HY1), z - 15, z + 15)
    hb = bohren(hb, "y", (PX, 0, z), Y(HY0), Y(HY1), 12)
    hb = bohren(hb, "y", (AKTOR_X, 0, z + 8), Y(HY0), Y(HY1), 8.2)
    for zz in (z - 9, z - 1):
        hb = bohren(hb, "x", (0, Y(-3), zz), 30, 45, 5.5)
    teil(g, "A11_Hebel_S235_30x12", hb, "alu_eloxiert", "h", "A11")
    lippe = z + LIPPE_DZ
    f = 15 * math.tan(math.radians(30))
    hk = cq.Workplane("XZ").polyline([(13.4, lippe), (30, lippe), (30, lippe - 15), (13.4 + f, lippe - 15)]).close() \
        .extrude(-42).val().translate(V(0, Y(-20), 0))
    for zz in (z - 9, z - 1):
        hk = bohren(hk, "x", (0, Y(-3), zz), 20, 30, 4.2)
    teil(g, "A12_Hakenleiste_C45_gehaertet", hk, "stahl", "h", "A12")
    teil(g, "Passschraube_ISO7379_10x16_M8", zyl("y", (PX, 0, z), Y(HY0 - 11), Y(HY0 - 1), 8)
         .fuse(zyl("y", (PX, 0, z), Y(HY0 - 1), Y(SP_Y0), 5)), "schwarz", "h")
    for y0_, y1_, yb in ((HY0 - 1, HY0 + 5, HY0 - 1), (HY1 - 5, HY1 + 1, HY1)):
        bb = zyl("y", (PX, 0, z), Y(y0_), Y(y1_), 6).fuse(zyl("y", (PX, 0, z), Y(yb), Y(yb + 1), 9)) \
            .cut(zyl("y", (PX, 0, z), Y(y0_ - 1), Y(y1_ + 1), 5))
        teil(g, "Bundbuchse_iglidur_G_10x12x6", bb, "gelb", "h")
    # Linearantrieb über dem Hebelende (drückt nach unten), Bügel oberhalb der Flaschen
    buegel = kasten(104, 250, Y(HY0), Y(HY1), z + 143, z + 151)
    buegel = buegel.fuse(kasten(94, 110, Y(SP_Y0 - 8), Y(SP_Y0), z + 28, z + 151))
    buegel = bohren(buegel, "z", (AKTOR_X, Y(-3), 0), z + 143, z + 151, 8.2)
    teil(g, "A10_Aktorbuegel_S235_8mm", buegel, "alu_eloxiert", k, "A10")
    teil(g, "Linearantrieb_24V_Hub50_200N_M3", kasten(AKTOR_X - 12, AKTOR_X + 12, Y(-15), Y(9), z + 30, z + 135)
         .fuse(zyl("y", (AKTOR_X, 0, z + 140), Y(-8), Y(2), 5)), "schwarz", k)
    teil(g, "Kolbenstange_D10", zyl("z", (AKTOR_X, Y(-3), 0), z + 15, z + 30, 5), "stahl_hell", "r")
    teil(g, "Sensor_induktiv_M8_Hebel_B10", sensor_zyl("z", (200, Y(-3), 0), z - 52, 8, 26, muttern=False), "sensor", k)
    teil(g, "Sensorwinkel_Hebel", kasten(196, 204, Y(SP_Y0 - 3), Y(SP_Y0), z - 52, z - 22)
         .fuse(kasten(196, 204, Y(-7), Y(SP_Y0), z - 56, z - 52)), "stahl", k)
    # Träger für den Schwenkarm (über Hebel und Haken)
    px, py = SCHWENK
    traeger = kasten(px - 12, -31, py - 30, py + 10, c + 38, c + 46)
    traeger = traeger.fuse(kasten(-31, 50, py - 24, py - 14, c + 38, c + 46))
    traeger = traeger.fuse(kasten(44, 50, py - 24, Y(SP_Y0), c + 38, c + 46))
    traeger = traeger.fuse(kasten(44, 50, Y(SP_Y0) - 6, Y(SP_Y0), z + 15, c + 46))
    traeger = bohren(traeger, "z", (px, py, 0), c + 38, c + 46, 6.2)
    teil(g, "A20_Schwenkarmtraeger_S235", traeger, "alu_eloxiert", k, "A20")
    teil(g, "Servo_MG996R_6V_M4", kasten(px - 10, px + 10, py - 30, py + 10, c + 46, c + 84), "schwarz", k)
    teil(g, "Schwenkwelle_D6", zyl("z", (px, py, 0), c + 23.5, c + 46, 3), "stahl_hell", "s")
    # Schwenkarm mit gefedertem Stempel (Klasse s, schwenkt um senkrechte Achse bei SCHWENK)
    arm = kasten(px, 16, py - 8, py + 8, c + 15.5, c + 23.5).fuse(zyl("z", (px, py, 0), c + 15.5, c + 23.5, 10))
    arm = bohren(arm, "z", (-3, py, 0), c + 15.5, c + 23.5, 8.2)
    arm = bohren(arm, "z", (-11, py, 0), c + 15.5, c + 23.5, 8.5)
    arm = bohren(arm, "z", (3, py, 0), c + 15.5, c + 23.5, 6.5)
    teil(g, "A07_Schwenkarm_S235_8mm", arm, "alu_eloxiert", "s", "A07")
    platte = zyl("z", (-3, py, 0), c + 0.5, c + 4.5, 14)
    platte = platte.cut(zyl("z", (3, py, 0), c, c + 5, 8.05)).cut(zyl("z", (-11, py, 0), c, c + 5, 4.05))
    teil(g, "A19_Stempelplatte_POM_D28", platte, "weiss", "s", "A19")
    teil(g, "Elektro-Haftmagnet_D16_24V_Y2", zyl("z", (3, py, 0), c + 0.5, c + 13.5, 8), "stahl_hell", "s")
    teil(g, "Sensor_induktiv_M8_Kronkorken_B8", sensor_zyl("z", (-11, py, 0), c + 0.5, 8, 26, muttern=False), "sensor", "s")
    teil(g, "Fuehrungsstange_D8", zyl("z", (-3, py, 0), c + 4.5, c + 39.5, 4), "stahl_hell", "s")
    teil(g, "Druckfeder_Stempel", zyl("z", (-3, py, 0), c + 4.5, c + 15.5, 6).cut(zyl("z", (-3, py, 0), c + 4, c + 16, 5)), "feder", "s")
    teil(g, "Schaltfahne_Stempel", kasten(-8, 14, py - 6, py + 6, c + 39.5, c + 41.5), "stahl", "s")
    teil(g, "Sensor_induktiv_M8_Stempelkontakt_B3", sensor_zyl("z", (8, py, 0), c + 45.5, 8, 26), "sensor", "s")
    teil(g, "Sensorwinkel_Stempel", kasten(0, 16, py - 8, py + 8, c + 43.5, c + 45.5)
         .fuse(kasten(14, 16, py - 8, py + 8, c + 23.5, c + 45.5)), "stahl", "s")


# ---------------------------------------------------------------- 06 Kronkorken-Abfuhr
FACH_KK = (-295.0, -170.0, 180.0, 295.0)               # Kronkorkenfach (x0, x1, y0, y1)


def trichter_lage():
    """Lage des Kronkorkens nach dem Schwenken (sichere Höhe) -> Trichtermitte."""
    px, py = SCHWENK
    a = math.radians(SCHWENK_WINKEL)
    mx, my = 0 - px, 0.0                     # Kronkorkenmitte (x = 0) relativ zur Schwenkachse
    return px + mx * math.cos(a) - my * math.sin(a), py + mx * math.sin(a) + my * math.cos(a)


def rinne(p0, p1, breite=40.0, hoehe=22.0, wand=1.5):
    """U-förmige Rutsche von p0 nach p1 (Mittellinie Boden)."""
    import numpy as np
    a, b = np.array(p0, float), np.array(p1, float)
    L = float(np.linalg.norm(b - a))
    u = cq.Workplane("XY").rect(L, breite).extrude(wand).val().translate(V(L / 2, 0, 0))
    for sg in (1, -1):
        u = u.fuse(kasten(0, L, sg * breite / 2 - (wand if sg > 0 else 0), sg * breite / 2 + (0 if sg > 0 else wand), 0, hoehe))
    d = (b - a) / L
    neig = math.degrees(math.atan2(d[2], math.hypot(d[0], d[1])))
    rich = math.degrees(math.atan2(d[1], d[0]))
    return u.rotate(V(0, 0, 0), V(0, 1, 0), -neig).rotate(V(0, 0, 0), V(0, 0, 1), rich).translate(V(*a))


def rinnen_punkte():
    tx, ty = trichter_lage()
    return (tx, ty, TRICHTER_OK - 32), (-182.0, 236.0, 300.0)


def abfuhr():
    g = "06_Kronkorken-Abfuhr"
    tx, ty = trichter_lage()
    zt, h = TRICHTER_OK, 30.0
    oben = [V(tx - 20, ty - 20, zt), V(tx + 20, ty - 20, zt), V(tx + 20, ty + 20, zt), V(tx - 20, ty + 20, zt)]
    unten = [V(tx - 12, ty - 12, zt - h), V(tx + 12, ty - 12, zt - h), V(tx + 12, ty + 12, zt - h), V(tx - 12, ty + 12, zt - h)]
    aussen = cq.Solid.makeLoft([cq.Wire.makePolygon(oben, close=True), cq.Wire.makePolygon(unten, close=True)], True)
    o2 = [V(p.x + (1.5 if p.x < tx else -1.5), p.y + (1.5 if p.y < ty else -1.5), zt + 0.1) for p in oben]
    u2 = [V(p.x + (1.5 if p.x < tx else -1.5), p.y + (1.5 if p.y < ty else -1.5), zt - h - 0.1) for p in unten]
    innen = cq.Solid.makeLoft([cq.Wire.makePolygon(o2, close=True), cq.Wire.makePolygon(u2, close=True)], True)
    teil(g, "A22_Trichter_PETG", aussen.cut(innen), "pe", nr="A22")
    p0, p1 = rinnen_punkte()
    teil(g, "A23_Rutsche_1.4301_1.5mm", rinne(p0, p1), "stahl_hell", nr="A23")
    teil(g, "Trichterhalter_Stahl", kasten(tx - 24, tx - 20, ty - 20, ty + 60, zt - 34, zt - 2)
         .fuse(kasten(tx - 24, tx - 20, ty + 56, ty + 60, DECK + 255, zt - 2)), "stahl")
    t = 0.5
    gx, gy, gz = [p0[i] + (p1[i] - p0[i]) * t for i in range(3)]
    gabel = kasten(gx - 4, gx + 4, gy - 28, gy + 28, gz - 10, gz - 6)
    gabel = gabel.fuse(kasten(gx - 4, gx + 4, gy - 28, gy - 23, gz - 6, gz + 28))
    gabel = gabel.fuse(kasten(gx - 4, gx + 4, gy + 23, gy + 28, gz - 6, gz + 28))
    teil(g, "Gabellichtschranke_B11", gabel, "sensor")
    fx0, fx1, fy0, fy1 = FACH_KK
    hz = p0[2] + (p1[2] - p0[2]) * (fx1 - p0[0]) / (p1[0] - p0[0])
    hy = p0[1] + (p1[1] - p0[1]) * (fx1 - p0[0]) / (p1[0] - p0[0])
    wand = kasten(fx1, fx1 + 3, fy0, fy1, DECK, DECK + 250).fuse(kasten(fx0, fx1 + 3, fy0, fy0 + 3, DECK, DECK + 250))
    wand = wand.fuse(kasten(fx0, fx1 + 3, fy0, fy1, DECK + 250, DECK + 253))
    wand = wand.cut(zyl("x", (0, hy, hz + 9), fx1 - 1, fx1 + 4, 27))
    teil(g, "A24_Trennwand_Kronkorkenfach_Alu_3mm", wand, "alu", nr="A24")
    beh = kasten(-283, -176, 188, 268, DECK, DECK + 150).cut(kasten(-280, -179, 191, 265, DECK + 3, DECK + 151))
    beh = beh.fuse(kasten(-289, -283, 208, 248, DECK + 100, DECK + 120))
    teil(g, "A13_Kronkorkenschublade_PP", beh, "weiss", nr="A13")
    teil(g, "Einweglichtschranke_Sender_B12", sensor_zyl("x", (0, 200, DECK + 158), -282, 12, 14, muttern=False), "sensor")
    teil(g, "Einweglichtschranke_Empfaenger_B12", sensor_zyl("x", (0, 200, DECK + 158), -196, 12, 14, muttern=False), "sensor")
    teil(g, "Reedkontakt_Schublade_B13", kasten(fx1 - 30, fx1 - 10, fy0 + 4, fy0 + 8, DECK + 20, DECK + 40), "sensor")


# ---------------------------------------------------------------- 07 Sensorik, Elektro
def sensorik_elektro():
    g = "07_Sensorik"
    teil(g, "Reflexlichttaster_M18_Station_B6", sensor_zyl("x", (0, 228, Z0 + 32), -95, 18, 30, muttern=False)
         .rotate(V(-95, 228, Z0 + 32), V(-95, 228, Z0 + 33), -39.4), "sensor")
    teil(g, "Sensorhalter_Station", kasten(-125, -95, 220, 236, DECK, Z0 + 23), "stahl")
    teil(g, "Reflexlichttaster_M18_Fach_B7", sensor_zyl("x", (0, -228, Z0 + 32), -95, 18, 30, muttern=False)
         .rotate(V(-95, -228, Z0 + 32), V(-95, -228, Z0 + 33), 39.4), "sensor")
    teil(g, "Sensorhalter_Fach", kasten(-125, -95, -236, -220, DECK, Z0 + 23), "stahl")
    teil(g, "Sensor_induktiv_M12_Sternrad_B4", sensor_zyl("z", (R_REF, 0, 0), Z0 - 40, 12, 32, muttern=False), "sensor")
    g = "09_Elektro"
    sk = kasten(140, 290, 228, 292, DECK, DECK + 200).cut(kasten(143, 287, 231, 289, DECK + 3, DECK + 197))
    teil(g, "Schaltkasten_Stahlblech_150x64x200", sk, "grau")
    teil(g, "Schaltkastentuer", kasten(150, 280, 226, 228, DECK + 10, DECK + 190), "grau")
    for i, (n, dx, dz, w, h, f) in enumerate((
            ("Netzteil_24V_150W_T1", 0, 10, 60, 100, "grau"), ("ESP32_DevKit_A1", 70, 120, 60, 40, "gruen"),
            ("MCP23017_IO-Erweiterung_A7", 70, 165, 30, 20, "gruen"), ("Sicherheitsrelais_K1", 70, 10, 22, 100, "gelb"),
            ("TMC2209_x2_A3_A4", 100, 10, 40, 40, "gruen"), ("H-Bruecke_A5", 100, 60, 30, 30, "gruen"),
            ("Optokoppler_16-fach_A2", 102, 120, 36, 70, "gruen"))):
        teil(g, n, kasten(146 + dx, 146 + dx + w, 270, 287, DECK + dz, DECK + dz + h), f)


# ---------------------------------------------------------------- 08 Haube, Bedienung
def haube_bedienung():
    g = "08_Haube"
    x0, x1, y0, y1 = RAHMEN
    xa, xb, ya, yb = x0 + 5, x1 - 25, y0, y1 - 20
    H = HAUBE_Z
    for x in (xa, xb):
        for y in (ya, yb):
            teil(g, "Profil_20x20_Pfosten", nutprofil20(H - DECK, "z", (x, y, DECK)), "alu")
    for y in (ya, yb):
        teil(g, "Profil_20x20_Riegel_X", nutprofil20(xb - xa + 20, "x", (xa, y, H)), "alu")
    for x in (xa, xb):
        teil(g, "Profil_20x20_Riegel_Y", nutprofil20(yb - ya - 20, "y", (x, ya + 20, H)), "alu")
    fx0, fx1 = FACH_X
    fz1 = DECK + 315
    links = kasten(xa + 8, xa + 12, ya + 20, yb, DECK, H).cut(kasten(xa + 7, xa + 13, 188, 268, DECK + 2, DECK + 172))
    teil(g, "Scheibe_PC_links_mit_Ausschnitt", links, "pc")
    teil(g, "Tuer_Kronkorkenfach_PC", kasten(xa + 2, xa + 6, 184, 272, DECK + 1, DECK + 174), "pc")
    teil(g, "Griff_Tuer_Kronkorkenfach", kasten(xa - 8, xa + 2, 250, 265, DECK + 70, DECK + 110), "schwarz")
    teil(g, "Scheibe_PC_rechts_4mm", kasten(xb + 8, xb + 12, ya + 20, yb, DECK, H), "pc")
    teil(g, "Scheibe_PC_hinten_4mm", kasten(xa + 20, xb, yb + 8, yb + 12, DECK, H), "pc")
    vorn = kasten(xa + 20, xb, ya + 2, ya + 6, DECK, H).cut(kasten(fx0, fx1, ya + 1, ya + 7, DECK + 2, fz1))
    teil(g, "Frontscheibe_PC_mit_Bedienfach", vorn, "pc")
    teil(g, "Servicedeckel_PC_4mm", kasten(xa + 20, xb, ya + 20, yb, H + 16, H + 20), "pc", "d")
    for x in (-200, 200):
        teil(g, "Scharnier_Deckel", zyl("x", (x, yb + 2, H + 20), -20, 20, 5), "schwarz")
    teil(g, "Sicherheitsschalter_Deckel_B1b", kasten(xb - 50, xb - 10, yb - 20, yb, H - 30, H), "gelb")
    # Bedienklappe (Klasse k, Scharnier senkrecht links)
    klappe = kasten(fx0, fx1, ya - 2, ya + 2, DECK + 2, fz1)
    klappe = klappe.fuse(kasten(fx1 - 25, fx1 - 10, ya - 14, ya - 2, DECK + 130, DECK + 190))
    teil(g, "Bedienklappe_PC_6mm_mit_Griff", klappe, "pc", "k")
    for zz in (DECK + 40, fz1 - 40):
        teil(g, "Scharnier_Bedienklappe", zyl("z", (fx0 - 4, ya, 0), zz - 15, zz + 15, 5), "schwarz")
    teil(g, "Sicherheitsschalter_Bedienklappe_B1a", kasten(fx1 + 5, fx1 + 40, ya - 12, ya, fz1 - 50, fz1 - 10), "gelb")
    teil(g, "Betaetiger_Bedienklappe", kasten(fx1 - 8, fx1 + 5, ya - 10, ya - 2, fz1 - 45, fz1 - 15), "stahl", "k")
    teil(g, "LED-Leiste_Bedienfach", kasten(fx0 + 5, fx1 - 5, ya + 8, ya + 14, fz1 + 2, fz1 + 8), "led")
    g = "08_Bedienung"
    px0, px1 = xb - 50, xb + 20
    teil(g, "Bediengehaeuse_ABS", kasten(px0, px1, ya - 40, ya, DECK + 140, DECK + 300)
         .cut(kasten(px0 + 3, px1 - 3, ya - 37, ya - 3, DECK + 143, DECK + 297)), "grau")
    for n, x, zz, f in (("Leuchttaster_Oeffnen_gruen_S1", px0 + 18, DECK + 270, "gruen"),
                        ("Leuchttaster_Laden_blau_S2", px1 - 18, DECK + 270, "blau"),
                        ("Drucktaster_Stopp_rot_S3", px0 + 18, DECK + 225, "rot"),
                        ("Drucktaster_Reset_weiss_S4", px1 - 18, DECK + 225, "weiss")):
        teil(g, n, zyl("y", (x, 0, zz), ya - 46, ya - 40, 11).fuse(zyl("y", (x, 0, zz), ya - 40, ya, 14)), f)
    teil(g, "Not-Halt_Pilztaster_S0", cq.Workplane("XZ").polyline([(0, 0), (14, 0), (14, 6), (20, 9), (20, 15), (0, 15)])
         .close().revolve(360, (0, 0, 0), (0, 1, 0)).val().rotate(V(0, 0, 0), V(1, 0, 0), 90)
         .translate(V((px0 + px1) / 2, ya - 43, DECK + 175)), "rot")
    teil(g, "Not-Halt_Schild_gelb", zyl("y", ((px0 + px1) / 2, 0, DECK + 175), ya - 43, ya - 40, 20), "gelb")
    sx, sy = xa + 30, yb - 10
    teil(g, "Signalsaeule_Fuss", zyl("z", (sx, sy, 0), H + 20, H + 50, 6), "schwarz")
    for i, f in enumerate(("gruen", "gelb", "rot")):
        teil(g, f"Signalsaeule_{f}_P1", zyl("z", (sx, sy, 0), H + 50 + i * 26, H + 74 + i * 26, 17), f)
    teil(g, "Signalsaeule_Deckel", zyl("z", (sx, sy, 0), H + 128, H + 134, 17), "schwarz")


# ---------------------------------------------------------------- 10 Flaschen
def flaschen_formen(fid):
    """Glas (hohl), Etikett, Kronkorken einer Sorte – Mitte x = y = 0, Boden auf Z0."""
    f = next(x for x in M.FLASCHEN if x[0] == fid)
    _, name, H, D, form = f
    pr = M.flasche_profil(H, D, form)
    R = D / 2
    wp = cq.Workplane("XZ").moveTo(0, 0).lineTo(pr[0][0], 0).lineTo(*pr[1]).lineTo(*pr[2])
    wp = wp.spline([p for p in pr[3:13]], includeCurrent=True)
    for p in pr[13:]:
        wp = wp.lineTo(*p)
    glas = wp.lineTo(0, H).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    innen = cq.Workplane("XZ").polyline([(0, 3), (R - 4, 3), (R - 4, pr[2][1]), (11, H - 20), (9.5, H - 1), (0, H - 1)]) \
        .close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
    glas = glas.cut(innen).translate(V(0, 0, Z0))
    etik = cq.Workplane("XZ").center(R + 0.15, 0.35 * H).rect(0.3, 0.2 * H) \
        .revolve(360, (-R - 0.15, 0, 0), (-R - 0.15, 1, 0)).val().translate(V(0, 0, Z0))
    z0, z1 = Z0 + H - 4.5, Z0 + H + 1.5
    pts = [(r * math.cos(2 * math.pi * k / 42), r * math.sin(2 * math.pi * k / 42))
           for k, r in enumerate([14.4 if k % 2 == 0 else 14.9 for k in range(42)])]
    kork = cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0 - 1).val()
    kork = kork.fuse(zyl("z", (0, 0, 0), z1 - 1, z1, 14.2)).cut(zyl("z", (0, 0, 0), z0 - 1, z1 - 1.2, 13.2))
    return name, H, D, glas, etik, kork


def flasche_voll(fid):
    """Massiver Ersatzkörper (Kontur + Kronkorken) für die Kollisionsprüfung."""
    f = next(x for x in M.FLASCHEN if x[0] == fid)
    _, name, H, D, form = f
    s = revolve_profil(M.flasche_profil(H, D, form), (0, 0, Z0))
    return s.fuse(zyl("z", (0, 0, 0), Z0 + H - 4.5, Z0 + H + 1.5, 14.9))


def tasche(i, D, versatz_mm=0.0, drehung=0.0):
    """Lage der Flaschenmitte in Tasche i (0 = Station) nach Sternraddrehung (Grad, Uhrzeigersinn negativ)."""
    r = flaschen_r(D)
    a = math.radians(90 + i * 360 / N_TASCHEN + drehung) + versatz_mm / r
    return r * math.cos(a), r * math.sin(a)


# ================================================================ Aufbau
def aufbauen():
    TEILE.clear()
    for f in (gestell, sternrad, gelaender, z_achse, kopf, abfuhr, sensorik_elektro, haube_bedienung):
        f()
    return TEILE


def gruppen():
    g = {}
    for t in TEILE:
        g.setdefault(t.gruppe, []).append(t)
    return g


def lage(t, dz_kopf=0.0, hebel=0.0, schwenk=0.0, stern=0.0, klappe=0.0, deckel=0.0):
    """Form eines Teils in einer Bewegungsstellung (für Prüfung und Vorschau)."""
    s = t.form
    k = t.klasse
    if k == "st":
        return s.rotate(V(0, 0, 0), V(0, 0, 1), stern)
    if k in ("z", "h", "r", "s"):
        s = s.translate(V(0, 0, dz_kopf))
        zc = ZP + dz_kopf
        if k == "h" and hebel:
            s = s.rotate(V(PX, 0, zc), V(PX, 1, zc), hebel)        # rechte Seite nach unten
        if k == "r" and hebel:
            s = s.translate(V(0, 0, -(AKTOR_X - PX) * math.sin(math.radians(hebel))))
        if k == "s" and schwenk:
            s = s.rotate(V(SCHWENK[0], SCHWENK[1], 0), V(SCHWENK[0], SCHWENK[1], 1), schwenk)
        return s
    if k == "k" and klappe:
        return s.rotate(V(FACH_X[0] - 4, RAHMEN[2], 0), V(FACH_X[0] - 4, RAHMEN[2], 1), -klappe)
    if k == "d" and deckel:
        return s.rotate(V(0, RAHMEN[3] - 18, HAUBE_Z + 20), V(1, RAHMEN[3] - 18, HAUBE_Z + 20), -deckel)
    return s


def baugruppe(mit_flaschen=True):
    asm = cq.Assembly(name="TFO-A_Flaschenoeffner_Automat_IndexB")
    for gname, liste in sorted(gruppen().items()):
        sub = cq.Assembly(name=gname)
        for t in liste:
            sub.add(t.form, name=t.name, color=Color(*FARBEN[t.farbe]))
        asm.add(sub, name=gname)
    if mit_flaschen:
        name, H, D, glas, etik, kork = flaschen_formen(REF[0])
        sub = cq.Assembly(name="10_Flaschen_NRW_0.5l")
        for i in range(N_TASCHEN):
            x, y = tasche(i, D)
            loc = Location(V(x, y, 0))
            sub.add(glas, name=f"Flasche_{i}_Glas", color=Color(0.43, 0.24, 0.08, 0.85), loc=loc)
            sub.add(etik, name=f"Flasche_{i}_Etikett", color=Color(0.92, 0.90, 0.84, 1), loc=loc)
            sub.add(kork, name=f"Flasche_{i}_Kronkorken", color=Color(0.83, 0.69, 0.22, 1), loc=loc)
        asm.add(sub, name="10_Flaschen_NRW_0.5l")
    return asm
