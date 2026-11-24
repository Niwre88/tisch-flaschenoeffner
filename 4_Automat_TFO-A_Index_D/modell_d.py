"""
Geometriemodell des Flaschenöffner-Automaten TFO-A, Änderungsindex D. Einzige Quelle
für STEP, STL, Vorschau, Kollisionsprüfung und Dokumentation.

Konzept Index D (alles neu gegenüber B und C):
  - TRANSPORT: Magnetbahn (Stadionform) mit 6 unabhängigen Movern. Jede Flasche steht auf
    ihrem eigenen Mover in einer selbstzentrierenden Klemme (zwei 90°-V-Backen, Feder
    schließt, feste Kurvenschiene öffnet an Ausgabe und Laden). Dadurch steht die
    Flaschenachse bei jedem Durchmesser (59,5 … 100 mm) genau in der Bahn.
    Ablauf gegen den Uhrzeigersinn: Laden (vorn rechts) -> Messen (hinten rechts) ->
    Öffnen (hinten Mitte) -> Ausgabe (vorn links). Flasche für Flasche.
  - MESSEN im Vorbeifahren: Laser-Abstandssensor misst die Kronkorkenhöhe, Kamera prüft
    den Verschluss. Der Kopf steht schon auf der richtigen Höhe, wenn die Flasche kommt.
  - ÖFFNEN durch ORBITAL-ENTBÖRDELN: offener Rotorring (Schlitz wie bei einer
    Orbital-Schweißzange), Ständer zweigeteilt (vorn/hinten), Flasche fährt durch.
    Drei Hartmetallrollen auf Schwenkhebeln laufen um den Kronkorken und biegen die
    Zähne schrittweise auf. Zustellung über einen zweiten Ring (Winkelversatz,
    elektronisches Getriebe). Ein Magnet-Überband hält den Kronkorken nieder, das CO2
    entweicht langsam, danach hängt der Kronkorken am Band.
  - ABFUHR: Überband (fährt mit der Z-Achse) übergibt an ein senkrechtes
    Magnet-Steigband, das die Kronkorken in einen durchsichtigen Sammelturm wirft.
  - STEUERUNG: Industrie-PC mit TwinCAT, EtherCAT, TwinSAFE (siehe sps/).

Koordinaten in mm: Z = 0 Tischoberfläche, Bediener bei -Y, Bahnmitte bei x = y = 0.
Mover-Teile werden in MOVER-KOORDINATEN gezeichnet: Ursprung = Flaschenachse auf der
Standfläche, +x in Fahrtrichtung, +y zur Bahn (nach innen).
"""
import math
import sys
from dataclasses import dataclass
from pathlib import Path

import cadquery as cq
from cadquery import Color, Location, Vector

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent / "gemeinsam"))
import erzeuge_stl as M  # noqa: E402  (Flaschenprofile)

V = Vector

# ================================================================ Flaschen (wie Index C, alle mit 26-mm-Kronkorken)
FLASCHEN = list(M.FLASCHEN) + [
    ("lgn066", "Longneck 0,66 l", 290.0, 74.0, "lgn"),
    ("sekt075", "Sektform 0,75 l", 305.0, 88.0, "lgn"),
    ("grenz", "Grenzmaß Ø 100 × 350", 350.0, 100.0, "lgn"),
]


def flasche(fid):
    return next(f for f in FLASCHEN if f[0] == fid)


D_MIN, D_MAX = min(f[3] for f in FLASCHEN), max(f[3] for f in FLASCHEN)
H_MIN, H_MAX = min(f[2] for f in FLASCHEN), max(f[2] for f in FLASCHEN)
REF = flasche("nrw05")

# ================================================================ Hauptmaße
RAHMEN = (-520.0, 520.0, -300.0, 400.0)
DECK = 88.0
HAUBE_Z = 850.0
A_GERADE = 200.0            # Geraden der Bahn von x = -200 … +200
RK = 100.0                  # Kurvenradius Bahnmitte (Motormodule)
OFF = 115.0                 # Flaschenachse liegt 115 mm außerhalb der Bahnmitte
RF = RK + OFF               # Radius der Flaschenbahn in den Kurven (215)
BAHN_Z = (DECK + 12, DECK + 112)
Z0 = DECK + 28              # Standfläche der Flaschen (Oberkante Halterplatte) = 116
N_MOVER = 6
L_BAHN = 4 * A_GERADE + 2 * math.pi * RK                     # 1428,3 mm
U2 = 2 * A_GERADE + math.pi * RK                             # Beginn der hinteren Geraden
YS = RF                                                      # Öffnungsstation (0, 215)

# Stationen als Bahnweg u (mm ab vorn links, gegen den Uhrzeigersinn)
STATIONEN = {
    "Ausgabe": 80.0,                         # vorn links  (x = -120)
    "Laden": 320.0,                          # vorn rechts (x = +120)
    "Kurve rechts": 2 * A_GERADE + math.pi * RK / 2,
    "Messen": U2 + 20.0,                     # hinten rechts (x = +180)
    "Oeffnen": U2 + 200.0,                   # hinten Mitte (x = 0)
    "Kurve links": U2 + 2 * A_GERADE + math.pi * RK / 2,
}
SLOTS = ["Ausgabe", "Laden", "Kurve rechts", "Messen", "Oeffnen", "Kurve links"]


def bahn(u):
    """Bahnmitte bei Weg u: Punkt (x, y), Fahrtrichtung t, Außennormale n."""
    u = u % L_BAHN
    a, r = A_GERADE, RK
    if u < 2 * a:
        return (-a + u, -r), (1.0, 0.0), (0.0, -1.0)
    u -= 2 * a
    if u < math.pi * r:
        p = -math.pi / 2 + u / r
        return (a + r * math.cos(p), r * math.sin(p)), (-math.sin(p), math.cos(p)), (math.cos(p), math.sin(p))
    u -= math.pi * r
    if u < 2 * a:
        return (a - u, r), (-1.0, 0.0), (0.0, 1.0)
    u -= 2 * a
    p = math.pi / 2 + u / r
    return (-a + r * math.cos(p), r * math.sin(p)), (-math.sin(p), math.cos(p)), (math.cos(p), math.sin(p))


