"""
Geometriemodell des Flaschenöffner-Automaten TFO-A, Änderungsindex C. Einzige Quelle
für STEP, STL, Vorschau, Kollisionsprüfung und Dokumentation.

Was Index C gegenüber Index B ändert:
  - Öffnen von oben mit einem GREIFKOPF statt Hebel und Linearantrieb:
    Die Z-Achse setzt den Kopf auf den Kronkorken (Tastleiste, -B3). Servo -M5 schließt
    zwei Backen: Die Hubbacke greift mit ihrer Lippe unter den Kronkorkenrand, die
    Druckbacke liegt mit ihrer Nase oben auf dem Kronkorken. Servo -M6 kippt die ganze
    Greiferschwinge um die Kippachse K, die genau unter der Nase liegt. Wie bei einem
    Handöffner ist die Nase der Drehpunkt (drückt nach unten), die Lippe hebt den Rand
    an. Die Flasche wird deshalb nicht hochgezogen. Der Greifer hält den Kronkorken fest,
    ein Magnet entfällt.
  - Abwurf: Kopf in Abwurfhöhe, Servo -M4 schwenkt eine Fangrinne unter den Greifer,
    Backen auf, der Kronkorken rutscht über Trichter und Rutsche in die Schublade.
  - Flaschen bis Ø 100 mm und 350 mm Höhe: größeres Sternrad (Taschenscheitel R 110),
    Geländerring mit 49 mm Stellweg, höhere Haube und Bedienfach.
  - Die Backen sind 54 mm lang. Dadurch greifen sie den Kronkorken bei jedem
    Durchmesser, obwohl der Hals je nach Sorte bis ±14,3 mm radial woanders steht.

Koordinaten in mm: Z = 0 Tischoberfläche, Bediener bei -Y, Sternradmitte bei x = y = 0.
Station (Öffnen) hinten bei 90°, Bedienfach vorn bei 270°.
Jedes Teil trägt Gruppe, Name, Farbe und Bewegungsklasse (für Vorschau und Prüfung).
"""
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
from cadquery import Color, Location, Vector

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent / "gemeinsam"))
import erzeuge_stl as M  # noqa: E402  (Flaschendaten und -profile)

V = Vector

# ================================================================ Flaschen
# Sorten des Handgeräts plus große Formate (alle mit 26-mm-Kronkorken).
# "Grenzmaß" ist keine reale Flasche, sondern die Hüllflasche für die Auslegung.
FLASCHEN = list(M.FLASCHEN) + [
    ("lgn066", "Longneck 0,66 l", 290.0, 74.0, "lgn"),
    ("sekt075", "Sektform 0,75 l", 305.0, 88.0, "lgn"),
    ("grenz", "Grenzmaß Ø 100 × 350", 350.0, 100.0, "lgn"),
]


def flasche(fid):
    return next(f for f in FLASCHEN if f[0] == fid)


D_MIN, D_MAX = min(f[3] for f in FLASCHEN), max(f[3] for f in FLASCHEN)
H_MIN, H_MAX = min(f[2] for f in FLASCHEN), max(f[2] for f in FLASCHEN)
REF = flasche("nrw05")                   # Modellstellung: NRW 0,5 l
D_FORMAT = REF[3]                        # Geländer im Modell auf diesen Durchmesser eingestellt

# ================================================================ Hauptmaße
RAHMEN = (-340.0, 340.0, -300.0, 340.0)
DECK = 88.0                 # Oberkante Deckplatte
Z0 = 94.0                   # Standfläche der Flaschen (Oberkante Gleitplatte)
R_GLEIT = 240.0
N_TASCHEN = 8
R_SCHEITEL = 110.0          # Scheitel der 90°-Tasche
R_STERN = 178.0             # Außenradius Sternrad (unter dem kleinsten Geländerradius + 6 mm)
STERN_Z = ((15, 25), (95, 105))
HAUBE_Z = 730.0
FACH_X = (-65.0, 65.0)      # Öffnung Bedienfach
FACH_H = 400.0              # lichte Höhe Bedienfach über Deck
R_REF = 75.0                # Referenzfahne/-sensor Sternrad innerhalb der Flaschenbahn
SEGMENTE = ((285.0, 390.0), (30.0, 150.0), (150.0, 255.0))   # Geländer, vorn offen


def flaschen_r(D):
    """Radius der Flaschenmitte in der 90°-Tasche."""
    return R_SCHEITEL + D / 2 * math.sqrt(2)


def gelaender_r(D):
    """Innenradius des Geländers für Durchmesser D (0,5 mm Luft, Feder gleicht aus)."""
    return flaschen_r(D) + D / 2 + 0.5


YS = round((flaschen_r(D_MIN) + flaschen_r(D_MAX)) / 2, 1)    # Greifermitte (166,4)
Y_VERSATZ = flaschen_r(D_MAX) - YS                             # Halslage ± 14,3 mm

# ---------------------------------------------------------------- Greifkopf
# Bezug ist die Kippachse K: waagrecht in Y-Richtung, bei x = KX, Höhe ZK.
# In Arbeitsstellung liegt K 0,5 mm über der Kronkorken-Oberkante.
KX = 12.0
KIPP_WINKEL = 25.0          # Kippen zum Abhebeln (Hubbacke nach oben)
BACKEN_HUB = 8.6            # Hub je Backe (offen -> zu)
LIPPE_X = 13.4              # Lippenspitze, Glas 13,15 mm
BACKE_Y = 27.0              # halbe Backenlänge (deckt ± 14,3 mm Halslage)


