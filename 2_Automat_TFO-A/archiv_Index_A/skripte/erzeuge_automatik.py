"""
Automatischer Flaschenöffner TFO-A – 3D-Modell, STL-Dateien und Vorschaudaten.

Aufbau (Koordinaten in mm, Z = 0 Tischoberfläche, Bediener bei -Y):
  - Grundrahmen aus Systemprofil 40x80, Deckplatte, Gleitplatte (PE-UHMW)
  - Sternrad mit 8 V-Taschen (Flaschenmagazin), Antrieb Schrittmotor + Zahnriemen 5:1
  - gefederter Führungsbogen drückt die Flaschen in die Taschen (Mitte in Umfangsrichtung)
  - Öffnerstation hinten (+Y): Z-Achse (Schrittmotor, Trapezspindel TR8x2, Linearführung
    MGN12) mit Öffnerkopf: Hebel + Hakenleiste wie beim Handgerät, Linearantrieb 24 V statt
    Handkraft, gefederter Magnetstempel als Drehpunkt und Höhenfühler
  - Kronkorken-Abfuhr: Servo-Abstreifer schiebt den Kronkorken vom Magneten in einen
    mitfahrenden Trichter, Spiralschlauch zum Sammelbehälter mit Füllstands-Lichtschranke
  - Schutzhaube (Profil 20x20 + Polycarbonat) mit Klappe, Sicherheits-Türschalter,
    Bedienpult (Start/Stopp/Reset/Not-Halt), Signalsäule, Schaltkasten mit ESP32

Aufruf:  python erzeuge_automatik.py
"""
import base64
import json
import math
import struct
import sys
from pathlib import Path

import numpy as np

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER.parent))
import erzeuge_stl as M  # noqa: E402  (Grundkörper und Flaschendaten des Handgeräts)

rot, prisma, quader, zyl, stab = M.rot, M.prisma, M.quader, M.zyl, M.stab
ellipsoid, kugel, profil40 = M.ellipsoid, M.kugel, M.profil40


def drehe(t, achse, grad, um=(0, 0, 0)):
    a = math.radians(grad)
    c, s = math.cos(a), math.sin(a)
    R = {"x": [[1, 0, 0], [0, c, -s], [0, s, c]], "y": [[c, 0, s], [0, 1, 0], [-s, 0, c]],
         "z": [[c, -s, 0], [s, c, 0], [0, 0, 1]]}[achse]
    u = np.array(um, float)
    return (t - u) @ np.array(R).T + u

# ---------------------------------------------------------------- Hauptmaße
RAHMEN = (-300.0, 300.0, -260.0, 300.0)   # x0, x1, y0, y1
DECK = 88.0           # Oberkante Deckplatte (Rahmen 40x80 + 8 mm Platte)
Z0 = 94.0             # Standfläche der Flaschen (Gleitplatte 6 mm)
R_GLEIT = 230.0       # Gleitplatte (Scheibe)
N_TASCHEN = 8
R_SCHEITEL = 102.0    # Scheitel der 90°-Tasche; Flaschenmitte = R_SCHEITEL + r*sqrt(2)
R_STERN = 175.0       # Außenradius der Sternradscheiben
STERN_Z = ((15, 25), (95, 105))     # Sternradscheiben über Z0
YS = 150.0            # Öffnerstation: nominelle Flaschenmitte (Winkel 90°)
PX = 80.0             # Drehachse Hebel (x)
HY0, HY1 = -9.0, 3.0  # Hebel 30x12, relativ zu YS
SP_Y0, SP_Y1 = 6.0, 16.0            # Kopfplatte (Alu 10) relativ zu YS
SAEULE_Y0 = 29.0      # Säule relativ zu YS (hinter Führungsschiene MGN12)
SPINDEL = (118.0, 39.0)             # Trapezspindel x, y relativ
AKTOR_X = 230.0       # Angriffspunkt Linearantrieb am Hebel
HAUBE_Z = 660.0
REF = M.FLASCHEN[0]   # NRW 0,5 l


def zp_arbeit(H):
    """Drehachse in Arbeitsstellung: Hakenoberkante 1,5 mm unter dem Kronkorkenrand."""
    return Z0 + H + 9.0