def mover_lage(u):
    """Flaschenachse (x, y) und Drehwinkel (Grad) der Mover-Koordinaten bei Weg u."""
    (cx, cy), t, n = bahn(u)
    return (cx + OFF * n[0], cy + OFF * n[1]), math.degrees(math.atan2(t[1], t[0]))


# ---------------------------------------------------------------- Klemme (Mover-Koordinaten)
KLEMME_Z = (Z0 + 60, Z0 + 75)
V_TIEFE = 40.0
BACKE_AUF = 12.0            # Öffnung je Backe über den größten Durchmesser hinaus


def backe_x(D):
    """Scheitel der V-Backe für Durchmesser D (90°-V)."""
    return D / 2 * math.sqrt(2)


# ---------------------------------------------------------------- Orbitalkopf
# Bezug ist die Kronkorken-Oberkante ZC in Arbeitsstellung, Achse bei (0, YS).
def zc_arbeit(H):
    return Z0 + H + 1.5


ZC = zc_arbeit(REF[2])               # Modellstellung (377,5)
ZC_MIN, ZC_MAX = zc_arbeit(H_MIN), zc_arbeit(H_MAX)
ABHEBEN = 8.0                        # Kopf hebt nach dem Entbördeln, Kronkorken hängt am Band
SCHLITZ = 54.0                       # Schlitzbreite Rotor (Grad)
R_ROTOR = (40.0, 52.0)
R_STATOR = (54.0, 66.0)
STATOR_W = ((40.0, 140.0), (220.0, 320.0))   # hinten / vorn, offen bei ±x
ARM_W = (60.0, 180.0, 300.0)         # Hebel bei Schlitz auf 0°
R_ROLLE_AUS = 27.0                   # Rollenmitte zurückgezogen
R_ROLLE_EIN = 16.4                   # Rollenmitte zugestellt (Kante 13,4 mm, Glas 13,15 mm)
ROLLE_R = 3.0
ROLLE_HUB = 1.5                      # Anstieg der Rolle am Ende der Zustellung (Aufbiegen)
Z_ARM = (-9.8, -6.3)                 # Hebelebene unter der Zahnkante (Kronkorken bis -6,0)
# Alles Drehende und der Ständer liegen unter z = -6,3: der Kronkorken (hängt am Überband bis -5,5)
# gleitet beim Abtransport nach hinten mit 0,8 mm Luft darüber.
UEBERBAND_SPALT = 0.5

# ---------------------------------------------------------------- Z-Modul, Steigband, Turm, Messen
ZMOD = (60.0, 120.0, 345.0, 385.0)   # x0, x1, y0, y1
STEIG = (-22.0, 22.0, 336.0, 364.0, 270.0, 815.0)
TURM = (-170.0, 330.0)
TURM_R = 43.0
TURM_OK = 700.0
MESS = (180.0, YS)
LASER_Z = 525.0


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


def profil20(laenge, achse, ecke):
    """Systemprofil 20×20, vereinfacht als Vollquader (ohne Spline-Flächen)."""
    x, y, z = ecke
    L = {"x": (laenge, 20, 20), "y": (20, laenge, 20), "z": (20, 20, laenge)}[achse]
    return kasten(x, x + L[0], y, y + L[1], z, z + L[2])


def ring(mitte, r_innen, r_aussen, z0, z1, w0=None, w1=None):
    """Kreisring, optional nur der Sektor w0 … w1 (Grad, gegen den Uhrzeigersinn)."""
    x, y = mitte
    if w0 is None:
        return zyl("z", (x, y, 0), z0, z1, r_aussen).cut(zyl("z", (x, y, 0), z0 - 1, z1 + 1, r_innen))
    s = cq.Workplane("XZ").center(r_innen + (r_aussen - r_innen) / 2, (z0 + z1) / 2).rect(r_aussen - r_innen, z1 - z0) \
        .revolve(w1 - w0, (-(r_innen + (r_aussen - r_innen) / 2), 0, 0), (-(r_innen + (r_aussen - r_innen) / 2), 1, 0)).val()
    return s.rotate(V(0, 0, 0), V(0, 0, 1), w0).translate(V(x, y, 0))


def polar(mitte, r, w):
    return mitte[0] + r * math.cos(math.radians(w)), mitte[1] + r * math.sin(math.radians(w))


def sensor_zyl(achse, mitte, a0, d, laenge, muttern=True):
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


def servomotor(x, y, z_flansch, laenge, kante=60, nach_oben=True):
    """EtherCAT-Servomotor mit Flansch (senkrecht), Flansch bei z_flansch."""
    s = 1 if nach_oben else -1
    k = cq.Workplane("XY").rect(kante, kante).extrude(laenge).edges("|Z").fillet(6).val()
    k = k.translate(V(x, y, z_flansch if nach_oben else z_flansch - laenge))
    k = k.fuse(zyl("z", (x, y, 0), *(sorted((z_flansch + s * laenge, z_flansch + s * (laenge + 22)))), 9))
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
    "alu": (0.78, 0.80, 0.84, 1), "alu_eloxiert": (0.25, 0.53, 0.84, 1), "anthrazit": (0.22, 0.24, 0.28, 1),
    "stahl": (0.42, 0.44, 0.48, 1), "stahl_hell": (0.66, 0.68, 0.70, 1), "schwarz": (0.12, 0.12, 0.14, 1),
    "pe": (0.93, 0.93, 0.90, 1), "gummi": (0.10, 0.10, 0.11, 1), "messing": (0.80, 0.65, 0.25, 1),
    "hartmetall": (0.55, 0.50, 0.62, 1), "sensor": (0.15, 0.55, 0.75, 1), "rot": (0.80, 0.12, 0.14, 1),
    "gruen": (0.15, 0.65, 0.30, 1), "gelb": (0.95, 0.75, 0.10, 1), "blau": (0.15, 0.40, 0.80, 1),
    "grau": (0.55, 0.57, 0.60, 1), "weiss": (0.95, 0.95, 0.95, 1), "pc": (0.70, 0.85, 0.95, 0.25),
    "turm": (0.75, 0.90, 1.00, 0.35), "led": (0.95, 0.95, 0.70, 1), "orange": (0.93, 0.48, 0.12, 1),
    "bahn": (0.30, 0.33, 0.38, 1), "band": (0.20, 0.20, 0.22, 1), "display": (0.10, 0.20, 0.35, 1),
}