def zk_arbeit(H):
    """Kippachse in Arbeitsstellung: 0,5 mm über der Kronkorken-Oberkante."""
    return Z0 + H + 1.5 + 0.5


ZK = zk_arbeit(REF[2])       # Modellstellung (356)
ZK_MIN = zk_arbeit(H_MIN)    # kleinste Flasche (267,5)
ZK_ABWURF = 515.0            # Takten, Abwurf (Kopf über allen Flaschen)
Z_REFERENZ = 522.0           # -B2 meldet

# ---------------------------------------------------------------- Z-Achse
SX, SY = 60.0, round(YS + 70.0, 1)   # Säule 40×40, Vorderkante bei SY
SPINDEL = (118.0, SY + 20.0)

# ---------------------------------------------------------------- Fangrinne, Trichter
PIVOT = (-70.0, 290.0)       # senkrechte Schwenkachse der Fangrinne = Trichtermitte
RINNE_NEIGUNG = 20.0
RINNE_L = 172.0
Z_F0 = 416.0                 # Unterkante Rinnenboden an der Schwenkachse
TRICHTER_OK = 412.0
TRICHTER_UK = 382.0
RINNE_WINKEL = (math.degrees(math.atan2(YS - PIVOT[1], 0.0 - PIVOT[0])) - 180.0) % 360.0   # 119,5°
FACH_KK = (-335.0, -205.0, 205.0, 326.0)        # Kronkorkenfach (x0, x1, y0, y1)


def Y(y):
    return YS + y


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


def ring(mitte, r_innen, r_aussen, z0, z1):
    x, y = mitte
    return zyl("z", (x, y, 0), z0, z1, r_aussen).cut(zyl("z", (x, y, 0), z0 - 1, z1 + 1, r_innen))


def bogenband(r_innen, dicke, z0, z1, w0, w1):
    """Ringsegment (Geländerband) von Winkel w0 bis w1 (Grad)."""
    s = cq.Workplane("XZ").center(r_innen + dicke / 2, (z0 + z1) / 2).rect(dicke, z1 - z0) \
        .revolve(w1 - w0, (-(r_innen + dicke / 2), 0, 0), (-(r_innen + dicke / 2), 1, 0)).val()
    return s.rotate(V(0, 0, 0), V(0, 0, 1), w0)


def polarpunkt(r, w, z=0.0):
    return (r * math.cos(math.radians(w)), r * math.sin(math.radians(w)), z)


def sensor_zyl(achse, mitte, a0, d, laenge, muttern=True):
    """Zylindrischer Sensor: Körper a0 … a0+laenge, Kabelstutzen danach."""
    k = zyl(achse, mitte, a0, a0 + laenge, d / 2)
    k = k.fuse(zyl(achse, mitte, a0 + laenge, a0 + laenge + 10, d / 2 * 0.8))
    for t in ((0.3, 0.6) if muttern else ()):
        aa = a0 + laenge * t
        k = k.fuse(zyl(achse, mitte, aa, aa + d * 0.4, d * 0.9))
    return k


def sensor_strahl(p, ziel, z, d, laenge):
    """Sensor, dessen aktive Fläche bei p liegt und waagrecht auf ziel zeigt."""
    w = math.degrees(math.atan2(ziel[1] - p[1], ziel[0] - p[0]))
    k = zyl("x", (0, 0, 0), -laenge, 0, d / 2).fuse(zyl("x", (0, 0, 0), -laenge - 10, -laenge, d / 2 * 0.8))
    for t in (0.3, 0.6):
        k = k.fuse(zyl("x", (0, 0, 0), -laenge * t - d * 0.2, -laenge * t + d * 0.2, d * 0.9))
    return k.rotate(V(0, 0, 0), V(0, 0, 1), w).translate(V(p[0], p[1], z))


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


def servo(x0, x1, y0, y1, z0, z1, flansch="z"):
    """Servo als Quader mit Befestigungsflansch."""
    k = kasten(x0, x1, y0, y1, z0, z1)
    if flansch == "z":
        zm = z0 + (z1 - z0) * 0.75
        k = k.fuse(kasten(x0 - 7, x1 + 7, y0, y1, zm, zm + 2.5))
    else:
        ym = y0 + (y1 - y0) * 0.75
        k = k.fuse(kasten(x0 - 7, x1 + 7, ym, ym + 2.5, z0, z1))
    return k


def rinne(p0, p1, breite=40.0, hoehe=22.0, wand=1.5):
    """U-förmige Rinne von p0 nach p1 (Mittellinie Unterkante Boden)."""
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


# ================================================================ Teileliste
FARBEN = {
    "alu": (0.78, 0.80, 0.84, 1), "alu_eloxiert": (0.25, 0.53, 0.84, 1), "stahl": (0.42, 0.44, 0.48, 1),
    "stahl_hell": (0.66, 0.68, 0.70, 1), "schwarz": (0.12, 0.12, 0.14, 1), "pe": (0.93, 0.93, 0.90, 1),
    "pe_blau": (0.30, 0.55, 0.85, 1), "gummi": (0.10, 0.10, 0.11, 1), "messing": (0.80, 0.65, 0.25, 1),
    "sensor": (0.15, 0.55, 0.75, 1), "rot": (0.80, 0.12, 0.14, 1), "gruen": (0.15, 0.65, 0.30, 1),
    "gelb": (0.95, 0.75, 0.10, 1), "blau": (0.15, 0.40, 0.80, 1), "grau": (0.55, 0.57, 0.60, 1),
    "weiss": (0.95, 0.95, 0.95, 1), "pc": (0.70, 0.85, 0.95, 0.25), "feder": (0.70, 0.72, 0.75, 1),
    "led": (0.95, 0.95, 0.70, 1), "orange": (0.93, 0.48, 0.12, 1),
}