ZP = zp_arbeit(REF[2])            # Modellstellung (363)
ZP_SICHER = 395.0                 # Hakenlippe über allen Kronkorken
ZP_ABSTREIF = 395.0               # Abstreifen in sicherer Höhe


def flaschen_r(D):
    return R_SCHEITEL + D / 2 * math.sqrt(2)


TEILE = []


def add(g, t, k="", teil=None, szene="maschine", inst=None):
    TEILE.append(dict(g=g, t=np.asarray(t, float), k=k, teil=teil, szene=szene, inst=inst))


def Y(y):
    """relativ zur Station -> absolut"""
    return YS + y


def profil20(achse, x0, y0, z0, laenge):
    return profil40(achse, 0, 0, 0, laenge) * ([0.5, 0.5, 1] if achse == "z" else
                                                [1, 0.5, 0.5] if achse == "x" else
                                                [0.5, 1, 0.5]) + [x0, y0, z0]


# ================================================================ Gestell
def gestell():
    x0, x1, y0, y1 = RAHMEN
    for y in (y0, y1 - 40):                                      # 40x80 längs X
        add("profil", profil40("x", x0, y, 0, x1 - x0))
        add("profil", profil40("x", x0, y, 40, x1 - x0))
    for x in (x0, x1 - 40):                                      # 40x80 längs Y
        add("profil", profil40("y", x, y0 + 40, 0, y1 - y0 - 80))
        add("profil", profil40("y", x, y0 + 40, 40, y1 - y0 - 80))
    for x in (x0 + 25, x1 - 25):
        for y in (y0 + 25, y1 - 25):
            add("gummi", zyl("z", (x, y, 0), -8, 0, 18))
    add("eigen", quader(x0, x1, y0, y1, 80, DECK), teil="A01_Deckplatte")
    add("kunststoff", rot([(R_GLEIT, DECK), (R_GLEIT, Z0)], "z", (0, 0, 0), 72), teil="A02_Gleitplatte")
    # Sternrad-Antrieb unter der Deckplatte: NEMA17, GT2 20Z -> 100Z
    add("normteil", rot([(14, 70), (14, 80), (11, 88)], "z", (0, 0, 0), 32))        # Flanschlager
    add("normteil", zyl("z", (0, 0, 0), 20, DECK + 150, 7.5, 28))                  # Welle Ø15
    add("normteil", zyl("z", (0, 0, 0), 56, 70, 32, 48))                           # Riemenscheibe 100Z
    add("normteil", quader(-21, 21, -111, -69, 8, 56))                             # Motor
    add("normteil", zyl("z", (0, -90, 0), 56, 70, 7, 20))                          # Riemenscheibe 20Z
    add("gummi", prisma([(-32, 0), (32, 0), (7, -90), (-7, -90)], "z", 60, 66))   # Zahnriemen (vereinf.)
    add("normteil", quader(-30, 30, -120, -60, 74, 80))                            # Motorhalter


def sternrad():
    """Zwei Scheiben mit 8 V-Taschen (90°, Scheitel innen), Nabe, Distanzrohre."""
    for (za, zb), nr in zip(STERN_Z, ("unten", "oben")):
        z0, z1 = Z0 + za, Z0 + zb
        add("kunststoff", zyl("z", (0, 0, 0), z0, z1, R_SCHEITEL, 64), "st", teil=f"A03_Sternrad_{nr}")
        for k in range(N_TASCHEN):
            a0 = math.radians(90 + k * 360 / N_TASCHEN)
            a1 = math.radians(90 + (k + 1) * 360 / N_TASCHEN)
            pts = [zahn_ecke(a0, +1)]
            pts += [(R_STERN * math.cos(a), R_STERN * math.sin(a))
                    for a in np.linspace(winkel_flanke(a0, +1), winkel_flanke(a1, -1), 8)]
            pts += [zahn_ecke(a1, -1)]
            pts = [(R_SCHEITEL * 0.98 * math.cos(a0), R_SCHEITEL * 0.98 * math.sin(a0))] + pts[1:-1] + \
                  [(R_SCHEITEL * 0.98 * math.cos(a1), R_SCHEITEL * 0.98 * math.sin(a1))]
            add("kunststoff", prisma(pts, "z", z0, z1), "st", teil=f"A03_Sternrad_{nr}")
    add("normteil", zyl("z", (0, 0, 0), Z0 + 10, Z0 + 110, 22, 32), "st")        # Nabe
    for k in range(4):
        a = math.radians(45 + 90 * k)
        add("normteil", zyl("z", (60 * math.cos(a), 60 * math.sin(a), 0), Z0 + 25, Z0 + 95, 6, 16), "st")
    # Referenzfahne für den Sternrad-Sensor
    add("normteil", zyl("z", (120, 0, 0), Z0 + 11, Z0 + 15, 5, 16), "st")