# Bewegungsklassen:
#   ""  fest      z  Kopfrahmen (Z-Achse)      ro  Orbitalrotor (Z + Drehung)   zr  Zustellring (Z + Drehung)
#   a0, a1, a2  Entbördelhebel (Z + Drehung + Zustellung)
#   mov  Mover mit Halter (Mover-Koordinaten)    jl / jr  Klemmbacken (Mover-Koordinaten + Hub)
#   k1 / k2  Klappe Ausgabe / Laden          d  Servicedeckel
KOPF_KLASSEN = ("z", "ro", "zr", "a0", "a1", "a2")
MOVER_KLASSEN = ("mov", "jl", "jr")


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
        teil(g, "Profil_40x80_L1040", nutprofil(40, 80, x1 - x0, "x", (x0, y, 0)), "alu")
    for x in (x0, x1 - 40):
        teil(g, "Profil_40x80_L620", nutprofil(40, 80, y1 - y0 - 80, "y", (x, y0 + 40, 0)), "alu")
    for x in (x0 + 25, x1 - 25):
        for y in (y0 + 25, y1 - 25):
            teil(g, "Geraetefuss_D36_M8", zyl("z", (x, y, 0), -8, 0, 18).fuse(zyl("z", (x, y, 0), 0, 12, 4)), "gummi")
    deck = kasten(x0, x1, y0, y1, 80, DECK)
    for x in (x0 + 20, 0, x1 - 20):
        for y in (y0 + 20, y1 - 20):
            deck = senkung(deck, x, y, DECK, 12.4, 6.6, 8)
    teil(g, "A01_Deckplatte_EN-AW-5754_8mm", deck, "alu", nr="A01")
    # Tropfwanne unter der Öffnungsstation (fängt Schaum und Tropfen)
    w = kasten(-90, 90, YS - 70, YS + 70, DECK, DECK + 6).cut(kasten(-87, 87, YS - 67, YS + 67, DECK + 1.5, DECK + 7))
    teil(g, "A14_Tropfwanne_Edelstahl", w, "stahl_hell", nr="A14")


# ---------------------------------------------------------------- 02 Magnetbahn
def stadion(r_innen, r_aussen, z0, z1):
    """Körper in Stadionform zwischen den Abständen r_innen … r_aussen von der Bahnmitte."""
    a = A_GERADE
    k = kasten(-a, a, -r_aussen, -r_innen, z0, z1)
    k = k.fuse(kasten(-a, a, r_innen, r_aussen, z0, z1))
    for sx, w0 in ((a, -90.0), (-a, 90.0)):
        k = k.fuse(ring((sx, 0), r_innen, r_aussen, z0, z1, w0, w0 + 180))
    return k


def magnetbahn():
    g = "02_Magnetbahn"
    z0, z1 = BAHN_Z
    teil(g, "Magnetbahn_Motormodule_Stadion_L1428", stadion(RK - 25, RK + 25, z0, z1), "bahn")
    for x in (-A_GERADE, -70, 70, A_GERADE):
        for sy in (-1, 1):
            teil(g, "Bahnstuetze_Alu", kasten(x - 20, x + 20, sy * RK - 20, sy * RK + 20, DECK, z0), "alu")
    # Kurvenschienen zum Öffnen der Klemmen an Ausgabe und Laden (vorne, unter dem Halter)
    for name in ("Ausgabe", "Laden"):
        (x, y), _ = mover_lage(STATIONEN[name])
        teil(g, f"A20_Kurvenschiene_{name}", kasten(x - 70, x + 70, y + 56, y + 64, DECK, DECK + 14)
             .fuse(kasten(x - 30, x + 30, y + 54, y + 56, DECK + 2, DECK + 14)), "stahl", nr="A20")