# Bewegungsklassen:
#   ""  fest            st  Sternrad (dreht um z)       z   Kopfrahmen (Z-Achse)
#   w   Greiferschwinge (Z + Kippen um K)               gl / gr  Backe links / rechts (Z + Kippen + Greifhub)
#   f   Fangrinne (schwenkt um PIVOT)                   k   Bedienklappe        d  Servicedeckel
KOPF_KLASSEN = ("z", "w", "gl", "gr")
SCHWINGE_KLASSEN = ("w", "gl", "gr")


@dataclass
class Teil:
    gruppe: str
    name: str
    form: object
    farbe: str
    klasse: str = ""
    nr: str = ""


TEILE: list = []


def teil(gruppe, name, form, farbe, klasse="", nr=""):
    n = sum(1 for t in TEILE if t.name == name or t.name.startswith(name + "_"))
    TEILE.append(Teil(gruppe, name if n == 0 else f"{name}_{n + 1}", form, farbe, klasse, nr))


# ---------------------------------------------------------------- 01 Gestell
def gestell():
    g = "01_Gestell"
    x0, x1, y0, y1 = RAHMEN
    for y in (y0, y1 - 40):
        teil(g, "Profil_40x80_L680", nutprofil(40, 80, x1 - x0, "x", (x0, y, 0)), "alu")
    for x in (x0, x1 - 40):
        teil(g, "Profil_40x80_L560", nutprofil(40, 80, y1 - y0 - 80, "y", (x, y0 + 40, 0)), "alu")
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
    gleit = gleit.cut(kasten(-55, 55, -236, -98, DECK - 1, Z0 + 1))            # Aussparung Tropfgitter
    gleit = bohren(gleit, "z", (R_REF, 0, 0), DECK, Z0, 14)
    for k in range(6):
        x, y, _ = polarpunkt(R_GLEIT - 14, 30 + 60 * k)
        gleit = senkung(gleit, x, y, Z0, 8.4, 4.5, 6)
    teil(g, "A02_Gleitplatte_PE-UHMW_6mm", gleit, "pe", nr="A02")
    schale = kasten(-53, 53, -234, -100, DECK, DECK + 4).cut(kasten(-51, 51, -232, -102, DECK + 1.5, DECK + 5))
    teil(g, "A14_Tropfschale_PP", schale, "weiss", nr="A14")
    gitter = kasten(-52, 52, -233, -101, DECK + 4, Z0)
    for x in range(-44, 45, 8):
        gitter = gitter.cut(kasten(x - 2, x + 2, -226, -108, DECK + 3, Z0 + 1))
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
GEL_Z = (Z0 + 55, Z0 + 75)
SOCKEL_R = (241.0, 305.0)        # Stellarm-Sockel fest auf dem Deck, Langloch 246 … 300


def gelaender_teile(D):
    """Vom Format abhängige Teile des Geländers (Bänder, Schieber, Klemmhebel, Federn)."""
    r = gelaender_r(D)
    z0, z1 = GEL_Z
    out = []
    for i, (w0, w1) in enumerate(SEGMENTE, 1):
        wm = (w0 + w1) / 2

        def rot(s, wm=wm):
            return s.rotate(V(0, 0, 0), V(0, 0, 1), wm)
        out.append((f"A16_Gelaenderband_{i}_1.4310_2x20", bogenband(r, 2, z0, z1, w0, w1), "stahl_hell", "A16"))
        schieber = kasten(r + 2, r + 14, -8, 8, DECK + 12, z1).fuse(kasten(r + 2, r + 72, -8, 8, DECK + 12, DECK + 20))
        out.append((f"A18_Stellarm_Schieber_{i}", rot(schieber), "alu_eloxiert", "A18"))
        out.append((f"Klemmhebel_M6_{i}", rot(zyl("z", (r + 66, 0, 0), DECK + 20, DECK + 32, 9)
                                               .fuse(kasten(r + 66, r + 92, -4, 4, DECK + 28, DECK + 32))), "schwarz", ""))
        out.append((f"Druckfeder_Gelaender_{i}", rot(zyl("x", (0, 6, (z0 + z1) / 2), r + 14, r + 22, 4)), "feder", ""))
    return out


def gelaender():
    g = "03_Gelaender"
    r0, r1 = SOCKEL_R
    for i, (w0, w1) in enumerate(SEGMENTE, 1):
        wm = (w0 + w1) / 2
        sockel = kasten(r0, r1, -12, 12, DECK, DECK + 12).cut(kasten(r0 + 5, r1 - 5, -3.3, 3.3, DECK - 1, DECK + 13))
        teil(g, f"A17_Stellarm_Sockel_{i}", sockel.rotate(V(0, 0, 0), V(0, 0, 1), wm), "alu_eloxiert", nr="A17")
        teil(g, f"Skala_Formatring_{i}", kasten(r0 + 5, r1 - 5, 12, 13, DECK + 2, DECK + 12)
             .rotate(V(0, 0, 0), V(0, 0, 1), wm), "gelb")
    for name, form, farbe, nr in gelaender_teile(D_FORMAT):
        teil(g, name, form, farbe, nr=nr)