def _flanke(a, s):
    """Flankenrichtung der Tasche bei Winkel a (s = +1: Seite zum nächsten Zahn)."""
    return a + s * math.radians(45)


def zahn_ecke(a, s):
    return (R_SCHEITEL * math.cos(a), R_SCHEITEL * math.sin(a))


def winkel_flanke(a, s):
    """Winkel des Schnittpunkts Flanke/Außenkreis."""
    ax, ay = R_SCHEITEL * math.cos(a), R_SCHEITEL * math.sin(a)
    d = _flanke(a, s)
    dx, dy = math.cos(d), math.sin(d)
    b = ax * dx + ay * dy
    t = -b + math.sqrt(b * b - (R_SCHEITEL ** 2 - R_STERN ** 2))
    return math.atan2(ay + t * dy, ax + t * dx)


def fuehrung():
    """Gefederter Führungsbogen (vereinfacht: Federband + Halter), vorn offen zum Beladen."""
    z0, z1 = Z0 + 55, Z0 + 75
    a_start, a_ende = -60.0, 240.0
    n = 60
    for i in range(n):
        a0 = math.radians(a_start + (a_ende - a_start) * i / n)
        a1 = math.radians(a_start + (a_ende - a_start) * (i + 1) / n)
        pts = [(202 * math.cos(a0), 202 * math.sin(a0)), (202 * math.cos(a1), 202 * math.sin(a1)),
               (204 * math.cos(a1), 204 * math.sin(a1)), (204 * math.cos(a0), 204 * math.sin(a0))]
        add("normteil", prisma(pts, "z", z0, z1))
    for a in (-45, 0, 45, 135, 180, 225):
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        add("normteil", zyl("z", (222 * c, 222 * s, 0), DECK, z1, 5, 16))
        add("feder", stab((222 * c, 222 * s, (z0 + z1) / 2), (205 * c, 205 * s, (z0 + z1) / 2), 5, 5, 12))


# ================================================================ Z-Achse + Kopf
def z_achse():
    sx = 60.0
    sy = Y(SAEULE_Y0)
    add("profil", profil40("z", sx, sy, DECK, 432))
    add("normteil", quader(sx - 30, sx + 70, sy, sy + 40, DECK, DECK + 6))        # Fußplatte
    add("normteil", quader(74, 86, Y(21), Y(29), 120, 515))                        # Schiene MGN12
    xs, ys = SPINDEL
    add("normteil", quader(sx - 5, xs + 25, sy, Y(ys + 25), 520, 528))            # Motorplatte
    add("normteil", quader(xs - 21, xs + 21, Y(ys - 21), Y(ys + 21), 528, 576))   # NEMA17
    add("normteil", zyl("z", (xs, Y(ys), 0), 500, 520, 10, 20))                    # Kupplung
    add("normteil", zyl("z", (xs, Y(ys), 0), 160, 500, 4, 16))                     # TR8x2
    add("normteil", quader(xs - 15, xs + 15, Y(ys - 12), Y(ys + 12), 150, 162))   # Lagerbock
    add("normteil", quader(sx + 40, xs - 6, Y(ys - 8), Y(ys + 8), 150, 156))
    add("sensor", zyl("x", (0, Y(ys - 30), 505), 100, 112, 4, 16))                # Referenz Z oben