# ---------------------------------------------------------------- 11 Mover (Mover-Koordinaten)
def mover():
    g = "11_Mover"
    teil(g, "Mover_Magnetbahn", kasten(-25, 25, 60, 90, DECK + 15, DECK + 105)
         .fuse(kasten(-22, 22, 82, 89.5, DECK + 30, DECK + 90)), "anthrazit", "mov")
    for zz in (DECK + 22, DECK + 98):
        teil(g, "Laufrolle_Mover", zyl("x", (0, 85.8, zz), -20, 20, 4), "schwarz", "mov")
    platte = kasten(-55, 55, -55, 60, Z0 - 8, Z0).cut(zyl("z", (0, 0, 0), Z0 - 9, Z0 + 1, 6))
    teil(g, "A21_Halterplatte_Alu_8mm", platte, "alu_eloxiert", "mov", "A21")
    teil(g, "A22_Halterstuetze_Alu", kasten(-12, 12, 50, 60, Z0, KLEMME_Z[1]), "alu_eloxiert", "mov", "A22")
    teil(g, "Klemmschiene_MGN9_L168", kasten(-84, 84, 50, 60, KLEMME_Z[0], KLEMME_Z[1]), "stahl_hell", "mov")
    teil(g, "Zugfeder_Klemme", zyl("x", (0, 55, KLEMME_Z[1] + 9), -60, 60, 3), "stahl_hell", "mov")
    teil(g, "Kurvenrolle_Klemme", zyl("z", (0, 51, 0), Z0 - 22, Z0 - 8, 4.5), "schwarz", "mov")
    teil(g, "Zahnstangenpaar_Klemme", kasten(-60, 60, 51, 59, KLEMME_Z[1], KLEMME_Z[1] + 5), "messing", "mov")
    # Klemmbacken: 90°-V, gezeichnet für Durchmesser D_REF (Hub über lage(…, klemme=D))
    for sg, kl in ((-1, "jl"), (1, "jr")):
        xa = sg * backe_x(REF[3])
        T = V_TIEFE
        pts = [(xa, 0), (xa - sg * T, -T), (xa - sg * T, -T - 6), (xa + sg * 12, -T - 6),
               (xa + sg * 12, T + 6), (xa - sg * T, T + 6), (xa - sg * T, T)]
        if sg > 0:
            pts = pts[::-1]
        v = cq.Workplane("XY").polyline(pts).close().extrude(KLEMME_Z[1] - KLEMME_Z[0]).val() \
            .translate(V(0, 0, KLEMME_Z[0]))
        v = v.fuse(kasten(min(xa, xa + sg * 12), max(xa, xa + sg * 12), T + 6, 50, KLEMME_Z[0], KLEMME_Z[1]))
        teil(g, f"A23_Klemmbacke_{'links' if sg < 0 else 'rechts'}_POM", v, "weiss", kl, "A23")


# ---------------------------------------------------------------- 04 Z-Achse
def z_achse():
    g = "04_Z-Achse"
    x0, x1, y0, y1 = ZMOD
    mod = kasten(x0, x1, y0, y1, DECK, 650).cut(kasten(x0 + 8, x1 - 8, y0 - 1, y0 + 6, DECK + 30, 640))
    teil(g, "Linearmodul_Kugelgewinde_Hub420", mod, "alu")
    teil(g, "Servomotor_Z-Achse_M1", servomotor((x0 + x1) / 2, (y0 + y1) / 2, 650, 120, 55), "schwarz")
    teil(g, "Modulfuss_Stahl", kasten(x0 - 20, x1 + 20, y0 - 5, y1 + 5, DECK, DECK + 8), "stahl")


# ---------------------------------------------------------------- 05 Orbital-Entbördelkopf
def orbitalkopf():
    g = "05_Orbitalkopf"
    z = ZC
    m = (0.0, YS)
    x0, x1, y0, y1 = ZMOD
    # Kopfrahmen (Klasse z)
    teil(g, "Schlitten_Linearmodul", kasten(x0 + 2, x1 - 2, y0 - 7, y0, z + 30, z + 110), "stahl_hell", "z")
    teil(g, "A45_Schlittenplatte_Alu_8mm", kasten(x0, x1, y0 - 15, y0 - 7, z + 30, z + 110), "alu_eloxiert", "z", "A45")
    tr = kasten(-80, 120, Y(-65), 300, z + 62, z + 72).fuse(kasten(x0, x1, 300, y0 - 7, z + 62, z + 72))
    tr = tr.cut(kasten(-24, 24, Y(-30), 300, z + 61, z + 73))           # Fenster über dem Überband
    teil(g, "A44_Kopftraeger_Alu_10mm", tr, "alu_eloxiert", "z", "A44")
    for i, (w0, w1) in enumerate(STATOR_W):
        st = ring(m, *R_STATOR, z - 22, z - 6.5, w0, w1)
        teil(g, f"A40_Statorsegment_{'hinten' if i == 0 else 'vorn'}", st, "alu_eloxiert", "z", "A40")
        for w in ((50.0, 130.0) if i == 0 else (240.0, 300.0)):
            px, py = polar(m, 60, w)
            teil(g, "Stuetze_Stator", kasten(px - 4, px + 4, py - 4, py + 4, z - 6.5, z + 62), "alu", "z")
    for w in (90.0, 245.0, 270.0, 295.0):
        px, py = polar(m, 55.5, w)
        teil(g, "Fuehrungsrolle_Rotor", zyl("z", (px, py, 0), z - 20, z - 6.8, 2.8), "stahl_hell", "z")
    for w in (45.0, 135.0):
        px, py = polar(m, 58, w)
        teil(g, "Ritzel_Rotor", zyl("z", (px, py, 0), z - 14, z - 9.8, 6), "messing", "z")
    for w in (60.0, 120.0):
        px, py = polar(m, 58, w)
        teil(g, "Ritzel_Zustellring", zyl("z", (px, py, 0), z - 18.2, z - 14, 6), "messing", "z")
    teil(g, "Servomotor_Rotor_M2", servomotor(70, Y(50), z - 6.5, 70, 45), "schwarz", "z")
    teil(g, "Servomotor_Zustellung_M3", servomotor(-70, Y(50), z - 6.5, 70, 45), "schwarz", "z")
    # Magnet-Überband (Klasse z): Unterkante 0,5 mm über dem Kronkorken
    u0 = z + UEBERBAND_SPALT
    band = kasten(-20, 20, Y(-30), Y(115), u0, u0 + 26).cut(kasten(-21, 21, Y(-18), Y(103), u0 + 1.5, u0 + 24.5))
    teil(g, "Magnet-Ueberband_Gurt_B40", band, "band", "z")
    for yy in (Y(-17), Y(102)):
        teil(g, "Umlenkrolle_Ueberband", zyl("x", (0, yy, u0 + 13), -19, 19, 11.5), "stahl_hell", "z")
    teil(g, "Magnetleiste_NdFeB_Ueberband", kasten(-17, 17, Y(-14), Y(98), u0 + 2, u0 + 9), "stahl", "z")
    teil(g, "A46_Bandrahmen_Ueberband", kasten(-26, -22, Y(-30), Y(115), u0, u0 + 26)
         .fuse(kasten(22, 26, Y(-30), Y(115), u0, u0 + 26))
         .fuse(kasten(-30, 30, Y(60), Y(70), u0 + 26, z + 62)), "alu_eloxiert", "z", "A46")
    teil(g, "Getriebemotor_Ueberband_M4", kasten(26, 66, Y(95), Y(115), u0 + 4, u0 + 40)
         .fuse(zyl("x", (0, Y(102), u0 + 13), 26, 32, 6)), "schwarz", "z")
    teil(g, "Sensor_induktiv_M12_Kronkorken_B8", sensor_zyl("z", (0, Y(85), 0), u0 + 26, 12, 20, muttern=False), "sensor", "z")
    # Rotor (ro) und Zustellring (zr) mit Schlitz bei 0° (Einfahrt von +x)
    for name, (za, zb), kl, nr in (("A41_Orbitalrotor_Stahl", (z - 14, z - 9.8), "ro", "A41"),
                                   ("A42_Zustellring_Stahl", (z - 18.2, z - 14), "zr", "A42")):
        teil(g, name, ring(m, *R_ROTOR, za, zb, SCHLITZ / 2, 360 - SCHLITZ / 2), "stahl", kl, nr)
    # Entbördelhebel mit Hartmetallrolle (a0 … a2), gezeichnet zurückgezogen
    for i, w in enumerate(ARM_W):
        za, zb = z + Z_ARM[0], z + Z_ARM[1]
        hebel = kasten(R_ROLLE_AUS, 49, -4, 4, za, zb).fuse(zyl("z", (46, 0, 0), za - 8.4, zb, 3))   # Bolzen nach unten in den Zustellring
        rolle = zyl("z", (R_ROLLE_AUS, 0, 0), za, zb, ROLLE_R)
        for s, n, f, nr in ((hebel, "A43_Entboerdelhebel_gehaertet", "stahl", "A43"),
                            (rolle, "Entboerdelrolle_Hartmetall_D6", "hartmetall", "")):
            teil(g, n, s.rotate(V(0, 0, 0), V(0, 0, 1), w).translate(V(m[0], m[1], 0)), f, f"a{i}", nr)