# ---------------------------------------------------------------- 04 Z-Achse
def z_achse():
    g = "04_Z-Achse"
    teil(g, "Profil_40x40_L562_Saeule", nutprofil(40, 40, 650 - DECK, "z", (SX, SY, DECK)), "alu")
    fuss = kasten(SX - 30, SX + 70, SY, SY + 40, DECK, DECK + 6)
    for x in (SX - 20, SX + 60):
        fuss = bohren(fuss, "z", (x, SY + 20, 0), DECK, DECK + 6, 6.6)
    teil(g, "Saeulenfuss_Stahl_6mm", fuss, "stahl")
    schiene = kasten(74, 86, SY - 8, SY, 320, 632)
    for zz in range(330, 632, 25):
        schiene = schiene.cut(zyl("y", (80, 0, zz), SY - 8, SY, 1.75))
    teil(g, "Linearfuehrung_MGN12_L312", schiene, "stahl_hell")
    xs, ys = SPINDEL
    platte = kasten(SX - 5, xs + 25, SY, ys + 25, 650, 658).cut(zyl("z", (xs, ys, 0), 649, 659, 11.25))
    teil(g, "Motorplatte_Alu_8mm", platte, "alu")
    teil(g, "Schrittmotor_NEMA17_Z_M1", nema17((xs, ys, 658), oben=False), "schwarz")
    teil(g, "Kupplung_5x8_D20", zyl("z", (xs, ys, 0), 630, 650, 10).cut(zyl("z", (xs, ys, 0), 629, 651, 2.6)), "alu")
    teil(g, "Trapezgewindespindel_TR8x2_L325", zyl("z", (xs, ys, 0), 305, 630, 4), "stahl_hell")
    teil(g, "Lagerbock_KFL08", kasten(xs - 15, xs + 15, ys - 12, ys + 12, 293, 305)
         .cut(zyl("z", (xs, ys, 0), 292, 306, 11)), "stahl_hell")
    teil(g, "Lagerwinkel_Stahl", kasten(SX + 40, xs - 6, ys - 8, ys + 8, 293, 299), "stahl")
    # -B2 Referenz oben: tastet die Vorderkante des Führungswagens (x = 67) bei ZK = Z_REFERENZ
    teil(g, "Sensor_induktiv_M8_Z-Referenz_B2",
         sensor_zyl("x", (0, SY - 14.5, Z_REFERENZ + 84), 40, 8, 26, muttern=False).rotate(
             V(53, SY - 14.5, Z_REFERENZ + 84), V(53, SY - 14.5, Z_REFERENZ + 85), 180), "sensor")
    teil(g, "Sensorwinkel_Z-Referenz", kasten(36, 62, SY - 8, SY, Z_REFERENZ + 78, Z_REFERENZ + 90), "stahl")