def kopf():
    """Öffnerkopf in Modellstellung ZP (Klasse 'z' bzw. 'h' für den Hebel)."""
    z = ZP
    k = "z"
    add("normteil", quader(67, 93, Y(16), Y(29), z - 22, z + 22), k)                # Laufwagen
    add("eigen", quader(50, 110, Y(SP_Y0), Y(SP_Y1), z - 60, z + 50), k, teil="A05_Kopfplatte")
    add("eigen", quader(110, 132, Y(SP_Y0), Y(52), z + 30, z + 40), k, teil="A06_Mutternhalter")
    add("normteil", zyl("z", (SPINDEL[0], Y(SPINDEL[1]), 0), z + 20, z + 45, 11, 24), k)
    # Stempelarm mit gefedertem Magnetstempel (Drehpunkt + Höhenfühler)
    add("eigen", quader(-14, 55, Y(5), Y(21), z + 4, z + 12), k, teil="A07_Stempelarm")
    add("eigen", quader(-14, 6, Y(-12), Y(21), z + 4, z + 12), k, teil="A07_Stempelarm")
    add("normteil", zyl("z", (0, YS, 0), z - 3, z + 4, 10, 28), k)                 # Führungsbuchse
    add("normteil", zyl("z", (0, YS, 0), z - 7, z - 2.5, 8, 28), k)                # Flachgreifer Ø16
    add("normteil", zyl("z", (0, YS, 0), z - 2.5, z + 22, 3, 12), k)               # Stößel
    add("feder", zyl("z", (0, YS, 0), z + 12, z + 20, 5.5, 16), k)
    add("sensor", zyl("z", (0, YS, 0), z + 26, z + 56, 4, 16), k)                  # Stempel-Sensor M8
    add("normteil", quader(-8, 8, Y(-6), Y(6), z + 24, z + 27), k)
    # Servo-Abstreifer
    add("elektro", quader(10, 30, Y(20), Y(60), z + 12, z + 48), k)                # Servo
    add("normteil", zyl("z", (20, Y(40), 0), z - 12, z + 12, 3, 12), k)            # Welle
    add("eigen", quader(-3, 3, Y(40), Y(110), z - 12, z - 8), "s", teil="A08_Abstreifer")
    # Trichter + Spiralschlauch zum Sammelbehälter
    tx, ty = -40.0, Y(-8)
    add("kunststoff", rot([(9, z - 42), (15, z - 16), (16.5, z - 16), (10.5, z - 42)], "z",
                          (tx, ty, 0), 28, ring=True), k, teil="A09_Trichter")
    add("eigen", quader(-26, -14, Y(-12), Y(4), z - 22, z + 4), k, teil="A09_Trichter")
    add("sensor", quader(tx - 16, tx + 16, ty - 4, ty + 4, z - 36, z - 30), k)     # Gabellichtschranke
    # Linearantrieb unter dem Hebelende (zieht nach unten)
    add("eigen", quader(94, 110, Y(SP_Y0 - 8), Y(SP_Y0), z - 160, z - 50), k, teil="A10_Aktorhalter")
    add("eigen", quader(94, 245, Y(HY0 - 2), Y(SP_Y0), z - 160, z - 152), k, teil="A10_Aktorhalter")
    add("aktor", quader(AKTOR_X - 14, AKTOR_X + 14, Y(-15), Y(9), z - 150, z - 45), k)  # Gehäuse
    add("normteil", zyl("z", (AKTOR_X, Y(-3), 0), z - 45, z - 15, 5, 16), "r")     # Kolbenstange


def hebel():
    z = ZP
    h = "h"
    add("eigen", quader(20, 245, Y(HY0), Y(HY1), z - 15, z + 15), h, teil="A11_Hebel")
    add("eigen", prisma([(13.4, z - 15), (48.4, z - 15), (48.4, z - 25), (19, z - 25)], "y",
                        Y(-20), Y(22)), h, teil="A12_Hakenleiste")
    add("normteil", zyl("y", (PX, 0, z), Y(HY0 - 11), Y(HY0 - 1), 8), h)
    add("kunststoff", zyl("y", (PX, 0, z), Y(HY0 - 1), Y(HY0), 9), h)
    add("normteil", zyl("y", (AKTOR_X, 0, z - 15), Y(HY0 - 3), Y(HY1 + 3), 4), h)  # Gabelkopfbolzen