# ---------------------------------------------------------------- 06 Kronkorken-Abfuhr
def abfuhr():
    g = "06_Kronkorken-Abfuhr"
    x0, x1, y0, y1, z0, z1 = STEIG
    band = kasten(x0, x1, y0, y1, z0, z1).cut(kasten(x0 - 1, x1 + 1, y0 + 2, y1 - 2, z0 + 14, z1 - 14))
    teil(g, "Magnet-Steigband_Gurt_B44", band, "band")
    for zz in (z0 + 14, z1 - 14):
        teil(g, "Umlenkrolle_Steigband", zyl("x", (0, (y0 + y1) / 2, zz), x0 + 1, x1 - 1, 12), "stahl_hell")
    teil(g, "Magnetleiste_NdFeB_Steigband", kasten(x0 + 3, x1 - 3, y0 + 3, y0 + 9, z0 + 10, z1 - 30), "stahl")
    rahmen = kasten(x0 - 5, x0, y0 - 2, y1 + 4, z0 - 10, z1 + 6).fuse(kasten(x1, x1 + 5, y0 - 2, y1 + 4, z0 - 10, z1 + 6))
    rahmen = rahmen.fuse(kasten(x0 - 5, x1 + 5, y1 + 4, y1 + 12, DECK, z1 + 6))
    teil(g, "A47_Steigbandrahmen_Alu", rahmen, "alu_eloxiert", nr="A47")
    teil(g, "Getriebemotor_Steigband_M5", kasten(x0 - 45, x0 - 5, y0 + 2, y1 - 2, z0 - 6, z0 + 34), "schwarz")
    # Abwurfrutsche oben zum Turm, Zähl-Lichtschranke
    tx, ty = TURM
    # Die Magnetleiste endet 30 mm unter der oberen Rolle: dort fällt der Kronkorken nach vorn ab.
    p0, p1 = (8.0, y0 - 24, z1 - 46), (tx + 18, ty - 6, TURM_OK + 6)
    teil(g, "A48_Abwurfrutsche_1.4301", rinne(p0, p1, 44, 18, 1.2), "stahl_hell", nr="A48")
    teil(g, "Rutschenhalter", kasten(-32, -27, y0 - 46, y0 - 2, p0[2] - 24, p0[2] + 2)
         .fuse(kasten(tx + 14, tx + 26, ty + 40, ty + 46, DECK, TURM_OK + 4)), "stahl")
    mx, my = [(p0[i] + p1[i]) / 2 for i in range(2)]
    mz = (p0[2] + p1[2]) / 2
    teil(g, "Gabellichtschranke_Zaehlen_B11", kasten(mx - 4, mx + 4, my - 30, my + 30, mz - 12, mz - 8)
         .fuse(kasten(mx - 4, mx + 4, my - 30, my - 25, mz - 8, mz + 26))
         .fuse(kasten(mx - 4, mx + 4, my + 25, my + 30, mz - 8, mz + 26)), "sensor")
    # Sammelturm (abnehmbar), Füllstand
    teil(g, "A49_Sammelturm_PC_D86", ring(TURM, TURM_R - 3, TURM_R, DECK + 14, TURM_OK)
         .fuse(zyl("z", (tx, ty, 0), DECK + 10, DECK + 14, TURM_R)), "turm", nr="A49")
    trichter = cq.Solid.makeCone(TURM_R, 60, 22, V(tx, ty, TURM_OK), V(0, 0, 1)) \
        .cut(cq.Solid.makeCone(TURM_R - 2, 58, 22.2, V(tx, ty, TURM_OK - 0.1), V(0, 0, 1)))
    teil(g, "A50_Einfuelltrichter_Turm_PETG", trichter, "pe", nr="A50")
    teil(g, "Turmsockel_mit_Bajonett", ring(TURM, TURM_R + 1, TURM_R + 9, DECK, DECK + 30), "anthrazit")
    teil(g, "Griff_Sammelturm", kasten(tx - 8, tx + 8, ty - TURM_R - 14, ty - TURM_R, TURM_OK - 120, TURM_OK - 40), "schwarz")
    teil(g, "Einweglichtschranke_Turm_voll_B12", sensor_zyl("x", (0, ty, TURM_OK - 30), tx + TURM_R + 4, 12, 16, False), "sensor")
    teil(g, "Reedkontakt_Turm_eingesetzt_B13", kasten(tx + TURM_R + 9, tx + TURM_R + 15, ty - 10, ty + 10, DECK + 5, DECK + 25), "sensor")