# ---------------------------------------------------------------- 05 Greifkopf
def greifkopf():
    g = "05_Greifkopf"
    z = ZK
    xs, ys = SPINDEL
    # --- Kopfrahmen (Klasse z): Wagen, Schlittenplatte, Kopfträger, Wangen, Kippservo
    teil(g, "Fuehrungswagen_MGN12H", kasten(67, 93, SY - 21, SY - 8, z + 62, z + 106)
         .cut(kasten(73.8, 86.2, SY - 16.2, SY - 7.9, z + 61, z + 107)), "stahl_hell", "z")
    teil(g, "A26_Schlittenplatte_Alu_10mm", kasten(60, 100, SY - 31, SY - 21, z + 55, z + 110), "alu_eloxiert", "z", "A26")
    tr = kasten(-45, 100, Y(-55), SY - 31, z + 100, z + 110)
    teil(g, "A27_Kopftraeger_Alu_10mm", tr, "alu_eloxiert", "z", "A27")
    mh = kasten(100, 132, SY - 31, ys + 13, z + 95, z + 105).cut(zyl("z", (xs, ys, 0), z + 94, z + 106, 5.25))
    teil(g, "A06_Mutternhalter_Alu_10mm", mh, "alu_eloxiert", "z", "A06")
    teil(g, "Spindelmutter_TR8x2_Messing", zyl("z", (xs, ys, 0), z + 83, z + 95, 5.1)
         .fuse(zyl("z", (xs, ys, 0), z + 91.5, z + 95, 11)).cut(zyl("z", (xs, ys, 0), z + 82, z + 96, 4)), "messing", "z")
    for sg in (-1, 1):
        ya, yb = (Y(40), Y(48)) if sg > 0 else (Y(-48), Y(-40))
        wange = kasten(-22, 46, ya, yb, z - 14, z + 100)
        wange = bohren(wange, "y", (KX, 0, z), ya, yb, 12)
        wange = wange.cut(kasten(-10, 34, ya - 1, yb + 1, z + 30, z + 80))         # Erleichterung
        teil(g, "A28_Kopfwange_Alu_8mm", wange, "alu_eloxiert", "z", "A28")
        bb = zyl("y", (KX, 0, z), ya - (1 if sg < 0 else 0), yb + (1 if sg > 0 else 0), 6) \
            .cut(zyl("y", (KX, 0, z), ya - 2, yb + 2, 4))
        teil(g, "Bundbuchse_iglidur_G_8x12x10", bb, "gelb", "z")
    # Kippservo -M6 vorn, Zahnradstufe 2 : 1 auf die Kippachse
    teil(g, "Servo_DS5160_60kgcm_M6", servo(0, 54, Y(-92), Y(-62), z + 14, z + 46, "y"), "schwarz", "z")
    teil(g, "A29_Servohalter_Kippen_Alu_6mm", kasten(-6, 50, Y(-62), Y(-40), z + 46, z + 52), "alu_eloxiert", "z", "A29")
    teil(g, "Stirnrad_m1_Z20", zyl("y", (KX, 0, z + 30), Y(-60), Y(-54), 11).cut(zyl("y", (KX, 0, z + 30), Y(-61), Y(-53), 3)),
         "messing", "z")
    teil(g, "Sensor_induktiv_M8_Kippen_Grundstellung_B10",
         sensor_zyl("y", (18, 0, z + 36), Y(40), 8, 26, muttern=False), "sensor", "z")
    # --- Greiferschwinge (Klasse w): kippt um K
    teil(g, "Stirnrad_m1_Z40", zyl("y", (KX, 0, z), Y(-60), Y(-54), 21).cut(zyl("y", (KX, 0, z), Y(-61), Y(-53), 4)),
         "messing", "w")
    for y0, y1 in ((Y(-60), Y(-30)), (Y(30), Y(52))):
        teil(g, "Lagerbolzen_D8_gehaertet", zyl("y", (KX, 0, z), y0, y1, 4), "stahl_hell", "w")
    for sg in (-1, 1):
        ya, yb = (Y(32), Y(38)) if sg > 0 else (Y(-38), Y(-32))
        sw = bohren(kasten(0, 24, ya, yb, z - 6, z + 45), "y", (KX, 0, z), ya, yb, 8)
        teil(g, "A34_Schwingenwange_S235_6mm", sw, "alu_eloxiert", "w", "A34")
    br = kasten(-44, 40, Y(-38), Y(38), z + 35, z + 45)
    for yy in (-16, 16):
        br = bohren(br, "z", (-2, Y(yy), 0), z + 35, z + 45, 6.4)
    teil(g, "A30_Greiferbruecke_Alu_10mm", br, "alu_eloxiert", "w", "A30")
    for sg in (-1, 1):
        y0, y1 = (Y(13), Y(20)) if sg > 0 else (Y(-20), Y(-13))
        teil(g, "Profilschiene_MGN7_L84", kasten(-44, 40, y0, y1, z + 30, z + 35), "stahl_hell", "w")
    teil(g, "Servo_MG996R_6V_M5", servo(-20, 20, Y(-10), Y(10), z + 45, z + 86), "schwarz", "w")
    teil(g, "Ritzel_m1_Z16", zyl("z", (0, Y(0), 0), z + 30, z + 35, 8.5), "messing", "w")
    tl = kasten(-9, 5, Y(-22), Y(22), z - 0.3, z + 5.7)
    teil(g, "A33_Tastleiste_POM_14x44", tl, "weiss", "w", "A33")
    teil(g, "Induktivsensor_flach_Kronkorken_B8", kasten(-12, 8, Y(-11), Y(11), z + 8, z + 22), "sensor", "w")
    for yy in (-16, 16):
        teil(g, "Fuehrungsstift_D6", zyl("z", (-2, Y(yy), 0), z + 5.7, z + 50, 3), "stahl_hell", "w")
        teil(g, "Druckfeder_Tastleiste", zyl("z", (-2, Y(yy), 0), z + 5.7, z + 30, 5)
             .cut(zyl("z", (-2, Y(yy), 0), z + 5, z + 31, 4)), "feder", "w")
    teil(g, "Schaltfahne_Tastleiste", kasten(-8, 4, Y(10), Y(22), z + 50, z + 52), "stahl", "w")
    teil(g, "Sensor_induktiv_M8_Tastleiste_B3", sensor_zyl("z", (-2, Y(16), 0), z + 56, 8, 26, muttern=False), "sensor", "w")
    teil(g, "Sensorwinkel_Tastleiste", kasten(-8, 4, Y(21), Y(24), z + 45, z + 62)
         .fuse(kasten(-8, 4, Y(10), Y(24), z + 60, z + 62).cut(zyl("z", (-2, Y(16), 0), z + 59, z + 63, 4.1))), "stahl", "w")
    # --- Backen (Klassen gl / gr), gezeichnet in Stellung "zu"
    lippe = cq.Workplane("XZ").polyline([(-LIPPE_X, z - 7), (-20, z - 7), (-20, z - 10),
                                         (-LIPPE_X - 3 * math.tan(math.radians(30)), z - 10)]).close() \
        .extrude(-2 * BACKE_Y).val().translate(V(0, Y(-BACKE_Y), 0))
    hub = lippe.fuse(kasten(-26, -20, Y(-BACKE_Y), Y(BACKE_Y), z - 10, z + 24)) \
        .fuse(kasten(-26, -14, Y(-BACKE_Y), Y(BACKE_Y), z + 24, z + 30))
    teil(g, "A31_Hubbacke_C45_gehaertet", hub, "stahl", "gl", "A31")
    druck = kasten(16.5, 22.5, Y(-BACKE_Y), Y(BACKE_Y), z - 3, z + 24) \
        .fuse(kasten(9, 16.5, Y(-BACKE_Y), Y(BACKE_Y), z, z + 5)) \
        .fuse(kasten(10.5, 22.5, Y(-BACKE_Y), Y(BACKE_Y), z + 24, z + 30))
    teil(g, "A32_Druckbacke_C45_gehaertet", druck, "stahl", "gr", "A32")
    for x0_, x1_, kl in ((-26, -14, "gl"), (10.5, 22.5, "gr")):
        teil(g, "Zahnstange_m1_L40", kasten(x0_ - (14 if kl == "gl" else 0), x1_ + (14 if kl == "gr" else 0),
                                            Y(-3), Y(3), z + 30, z + 33), "messing", kl)