# ================================================================ Abfuhr, Sensorik, Haube
def abfuhr_und_sensorik():
    # Sammelbehälter hinten links mit Einweg-Lichtschranke (Füllstand)
    add("kunststoff", quader(-290, -185, 185, 292, DECK, DECK + 150), teil="A13_Behaelter")
    add("sensor", zyl("y", (-280, 0, DECK + 135), 178, 186, 6, 16))
    add("sensor", zyl("y", (-195, 0, DECK + 135), 178, 186, 6, 16))
    # Flasche-in-Station: Reflexlichttaster M18
    add("normteil", quader(-75, -55, 195, 215, DECK, Z0 + 50))
    add("sensor", stab((-65, 205, Z0 + 55), (-50, 188, Z0 + 55), 9, 9, 20))
    # Sternrad-Referenz: induktiv M12 unter der Fahne
    add("sensor", zyl("z", (120, 0, 0), Z0 - 2, Z0 + 8, 6, 16))
    # Schaltkasten mit ESP32, Netzteil, Treibern, Sicherheitsrelais
    add("elektro", quader(140, 290, 228, 292, DECK, DECK + 200), teil=None)
    add("normteil", quader(150, 280, 226, 228, DECK + 10, DECK + 190))             # Tür
    for x in (160, 180, 200):
        add("normteil", zyl("z", (x, 260, 0), DECK + 200, DECK + 210, 6, 12))      # Kabelverschraubung