# ---------------------------------------------------------------- 07 Messen, Sensorik
def sensorik():
    g = "07_Sensorik"
    mx, my = MESS
    teil(g, "Messsaeule_Profil_40x40", nutprofil(40, 40, LASER_Z + 30 - DECK, "z", (mx - 20, 300, DECK)), "alu")
    teil(g, "Messausleger_Alu", kasten(mx - 15, mx + 15, my - 25, 300, LASER_Z + 20, LASER_Z + 30), "alu_eloxiert")
    teil(g, "Laser-Abstandssensor_Hoehe_B3", kasten(mx - 18, mx + 18, my - 22, my + 22, LASER_Z, LASER_Z + 20), "sensor")
    teil(g, "Smart-Kamera_Verschluss_B4", kasten(mx + 18, mx + 48, my - 15, my + 15, LASER_Z - 15, LASER_Z + 20)
         .fuse(zyl("z", (mx + 33, my, 0), LASER_Z - 25, LASER_Z - 15, 9)), "schwarz")
    teil(g, "Ringlicht_LED_Kamera", ring((mx + 33, my), 10, 16, LASER_Z - 29, LASER_Z - 25), "led")
    # Flasche im Fach: Reflextaster mit Hintergrundausblendung, schaut von oben in die Tasche
    for name, st in (("Reflextaster_Ausgabe_B6", "Ausgabe"), ("Reflextaster_Laden_B7", "Laden")):
        (zx, zy), _ = mover_lage(STATIONEN[st])
        teil(g, name, sensor_zyl("z", (zx, zy, 0), DECK + FACH_H + 40, 18, 30, muttern=False), "sensor")
        teil(g, "Sensorwinkel_" + st, kasten(zx - 12, zx + 12, RAHMEN[2] + 6, zy + 12, DECK + FACH_H + 70, DECK + FACH_H + 74), "stahl")


# ---------------------------------------------------------------- 08 Haube, Bedienung, 09 Elektro
FACH = {"Ausgabe": -120.0, "Laden": 120.0}
FACH_B, FACH_H = 150.0, 430.0