# ---------------------------------------------------------------- 06 Kronkorken-Abfuhr
def rinne_punkte():
    """Fangrinne in Parkstellung (zeigt nach -x): Station-Ende hoch, Achsende tief."""
    px, py = PIVOT
    t = math.tan(math.radians(RINNE_NEIGUNG))
    return (px - RINNE_L, py, Z_F0 + RINNE_L * t), (px, py, Z_F0)


def rutsche_punkte():
    px, py = PIVOT
    p0 = (px - 3.0, py, TRICHTER_UK - 6.0)
    p1 = (-228.0, 262.0, 0.0)
    L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
    return p0, (p1[0], p1[1], p0[2] - L * math.tan(math.radians(25)))


def rinne_boden(rho):
    """Unterkante Rinnenboden im Abstand rho von der Schwenkachse."""
    return Z_F0 + rho * math.tan(math.radians(RINNE_NEIGUNG))


def abfuhr():
    g = "06_Kronkorken-Abfuhr"
    px, py = PIVOT
    # Trichter rund, PETG
    aussen = cq.Solid.makeCone(13.0, 24.0, TRICHTER_OK - TRICHTER_UK, V(px, py, TRICHTER_UK), V(0, 0, 1))
    innen = cq.Solid.makeCone(11.5, 22.5, TRICHTER_OK - TRICHTER_UK + 0.2, V(px, py, TRICHTER_UK - 0.1), V(0, 0, 1))
    teil(g, "A22_Trichter_PETG", aussen.cut(innen), "pe", nr="A22")
    halter = ring(PIVOT, 13.2, 17, TRICHTER_UK - 4, TRICHTER_UK + 4) \
        .fuse(kasten(px - 4, px + 4, py + 15, py + 34, TRICHTER_UK - 4, TRICHTER_UK + 2)) \
        .fuse(kasten(px - 4, px + 4, py + 30, py + 34, DECK, TRICHTER_UK + 2))
    teil(g, "Trichterhalter_Stahl", halter, "stahl")
    # Fangrinne (Klasse f) mit Drehring, Parkstellung
    p0, p1 = rinne_punkte()
    teil(g, "A35_Fangrinne_1.4301_1mm", rinne(p0, p1, breite=50, hoehe=12, wand=1.2), "stahl_hell", "f", "A35")
    teil(g, "A36_Drehring_POM", ring(PIVOT, 26, 33, TRICHTER_OK - 8, TRICHTER_OK), "weiss", "f", "A36")
    teil(g, "Rinnenhalter_Stahl", kasten(px - 33, px - 26, py - 6, py + 6, TRICHTER_OK, rinne_boden(26) + 0.5), "stahl", "f")
    teil(g, "Lagerbock_Drehring", ring(PIVOT, 24.5, 25.8, TRICHTER_OK - 10, TRICHTER_OK - 2)
         .fuse(kasten(px - 4, px + 4, py + 24, py + 34, TRICHTER_OK - 10, TRICHTER_OK - 6))
         .fuse(kasten(px - 4, px + 4, py + 30, py + 34, TRICHTER_UK + 2, TRICHTER_OK - 6)), "stahl")
    # Servo -M4 (270°) treibt den Drehring über Ritzel Z33 auf Zahnkranz Z66 (2 : 1 -> bis 135°)
    teil(g, "Servo_DS3218_270Grad_M4", servo(px + 42, px + 62, py - 30, py + 10, TRICHTER_OK - 48, TRICHTER_OK - 6), "schwarz")
    teil(g, "Stirnrad_m1_Z33_Servo_Rinne", zyl("z", (px + 49.5, py, 0), TRICHTER_OK - 6, TRICHTER_OK - 2, 17), "messing")
    # Rutsche, Zähl-Lichtschranke, Fach
    q0, q1 = rutsche_punkte()
    teil(g, "A23_Rutsche_1.4301_1.5mm", rinne(q0, q1), "stahl_hell", nr="A23")
    t = 0.5
    gx, gy, gz = [q0[i] + (q1[i] - q0[i]) * t for i in range(3)]
    gabel = kasten(gx - 4, gx + 4, gy - 28, gy + 28, gz - 10, gz - 6)
    gabel = gabel.fuse(kasten(gx - 4, gx + 4, gy - 28, gy - 23, gz - 6, gz + 28))
    gabel = gabel.fuse(kasten(gx - 4, gx + 4, gy + 23, gy + 28, gz - 6, gz + 28))
    teil(g, "Gabellichtschranke_B11", gabel, "sensor")
    fx0, fx1, fy0, fy1 = FACH_KK
    s = (fx1 - q0[0]) / (q1[0] - q0[0])
    hz = q0[2] + (q1[2] - q0[2]) * s
    hy = q0[1] + (q1[1] - q0[1]) * s
    wand = kasten(fx1, fx1 + 3, fy0, fy1, DECK, DECK + 250).fuse(kasten(fx0, fx1 + 3, fy0, fy0 + 3, DECK, DECK + 250))
    wand = wand.fuse(kasten(fx0, fx1 + 3, fy0, fy1, DECK + 250, DECK + 253))
    wand = wand.cut(zyl("x", (0, hy, hz + 9), fx1 - 1, fx1 + 4, 27))
    teil(g, "A24_Trennwand_Kronkorkenfach_Alu_3mm", wand, "alu", nr="A24")
    beh = kasten(-323, -216, 213, 300, DECK, DECK + 150).cut(kasten(-320, -219, 216, 297, DECK + 3, DECK + 151))
    beh = beh.fuse(kasten(-329, -323, 236, 276, DECK + 100, DECK + 120))
    teil(g, "A13_Kronkorkenschublade_PP", beh, "weiss", nr="A13")
    teil(g, "Einweglichtschranke_Sender_B12", sensor_zyl("x", (0, 226, DECK + 158), -322, 12, 14, muttern=False), "sensor")
    teil(g, "Einweglichtschranke_Empfaenger_B12", sensor_zyl("x", (0, 226, DECK + 158), -236, 12, 14, muttern=False), "sensor")
    teil(g, "Reedkontakt_Schublade_B13", kasten(fx1 - 30, fx1 - 10, fy0 + 4, fy0 + 8, DECK + 20, DECK + 40), "sensor")