def schlauch_pfad(z):
    """Spiralschlauch vom Trichter (bewegt mit Kopf) zum Behälter."""
    p0 = np.array([-40.0, Y(-8), z - 42])
    p3 = np.array([-235.0, 235.0, DECK + 150])
    p1 = p0 + [0, 0, -60]
    p2 = p3 + [40, -10, 90]
    return [((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3
            for t in np.linspace(0, 1, 14)]


def schlauch():
    pts = schlauch_pfad(ZP)
    for a, b in zip(pts, pts[1:]):
        add("schlauch", stab(a, b, 11, 11, 14), "sl")


def haube():
    x0, x1, y0, y1 = RAHMEN
    xa, xb, ya, yb = x0 + 5, x1 - 25, y0, y1 - 20
    for x in (xa, xb):
        for y in (ya, yb):
            add("profil", profil20("z", x, y, DECK, HAUBE_Z - DECK))
    for y in (ya, yb):
        add("profil", profil20("x", xa, y, HAUBE_Z, xb - xa + 20))
    for x in (xa, xb):
        add("profil", profil20("y", x, ya, HAUBE_Z, yb - ya + 20))
    # Polycarbonat-Scheiben (Seiten, Rückwand, Dach) und Klappe vorn (Klasse 'd')
    add("haube", quader(xa, xa + 2, ya + 20, yb, DECK, HAUBE_Z))
    add("haube", quader(xb + 18, xb + 20, ya + 20, yb, DECK, HAUBE_Z))
    add("haube", quader(xa + 20, xb, yb + 18, yb + 20, DECK, HAUBE_Z))
    add("haube", quader(xa + 20, xb, ya + 20, yb, HAUBE_Z + 18, HAUBE_Z + 20))
    add("haube", quader(xa + 20, xb, ya - 3, ya - 1, DECK + 4, HAUBE_Z), "d")
    add("griff", quader(-60, 60, ya - 15, ya - 3, DECK + 60, DECK + 75), "d")       # Griffleiste
    for x in (-200, 200):
        add("normteil", zyl("x", (x, ya - 2, HAUBE_Z + 5), -20, 20, 6, 16))       # Scharniere
    # Sicherheits-Türschalter (EN ISO 14119) rechts oben
    add("sensor", quader(xb - 40, xb, ya - 12, ya, HAUBE_Z - 50, HAUBE_Z - 10))
    add("griff", quader(xb - 34, xb - 6, ya - 18, ya - 12, HAUBE_Z - 45, HAUBE_Z - 15), "d")
    # Bedienpult am rechten Pfosten
    px0, px1 = xb - 50, xb + 20
    add("elektro", quader(px0, px1, ya - 40, ya, DECK + 140, DECK + 260))
    for (x, z, g) in ((px0 + 18, DECK + 230, "lampe_gruen"), (px1 - 18, DECK + 230, "warn"),
                      (px0 + 18, DECK + 185, "lampe_blau")):
        add(g, zyl("y", (x, 0, z), ya - 46, ya - 40, 11, 24))
    add("lampe_gelb", zyl("y", (px1 - 18, 0, DECK + 180), ya - 43, ya - 40, 16, 28))
    add("warn", rot([(14, ya - 58), (14, ya - 52), (9, ya - 43)], "y", (px1 - 18, 0, DECK + 180), 28))
    # Signalsäule hinten links auf dem Dach
    sx, sy = xa + 30, yb - 10
    add("normteil", zyl("z", (sx, sy, 0), HAUBE_Z + 20, HAUBE_Z + 50, 6, 16))
    for i, g in enumerate(("lampe_gruen", "lampe_gelb", "warn")):
        add(g, zyl("z", (sx, sy, 0), HAUBE_Z + 50 + i * 26, HAUBE_Z + 74 + i * 26, 17, 28))
    add("normteil", zyl("z", (sx, sy, 0), HAUBE_Z + 128, HAUBE_Z + 134, 17, 28))


# ================================================================ Flaschen (Instanzen)
def flaschen_netze():
    """Je Flaschensorte ein Netz (Mitte x=y=0, Boden z=Z0) und ein Kronkorken-Netz."""
    netze = {}
    for fid, name, H, D, form in M.FLASCHEN:
        glas = rot(M.flasche_profil(H, D, form), "z", (0, 0, Z0), 32)
        etik = rot([(D / 2 - 0.1, 0.25 * H), (D / 2 + 0.6, 0.25 * H), (D / 2 + 0.6, 0.45 * H),
                    (D / 2 - 0.1, 0.45 * H)], "z", (0, 0, Z0), 32, ring=True)
        z0, z1 = Z0 + H - 4.5, Z0 + H + 1.5
        kork = np.concatenate([M.stern((0, 0), [14.4 if k % 2 == 0 else 14.9 for k in range(42)], z0, z1 - 1),
                               zyl("z", (0, 0, 0), z1 - 1, z1, 14.2, 42)])
        netze[fid] = (glas, etik, kork)
    return netze


# ================================================================ Szene
TISCH_Z = 750.0


def tisch_und_mensch():
    y0 = RAHMEN[2] - 80
    for x in range(-500, 900, 100):
        for y in range(int(y0), int(y0) + 800, 100):
            add("tischplatte", quader(x, x + 100, y, y + 100, TISCH_Z - 30, TISCH_Z), szene="tisch")
    for x in (-450, 790):
        for y in (y0 + 50, y0 + 690):
            add("tisch", quader(x, x + 60, y, y + 60, 0, TISCH_Z - 30), szene="tisch")
    start = (RAHMEN[1] - 25 - 50 + 18, RAHMEN[2] - 46, TISCH_Z + DECK + 230)
    links = (-150.0, -420.0, 830.0)
    vor = len(TEILE)
    M.TEILE.clear()
    M.mensch(X=60.0, Y=-470.0, hand_r=start, hand_l=links)
    for p in M.TEILE:
        add("mensch", p["t"], szene="mensch")
    M.TEILE.clear()
    return vor


# ================================================================ Ausgabe
def stl(pfad, teile, skala=1.0, versatz=(0, 0, 0)):
    tris = (np.concatenate([p["t"] for p in teile]) + np.array(versatz, float)) * skala
    nv = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(nv, axis=1, keepdims=True)
    nv = np.divide(nv, ln, out=np.zeros_like(nv), where=ln > 0)
    d = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", 9), ("a", "<u2")])
    d["n"], d["v"] = nv, tris.reshape(-1, 9)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "wb") as f:
        f.write(b"Flaschenoeffner Automatik TFO-A".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        f.write(d.tobytes())
    g = tris.reshape(-1, 3).max(0) - tris.reshape(-1, 3).min(0)
    print(f"  {str(pfad.relative_to(HIER)):44s} {len(tris):6d} Dreiecke  "
          f"{g[0]:6.1f} x {g[1]:6.1f} x {g[2]:6.1f} mm")


def b64(t):
    return base64.b64encode(np.asarray(t, "<f4").tobytes()).decode()


def vorschau(teile, netze):
    pakete = {}
    for p in teile:
        dz = TISCH_Z if p["szene"] == "maschine" else 0.0
        pakete.setdefault((p["g"], p["k"], p["szene"]), []).append(p["t"] + [0, 0, dz])
    daten = [{"g": g, "k": k, "s": s, "d": b64(np.concatenate(v))} for (g, k, s), v in pakete.items()]
    fl = []
    for fid, name, H, D, _ in M.FLASCHEN:
        glas, etik, kork = netze[fid]
        fl.append({"id": fid, "name": name, "H": H, "D": D, "r": flaschen_r(D),
                   "zp": zp_arbeit(H), "glas": b64(glas + [0, 0, TISCH_Z]),
                   "etikett": b64(etik + [0, 0, TISCH_Z]), "kork": b64(kork + [0, 0, TISCH_Z])})
    info = {"tisch": TISCH_Z, "zp_modell": ZP, "zp_sicher": ZP_SICHER, "ys": YS, "px": PX,
            "aktor_x": AKTOR_X, "n": N_TASCHEN, "abstreifer": [20, Y(40)],
            "trichter": [-40, Y(-8)], "behaelter": [-235, 235, DECK + 40],
            "schlauch_z": [DECK + 150, ZP - 42], "haube": [RAHMEN[2] - 2, HAUBE_Z + 5]}
    html = (HIER / "vorschau_vorlage.html").read_text(encoding="utf-8")
    html = (html.replace("/*DATEN*/[]", json.dumps(daten)).replace("/*FLASCHEN*/[]", json.dumps(fl))
                .replace("/*INFO*/{}", json.dumps(info)))
    (HIER / "vorschau_automatik.html").write_text(html, encoding="utf-8")


def aufbauen():
    TEILE.clear()
    gestell()
    sternrad()
    fuehrung()
    z_achse()
    kopf()
    hebel()
    abfuhr_und_sensorik()
    schlauch()
    haube()
    return TEILE


if __name__ == "__main__":
    aufbauen()
    netze = flaschen_netze()
    tisch_und_mensch()
    falsch = [p["g"] for p in TEILE if M.volumen(p["t"]) <= 0]
    print(f"{len(TEILE)} Einzelkörper, falsch orientiert: {len(falsch)} {falsch[:6]}")

    maschine = [p for p in TEILE if p["szene"] == "maschine"]
    ohne_haube = [p for p in maschine if p["g"] != "haube"]
    # Flaschen für die STL: 8 Taschen mit NRW 0,5 l
    glas, etik, kork = netze[REF[0]]
    fl = []
    for i in range(N_TASCHEN):
        a = math.radians(90 + i * 360 / N_TASCHEN)
        r = flaschen_r(REF[3])
        off = [r * math.cos(a), r * math.sin(a), 0]
        fl += [dict(t=glas + off), dict(t=kork + off)]
    print("Gesamtdateien:")
    stl(HIER / "TFO-A_1zu1_Maschine.stl", ohne_haube)
    stl(HIER / "TFO-A_1zu1_mit_Haube_und_Flaschen.stl", maschine + fl)
    szene = [dict(t=p["t"] + [0, 0, TISCH_Z]) for p in maschine + fl] + \
            [p for p in TEILE if p["szene"] in ("tisch", "mensch")]
    stl(HIER / "TFO-A_1zu1_Szene_mit_Mensch.stl", szene)
    stl(HIER / "TFO-A_1zu4_Druckmodell.stl", ohne_haube + fl, 0.25)
    print("Eigenfertigungsteile:")
    for n in sorted({p["teil"] for p in TEILE if p["teil"]}):
        tt = [p for p in TEILE if p["teil"] == n]
        mn = np.concatenate([p["t"] for p in tt]).reshape(-1, 3).min(0)
        stl(HIER / "teile" / f"{n}.stl", tt, versatz=-mn)
    vorschau(TEILE, netze)
    print("Vorschau: vorschau_automatik.html")
    print(f"Drehachse: Modell {ZP:.0f}, sicher {ZP_SICHER:.0f}, Bereich "
          f"{zp_arbeit(171.5):.1f} … {zp_arbeit(270):.1f}")