def haube_bedienung():
    g = "08_Haube"
    x0, x1, y0, y1 = RAHMEN
    xa, xb, ya, yb = x0 + 5, x1 - 25, y0, y1 - 20
    H = HAUBE_Z
    for x in (xa, xb):
        for y in (ya, yb):
            teil(g, "Profil_20x20_Pfosten", profil20(H - DECK, "z", (x, y, DECK)), "alu")
    for y in (ya, yb):
        teil(g, "Profil_20x20_Riegel_X", profil20(xb - xa + 20, "x", (xa, y, H)), "alu")
    for x in (xa, xb):
        teil(g, "Profil_20x20_Riegel_Y", profil20(yb - ya - 20, "y", (x, ya + 20, H)), "alu")
    teil(g, "Scheibe_PC_links_4mm", kasten(xa + 8, xa + 12, ya + 20, yb, DECK, H), "pc")
    teil(g, "Scheibe_PC_rechts_4mm", kasten(xb + 8, xb + 12, ya + 20, yb, DECK, H), "pc")
    teil(g, "Scheibe_PC_hinten_4mm", kasten(xa + 20, xb, yb + 8, yb + 12, DECK, H), "pc")
    vorn = kasten(xa + 20, xb, ya + 2, ya + 6, DECK, H)
    for name, fx in FACH.items():
        vorn = vorn.cut(kasten(fx - FACH_B / 2, fx + FACH_B / 2, ya + 1, ya + 7, DECK + 2, DECK + FACH_H))
    teil(g, "Frontscheibe_PC_mit_2_Faechern", vorn, "pc")
    teil(g, "Servicedeckel_PC_4mm", kasten(xa + 20, xb, ya + 20, yb, H + 16, H + 20), "pc", "d")
    for x in (-300, 300):
        teil(g, "Scharnier_Deckel", zyl("x", (x, yb + 2, H + 20), -20, 20, 5), "schwarz")
    teil(g, "Sicherheitsschalter_Deckel_B1c", kasten(xb - 50, xb - 10, yb - 20, yb, H - 30, H), "gelb")
    for i, (name, fx) in enumerate(FACH.items(), 1):
        f0, f1 = fx - FACH_B / 2, fx + FACH_B / 2
        kl = kasten(f0, f1, ya - 2, ya + 2, DECK + 2, DECK + FACH_H)
        kl = kl.fuse(kasten(f1 - 25, f1 - 10, ya - 14, ya - 2, DECK + 190, DECK + 260))
        teil(g, f"Klappe_{name}_PC_6mm_mit_Griff", kl, "pc", f"k{i}")
        for zz in (DECK + 50, DECK + FACH_H - 50):
            teil(g, f"Scharnier_Klappe_{name}", zyl("z", (f0 - 4, ya, 0), zz - 15, zz + 15, 5), "schwarz")
        teil(g, f"Sicherheitsschalter_Klappe_{name}_B1{'a' if i == 1 else 'b'}",
             kasten(f1 + 5, f1 + 40, ya - 12, ya, DECK + FACH_H - 50, DECK + FACH_H - 10), "gelb")
        teil(g, f"Betaetiger_Klappe_{name}", kasten(f1 - 8, f1 + 5, ya - 10, ya - 2, DECK + FACH_H - 45, DECK + FACH_H - 15),
             "stahl", f"k{i}")
        teil(g, f"LED-Leiste_Fach_{name}", kasten(f0 + 5, f1 - 5, ya + 8, ya + 14, DECK + FACH_H + 2, DECK + FACH_H + 8), "led")
    g = "08_Bedienung"
    px0, px1 = 330.0, 470.0
    teil(g, "Bedienpanel_Touch_7Zoll_A20", kasten(px0, px1, ya - 30, ya - 2, DECK + 260, DECK + 360), "anthrazit")
    teil(g, "Display_Bedienpanel", kasten(px0 + 8, px1 - 8, ya - 31, ya - 30, DECK + 268, DECK + 352), "display")
    teil(g, "Not-Halt_Pilztaster_S0", cq.Workplane("XZ").polyline([(0, 0), (14, 0), (14, 6), (20, 9), (20, 15), (0, 15)])
         .close().revolve(360, (0, 0, 0), (0, 1, 0)).val().rotate(V(0, 0, 0), V(1, 0, 0), 90)
         .translate(V(400, ya - 3, DECK + 200)), "rot")
    teil(g, "Not-Halt_Gehaeuse_gelb", kasten(375, 425, ya - 3, ya + 2, DECK + 175, DECK + 225), "gelb")
    teil(g, "Leuchttaster_Oeffnen_gruen_S1", zyl("y", (350, 0, DECK + 140), ya - 10, ya, 11), "gruen")
    teil(g, "Drucktaster_Stopp_rot_S3", zyl("y", (450, 0, DECK + 140), ya - 10, ya, 11), "rot")
    teil(g, "Leuchtdrucktaster_Quittieren_blau_S4", zyl("y", (400, 0, DECK + 140), ya - 10, ya, 11), "blau")
    sx, sy = xa + 40, yb - 10
    teil(g, "Signalsaeule_Fuss", zyl("z", (sx, sy, 0), H + 20, H + 50, 6), "schwarz")
    for i, f in enumerate(("gruen", "gelb", "rot")):
        teil(g, f"Signalsaeule_{f}_P1", zyl("z", (sx, sy, 0), H + 50 + i * 26, H + 74 + i * 26, 17), f)
    teil(g, "Signalsaeule_Deckel", zyl("z", (sx, sy, 0), H + 128, H + 134, 17), "schwarz")
    g = "09_Elektro"
    sk = kasten(300, 495, 300, 375, DECK, DECK + 300).cut(kasten(303, 492, 303, 372, DECK + 3, DECK + 297))
    teil(g, "Schaltschrank_Stahlblech_195x75x300", sk, "grau")
    teil(g, "Schaltschranktuer", kasten(310, 485, 298, 300, DECK + 10, DECK + 290), "grau")
    for n, dx, dz, w, h, f in (
            ("Netzteil_24V_20A_T1", 0, 10, 60, 120, "grau"), ("Netzteil_48V_20A_Magnetbahn_T2", 65, 10, 70, 120, "grau"),
            ("Embedded-PC_TwinCAT_A1", 0, 150, 90, 100, "anthrazit"), ("EtherCAT-Klemmen_A2", 95, 150, 85, 100, "orange"),
            ("Servoverstaerker_3-fach_A3", 140, 10, 45, 120, "anthrazit"), ("Sicherheitssteuerung_TwinSAFE_A4", 95, 255, 85, 35, "gelb")):
        teil(g, n, kasten(306 + dx, 306 + dx + w, 355, 370, DECK + dz, DECK + dz + h), f)


# ---------------------------------------------------------------- 10 Flaschen
def flaschen_formen(fid):
    """Glas (hohl), Etikett, Kronkorken einer Sorte. Mitte x = y = 0, Boden auf Z0.
    Schulter als Polygonzug, damit jeder STEP-Viewer sie darstellt."""
    _, name, H, D, form = flasche(fid)
    pr = M.flasche_profil(H, D, form)
    R = D / 2
    pts = [(0, 0), (pr[0][0], 0), pr[1], pr[2]]
    hb, hs, rn = pr[2][1], pr[12][1], pr[12][0]
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
    return name, H, D, glas, etik, kronkorken(H)


def kronkorken(H, z_ok=None):
    """Kronkorken (21 Zähne), Oberkante bei z_ok (Standard: auf der Flasche)."""
    z1 = Z0 + H + 1.5 if z_ok is None else z_ok
    z0 = z1 - 6
    pts = [(r * math.cos(2 * math.pi * k / 42), r * math.sin(2 * math.pi * k / 42))
           for k, r in enumerate([14.4 if k % 2 == 0 else 14.9 for k in range(42)])]
    kork = cq.Workplane("XY").workplane(offset=z0).polyline(pts).close().extrude(z1 - z0 - 1).val()
    return kork.fuse(zyl("z", (0, 0, 0), z1 - 1, z1, 14.2)).cut(zyl("z", (0, 0, 0), z0 - 1, z1 - 1.2, 13.2))


def glas_voll(fid):
    _, name, H, D, form = flasche(fid)
    return revolve_profil(M.flasche_profil(H, D, form), (0, 0, Z0))


def revolve_profil(pts, mitte=(0, 0, 0)):
    wp = cq.Workplane("XZ").polyline([(0, pts[0][1])] + list(pts) + [(0, pts[-1][1])]).close()
    return wp.revolve(360, (0, 0, 0), (0, 1, 0)).val().translate(V(*mitte))