# ---------------------------------------------------------------- 07 Sensorik, 09 Elektro
def sensorik_elektro():
    g = "07_Sensorik"
    for (px_, py_), ziel, n in (((-110.0, 250.0), (0.0, YS), "Reflexlichttaster_M18_Station_B6"),
                                ((-110.0, -250.0), (0.0, -YS), "Reflexlichttaster_M18_Fach_B7")):
        teil(g, n, sensor_strahl((px_, py_), ziel, Z0 + 32, 18, 30), "sensor")
        teil(g, "Sensorhalter_" + n.split("_")[-2], kasten(px_ - 40, px_ - 22, py_ - 8, py_ + 8, DECK, Z0 + 23), "stahl")
    teil(g, "Sensor_induktiv_M12_Sternrad_B4", sensor_zyl("z", (R_REF, 0, 0), Z0 - 40, 12, 32, muttern=False), "sensor")
    g = "09_Elektro"
    sk = kasten(150, 300, 262, 326, DECK, DECK + 200).cut(kasten(153, 297, 265, 323, DECK + 3, DECK + 197))
    teil(g, "Schaltkasten_Stahlblech_150x64x200", sk, "grau")
    teil(g, "Schaltkastentuer", kasten(160, 290, 260, 262, DECK + 10, DECK + 190), "grau")
    for n, dx, dz, w, h, f in (
            ("Netzteil_24V_200W_T1", 0, 10, 60, 100, "grau"), ("ESP32_DevKit_A1", 70, 120, 60, 40, "gruen"),
            ("MCP23017_IO-Erweiterung_A7", 70, 165, 30, 20, "gruen"), ("Sicherheitsrelais_K1", 70, 10, 22, 100, "gelb"),
            ("TMC2209_x2_A3_A4", 100, 10, 40, 40, "gruen"), ("DC-DC_6V_10A_T3", 100, 55, 40, 25, "grau"),
            ("DC-DC_7V4_10A_T4", 100, 84, 40, 25, "grau"), ("Optokoppler_16-fach_A2", 0, 120, 60, 70, "gruen")):
        teil(g, n, kasten(156 + dx, 156 + dx + w, 304, 321, DECK + dz, DECK + dz + h), f)


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
    fz1 = DECK + FACH_H
    fy0, fy1 = FACH_KK[2] + 8, FACH_KK[3] - 8
    links = kasten(xa + 8, xa + 12, ya + 20, yb, DECK, H).cut(kasten(xa + 7, xa + 13, fy0, fy1, DECK + 2, DECK + 172))
    teil(g, "Scheibe_PC_links_mit_Ausschnitt", links, "pc")
    teil(g, "Tuer_Kronkorkenfach_PC", kasten(xa + 2, xa + 6, fy0 - 4, fy1 + 4, DECK + 1, DECK + 174), "pc")
    teil(g, "Griff_Tuer_Kronkorkenfach", kasten(xa - 8, xa + 2, fy1 - 20, fy1 - 5, DECK + 70, DECK + 110), "schwarz")
    teil(g, "Scheibe_PC_rechts_4mm", kasten(xb + 8, xb + 12, ya + 20, yb, DECK, H), "pc")
    teil(g, "Scheibe_PC_hinten_4mm", kasten(xa + 20, xb, yb + 8, yb + 12, DECK, H), "pc")
    vorn = kasten(xa + 20, xb, ya + 2, ya + 6, DECK, H).cut(kasten(fx0, fx1, ya + 1, ya + 7, DECK + 2, fz1))
    teil(g, "Frontscheibe_PC_mit_Bedienfach", vorn, "pc")
    teil(g, "Servicedeckel_PC_4mm", kasten(xa + 20, xb, ya + 20, yb, H + 16, H + 20), "pc", "d")
    for x in (-220, 220):
        teil(g, "Scharnier_Deckel", zyl("x", (x, yb + 2, H + 20), -20, 20, 5), "schwarz")
    teil(g, "Sicherheitsschalter_Deckel_B1b", kasten(xb - 50, xb - 10, yb - 20, yb, H - 30, H), "gelb")
    klappe = kasten(fx0, fx1, ya - 2, ya + 2, DECK + 2, fz1)
    klappe = klappe.fuse(kasten(fx1 - 25, fx1 - 10, ya - 14, ya - 2, DECK + 170, DECK + 240))
    teil(g, "Bedienklappe_PC_6mm_mit_Griff", klappe, "pc", "k")
    for zz in (DECK + 50, fz1 - 50):
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
    """Glas (hohl), Etikett, Kronkorken einer Sorte. Mitte x = y = 0, Boden auf Z0."""
    _, name, H, D, form = flasche(fid)
    pr = M.flasche_profil(H, D, form)
    R = D / 2
    # Schulter als Polygonzug (feiner aufgelöst) statt Spline: Spline-Rotationsflächen
    # zeigen manche STEP-Viewer nicht an (Flasche erscheint dann ohne Schulter).
    pts = [(0, 0), (pr[0][0], 0), pr[1], pr[2]]
    hb, hs, rn = (pr[2][1], pr[12][1], pr[12][0])
    for i in range(1, 25):
        t = i / 24
        s = t * t * (3 - 2 * t)
        pts.append((R + (rn - R) * s, hb + (hs - hb) * t))
    pts += list(pr[13:]) + [(0, H)]
    glas = cq.Workplane("XZ").polyline(pts).close().revolve(360, (0, 0, 0), (0, 1, 0)).val()
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