def flasche_voll(fid):
    H = flasche(fid)[2]
    return glas_voll(fid).fuse(zyl("z", (0, 0, 0), Z0 + H - 4.5, Z0 + H + 1.5, 14.9))


# ================================================================ Aufbau, Stellungen
def aufbauen():
    TEILE.clear()
    for f in (gestell, magnetbahn, mover, z_achse, orbitalkopf, abfuhr, sensorik, haube_bedienung):
        f()
    return TEILE


def gruppen():
    g = {}
    for t in TEILE:
        g.setdefault(t.gruppe, []).append(t)
    return g


def platziere(s, u):
    """Form in Mover-Koordinaten an den Bahnweg u setzen."""
    (x, y), w = mover_lage(u)
    return s.rotate(V(0, 0, 0), V(0, 0, 1), w).translate(V(x, y, 0))


def lage(t, zc=None, rotor=0.0, zustell=0.0, u=None, klemme=None, klappe1=0.0, klappe2=0.0, deckel=0.0):
    """Form eines Teils in einer Bewegungsstellung (für Prüfung und Vorschau).

    zc       Kronkorken-Oberkante, auf die der Kopf eingestellt ist (None = Modellstellung)
    rotor    Drehwinkel von Rotor, Zustellring und Hebeln (Grad, 0 = Schlitz bei +x)
    zustell  0 = Rollen zurück, 1 = Rollenkante auf 13,4 mm
    u        Bahnweg des Movers (nur Mover-Teile)
    klemme   Durchmesser, auf den die Backen geschlossen sind (None = Modell, 'auf' = offen)
    """
    s, k = t.form, t.klasse
    if k in MOVER_KLASSEN:
        if k in ("jl", "jr") and klemme is not None:
            ziel = backe_x(D_MAX) + BACKE_AUF if klemme == "auf" else backe_x(klemme)
            d = ziel - backe_x(REF[3])
            s = s.translate(V(-d if k == "jl" else d, 0, 0))
        return platziere(s, u) if u is not None else s
    if k in KOPF_KLASSEN:
        if k.startswith("a") and zustell:
            # Hebelachse geneigt: auf den letzten 30 % der Zustellung steigt die Rolle um 1,5 mm
            # und biegt die Zahnkante gegen den vom Überband gehaltenen Kronkorken auf.
            w = math.radians(ARM_W[int(k[1])])
            r = -(R_ROLLE_AUS - R_ROLLE_EIN) * min(zustell, 1.0)
            hub = ROLLE_HUB * min(1.0, max(0.0, (zustell - 0.7) / 0.3))
            s = s.translate(V(r * math.cos(w), r * math.sin(w), hub))
        if k != "z" and rotor:
            s = s.rotate(V(0, YS, 0), V(0, YS, 1), rotor)
        dz = 0.0 if zc is None else zc - ZC
        return s.translate(V(0, 0, dz)) if dz else s
    if k == "k1" and klappe1:
        return s.rotate(V(FACH["Ausgabe"] - FACH_B / 2 - 4, RAHMEN[2], 0), V(FACH["Ausgabe"] - FACH_B / 2 - 4, RAHMEN[2], 1), -klappe1)
    if k == "k2" and klappe2:
        return s.rotate(V(FACH["Laden"] - FACH_B / 2 - 4, RAHMEN[2], 0), V(FACH["Laden"] - FACH_B / 2 - 4, RAHMEN[2], 1), -klappe2)
    if k == "d" and deckel:
        return s.rotate(V(0, RAHMEN[3] - 18, HAUBE_Z + 20), V(1, RAHMEN[3] - 18, HAUBE_Z + 20), -deckel)
    return s


def baugruppe(mit_flaschen=True):
    asm = cq.Assembly(name="TFO-A_Flaschenoeffner_Automat_IndexD")
    for gname, liste in sorted(gruppen().items()):
        if gname == "11_Mover":
            continue
        sub = cq.Assembly(name=gname)
        for t in liste:
            sub.add(t.form, name=t.name, color=Color(*FARBEN[t.farbe]))
        asm.add(sub, name=gname)
    mover_teile = gruppen()["11_Mover"]
    name, H, D, glas, etik, kork = flaschen_formen(REF[0])
    for i, slot in enumerate(SLOTS):
        (x, y), w = mover_lage(STATIONEN[slot])
        loc = Location(V(x, y, 0), V(0, 0, 1), w)
        sub = cq.Assembly(name=f"11_Mover_{i + 1}_{slot.replace(' ', '_')}", loc=loc)
        for t in mover_teile:
            sub.add(t.form, name=f"{t.name}_M{i + 1}", color=Color(*FARBEN[t.farbe]))
        if mit_flaschen:
            sub.add(glas, name=f"Flasche_M{i + 1}_Glas", color=Color(0.43, 0.24, 0.08, 0.85))
            sub.add(etik, name=f"Flasche_M{i + 1}_Etikett", color=Color(0.92, 0.90, 0.84, 1))
            if slot not in ("Kurve links", "Ausgabe"):
                sub.add(kork, name=f"Flasche_M{i + 1}_Kronkorken", color=Color(0.83, 0.69, 0.22, 1))
        asm.add(sub)
    return asm


if __name__ == "__main__":
    aufbauen()
    print(f"{len(TEILE)} Teile in {len(gruppen())} Gruppen, Bahnlänge {L_BAHN:.1f} mm")
    for s in SLOTS:
        (x, y), w = mover_lage(STATIONEN[s])
        print(f"  {s:13s} u = {STATIONEN[s]:7.1f}  ({x:7.1f}, {y:7.1f})  {w:6.1f}°")
    print(f"ZC {ZC}  ZC_MIN {ZC_MIN}  ZC_MAX {ZC_MAX}")
    falsch = [t.name for t in TEILE if t.form.Volume() <= 0 or not t.form.isValid()]
    print("ungültig:", falsch)