def glas_voll(fid):
    """Massiver Glaskörper ohne Kronkorken (Kollisionsprüfung)."""
    _, name, H, D, form = flasche(fid)
    return revolve_profil(M.flasche_profil(H, D, form), (0, 0, Z0))


def flasche_voll(fid):
    """Massiver Ersatzkörper (Kontur + Kronkorken) für die Kollisionsprüfung."""
    H = flasche(fid)[2]
    return glas_voll(fid).fuse(zyl("z", (0, 0, 0), Z0 + H - 4.5, Z0 + H + 1.5, 14.9))


def tasche(i, D, versatz_mm=0.0, drehung=0.0):
    """Lage der Flaschenmitte in Tasche i (0 = Station) nach Sternraddrehung (Grad, Uhrzeigersinn negativ)."""
    r = flaschen_r(D)
    a = math.radians(90 + i * 360 / N_TASCHEN + drehung) + versatz_mm / r
    return r * math.cos(a), r * math.sin(a)


# ================================================================ Aufbau
def aufbauen():
    TEILE.clear()
    for f in (gestell, sternrad, gelaender, z_achse, greifkopf, abfuhr, sensorik_elektro, haube_bedienung):
        f()
    return TEILE


def gruppen():
    g = {}
    for t in TEILE:
        g.setdefault(t.gruppe, []).append(t)
    return g


def lage(t, zk=None, kipp=0.0, greif=1.0, stern=0.0, rinne_w=0.0, klappe=0.0, deckel=0.0):
    """Form eines Teils in einer Bewegungsstellung (für Prüfung und Vorschau).

    zk     Höhe der Kippachse (None = Modellstellung)
    kipp   Kippwinkel der Greiferschwinge in Grad (+ = Hubbacke nach oben)
    greif  0 = Backen offen, 1 = zu (Modell), > 1 = nachgreifen
    """
    s = t.form
    k = t.klasse
    if k == "st":
        return s.rotate(V(0, 0, 0), V(0, 0, 1), stern) if stern else s
    if k in KOPF_KLASSEN:
        if k == "gl" and greif != 1.0:
            s = s.translate(V(-BACKEN_HUB * (1 - greif), 0, 0))
        if k == "gr" and greif != 1.0:
            s = s.translate(V(BACKEN_HUB * (1 - greif), 0, 0))
        dz = 0.0 if zk is None else zk - ZK
        if dz:
            s = s.translate(V(0, 0, dz))
        if k != "z" and kipp:
            zc = ZK + dz
            s = s.rotate(V(KX, 0, zc), V(KX, 1, zc), kipp)
        return s
    if k == "f" and rinne_w:
        return s.rotate(V(PIVOT[0], PIVOT[1], 0), V(PIVOT[0], PIVOT[1], 1), rinne_w)
    if k == "k" and klappe:
        return s.rotate(V(FACH_X[0] - 4, RAHMEN[2], 0), V(FACH_X[0] - 4, RAHMEN[2], 1), -klappe)
    if k == "d" and deckel:
        return s.rotate(V(0, RAHMEN[3] - 18, HAUBE_Z + 20), V(1, RAHMEN[3] - 18, HAUBE_Z + 20), -deckel)
    return s


def baugruppe(mit_flaschen=True):
    asm = cq.Assembly(name="TFO-A_Flaschenoeffner_Automat_IndexC")
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


if __name__ == "__main__":
    aufbauen()
    print(f"{len(TEILE)} Teile in {len(gruppen())} Gruppen")
    print(f"YS {YS}  Halslage ±{Y_VERSATZ:.1f}  ZK {ZK}  ZK_MIN {ZK_MIN}  Rinnenwinkel {RINNE_WINKEL:.1f}°")
    print(f"Geländer {gelaender_r(D_MIN):.1f} … {gelaender_r(D_MAX):.1f} mm")
    falsch = [t.name for t in TEILE if t.form.Volume() <= 0 or not t.form.isValid()]
    print("ungültig:", falsch)
