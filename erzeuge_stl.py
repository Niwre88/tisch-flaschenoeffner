"""
Tisch-Flaschenöffner aus Normteilen – Generator für STL-Dateien und 3D-Vorschau.

Koordinaten der Maschine (Einheit mm):
  X = Breite (Bediener-rechts = +X), Y = Tiefe (Bediener steht bei -Y),
  Z = Höhe, Z = 0 ist die Tischoberfläche.
In der Szene steht der Tisch auf dem Boden, die Tischplatte liegt auf 750 mm.

Funktionsprinzip
  1. Die Flasche wird von vorn in ein 90°-Prisma geschoben und mit einem
     Schubstangenspanner gespannt. Das Prisma zentriert die Flasche in X;
     je nach Durchmesser verschiebt sie sich nur in Y.
  2. Beim Hineinschieben gleitet der Kronkorkenrand über die Hakenleiste, die
     genau in Y-Richtung liegt. Darum passt sie bei jedem Durchmesser.
  3. Der Bediener drückt den Kugelknopf nach unten. Die Hakenleiste geht
     hoch und hebt den Kronkorken ab, ein Magnet fängt ihn.
  4. Die Höhe des Schlittens wird für die Flaschensorte mit zwei
     Klemmhebeln eingestellt. Das Maßband zeigt direkt die Flaschenhöhe.

Flaschenmaße: VLB-Tabelle der Mehrweg-Standardpoolflaschen (Stand Jan. 2025).
Kronkorken: DIN EN 17177 (26 mm Mündung, Höhe 6 mm).

Nur Standardbibliothek + numpy.   Aufruf:  python erzeuge_stl.py
"""
import base64
import json
import math
import struct
from pathlib import Path

import numpy as np

AUSGABE = Path(__file__).parent
TEILE_ORDNER = AUSGABE / "teile"

# =====================================================================
# Grundkörper (geschlossene, nach außen orientierte Dreiecksnetze)
# =====================================================================


def _ccw(poly):
    f = sum(a0 * b1 - a1 * b0 for (a0, b0), (a1, b1) in zip(poly, poly[1:] + poly[:1]))
    return poly if f > 0 else poly[::-1]


def _abb(u, w, h, achse):
    if achse == "z":
        return (u, w, h)
    if achse == "x":
        return (h, u, w)
    return (w, h, u)  # y


def rot(profil, achse="z", mitte=(0, 0, 0), n=48, phase=0.0, ring=False):
    """Rotationskörper aus Profil [(radius, hoehe), ...]; n=6 -> Sechskant."""
    pts = [(float(r) if abs(r) > 1e-9 else 0.0, float(h)) for r, h in profil]
    if not ring:
        if pts[0][0] > 0:
            pts.insert(0, (0.0, pts[0][1]))
        if pts[-1][0] > 0:
            pts.append((0.0, pts[-1][1]))
    pts = _ccw(pts)
    cs = [(math.cos(math.radians(phase) + 2 * math.pi * k / n),
           math.sin(math.radians(phase) + 2 * math.pi * k / n)) for k in range(n)]
    t = []
    for i in range(len(pts)):
        (r0, h0), (r1, h1) = pts[i], pts[(i + 1) % len(pts)]
        if r0 == 0 and r1 == 0:
            continue
        for k in range(n):
            (c0, s0), (c1, s1) = cs[k], cs[(k + 1) % n]
            p00, p01 = _abb(r0 * c0, r0 * s0, h0, achse), _abb(r0 * c1, r0 * s1, h0, achse)
            p10, p11 = _abb(r1 * c0, r1 * s0, h1, achse), _abb(r1 * c1, r1 * s1, h1, achse)
            if r0 > 0:
                t.append((p00, p01, p11))
            if r1 > 0:
                t.append((p00, p11, p10))
    return np.array(t, float) + np.array(mitte, float)


def prisma(poly, achse, a0, a1):
    """Konvexes Polygon extrudiert.
    achse 'z': Polygon in (x, y) | 'x': in (y, z) | 'y': in (x, z)."""
    if achse == "y":
        poly = [(z, x) for x, z in poly]
    poly = _ccw([(float(p), float(q)) for p, q in poly])
    P = lambda p, q, h: _abb(p, q, h, achse)
    t = []
    for i in range(1, len(poly) - 1):
        (p0, q0), (p1, q1), (p2, q2) = poly[0], poly[i], poly[i + 1]
        t.append((P(p0, q0, a1), P(p1, q1, a1), P(p2, q2, a1)))
        t.append((P(p0, q0, a0), P(p2, q2, a0), P(p1, q1, a0)))
    for i in range(len(poly)):
        (pi, qi), (pj, qj) = poly[i], poly[(i + 1) % len(poly)]
        t.append((P(pi, qi, a0), P(pj, qj, a0), P(pj, qj, a1)))
        t.append((P(pi, qi, a0), P(pj, qj, a1), P(pi, qi, a1)))
    return np.array(t, float)


def quader(x0, x1, y0, y1, z0, z1):
    return prisma([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], "z", z0, z1)


def zyl(achse, mitte, a0, a1, r, n=32):
    return rot([(r, a0), (r, a1)], achse, mitte, n)


def stern(mitte, radien, z0, z1):
    """Sternförmiges Prisma (z. B. Kronkorken mit 21 Zacken), Fächer ab Mitte."""
    cx, cy = mitte
    n = len(radien)
    pts = [(cx + r * math.cos(2 * math.pi * k / n), cy + r * math.sin(2 * math.pi * k / n))
           for k, r in enumerate(radien)]
    t = []
    for k in range(n):
        (xa, ya), (xb, yb) = pts[k], pts[(k + 1) % n]
        t.append(((cx, cy, z1), (xa, ya, z1), (xb, yb, z1)))
        t.append(((cx, cy, z0), (xb, yb, z0), (xa, ya, z0)))
        t.append(((xa, ya, z0), (xb, yb, z0), (xb, yb, z1)))
        t.append(((xa, ya, z0), (xb, yb, z1), (xa, ya, z1)))
    return np.array(t, float)


def _ausrichten(d):
    z = np.array([0.0, 0.0, 1.0])
    c = float(np.dot(z, d))
    if c < -0.999999:
        return np.diag([1.0, -1.0, -1.0])
    v = np.cross(z, d)
    vx = np.array([[0, -v[2], v[1]], [v[2], 0, -v[0]], [-v[1], v[0], 0]])
    return np.eye(3) + vx + vx @ vx / (1 + c)


def stab(p0, p1, r0, r1=None, n=28):
    r1 = r0 if r1 is None else r1
    p0, p1 = np.array(p0, float), np.array(p1, float)
    d = p1 - p0
    L = np.linalg.norm(d)
    return rot([(r0, 0), (r1, L)], "z", (0, 0, 0), n) @ _ausrichten(d / L).T + p0


def ellipsoid(m, rx, ry, rz, n=32, k=16):
    prof = [(math.sin(math.pi * i / k), -math.cos(math.pi * i / k)) for i in range(k + 1)]
    return rot(prof, "z", (0, 0, 0), n) * [rx, ry, rz] + np.array(m, float)


def kugel(m, r, n=28):
    return ellipsoid(m, r, r, r, n, n // 2)


def profil40(achse, x0, y0, z0, laenge):
    """Alu-Systemprofil 40x40, Nut 8 (vereinfacht: Kern + 4 Ecken, Nuttiefe 12).
    (x0, y0, z0) = Ecke mit kleinsten Koordinaten."""
    t = []
    for a0, a1, b0, b1 in ((0, 16, 0, 16), (24, 40, 0, 16), (0, 16, 24, 40),
                           (24, 40, 24, 40), (12, 28, 12, 28)):
        if achse == "z":
            t.append(quader(x0 + a0, x0 + a1, y0 + b0, y0 + b1, z0, z0 + laenge))
        elif achse == "y":
            t.append(quader(x0 + a0, x0 + a1, y0, y0 + laenge, z0 + b0, z0 + b1))
        else:
            t.append(quader(x0, x0 + laenge, y0 + a0, y0 + a1, z0 + b0, z0 + b1))
    return np.concatenate(t)


def volumen(t):
    return float(np.einsum("ij,ij->i", t[:, 0], np.cross(t[:, 1], t[:, 2])).sum() / 6)


# =====================================================================
# Teileverwaltung
#   gruppe : Farbe/Kategorie (profil, normteil, eigen, druck, gummi, ...)
#   klasse : Bewegung in der Vorschau
#            ""  fest | "s" Schlitten (Höhe) | "h" Hebel (Höhe + Drehung)
#            "k" Spannerstange (Y)  | "c" Kronkorken (dreht mit Hebel)
#   teil   : Name für Einzel-STL (Eigenfertigung) | flasche : Flaschen-ID
# =====================================================================

TEILE = []


def add(gruppe, t, klasse="", teil=None, flasche=None, szene="maschine"):
    TEILE.append(dict(g=gruppe, t=np.asarray(t, float), k=klasse,
                      teil=teil, f=flasche, szene=szene))


# ---------------------------------------------------------------------
# Flaschen (VLB-Tabelle, nur Kronkorken-Flaschen)
# ---------------------------------------------------------------------
FLASCHEN = [
    # id,       Name,               Höhe,  Ø,    Form
    ("nrw05",   "NRW 0,5 l",        260.0, 67.5, "nrw"),
    ("lgn05",   "Longneck 0,5 l",   270.0, 68.5, "lgn"),
    ("euro05",  "Euro 0,5 l",       228.0, 70.5, "euro"),
    ("stein05", "Steinie 0,5 l",    197.0, 79.0, "stein"),
    ("lgn033",  "Longneck 0,33 l",  238.0, 61.0, "lgn"),
    ("vichy",   "Vichy 0,33 l",     233.0, 61.0, "vichy"),
    ("euro033", "Euro 0,33 l",      190.0, 63.0, "euro"),
    ("stein033", "Steinie 0,33 l",  174.0, 70.0, "stein"),
    ("euro025", "Euro 0,25 l",      171.5, 59.5, "euro"),
]
REF = FLASCHEN[0]   # Bezugsflasche für die Grundstellung: NRW 0,5 l

# ---------------------------------------------------------------------
# Hauptmaße der Maschine
# ---------------------------------------------------------------------
PL_U, PL_O = 10.0, 22.0       # Grundplatte (Alu 12 mm) auf Gerätefüßen 10 mm
STAND = 25.0                  # Standfläche Flasche (Gummimatte 3 mm)
Y_APEX = 48.0                 # Scheitel des 90°-Prismas
SPANN_Z = 73.0                # Höhe der Spannerachse
PX = 80.0                     # X der Drehachse (= Mitte Säule)
HY0, HY1 = -7.0, 1.0          # Hebel Flachstahl 30x8 liegt in Y -7..1
KNOPF_X = 370.0               # Kugelknopf
HEBEL_X0 = 20.0               # linkes Hebelende (5 mm Abstand zum Kronkorken)
EINLEGE_Y = -26.0             # Flaschenmitte beim Hinstellen (Kronkorken frei vom Haken)
SPANNER_HUB = 40.0            # Hub des Schubstangenspanners
SAEULE = (60.0, 15.0)         # Ecke der Säule (x, y), Profil 40x40


def drehachse_z(H):
    """Höhe der Drehachse über Tisch für Flaschenhöhe H.
    Kronkorken-Unterkante = STAND + H - 4.5; Hakenoberkante 1,5 mm darunter;
    Haken liegt 15 mm unter der Hebelmitte."""
    return STAND + H - 4.5 - 1.5 + 15.0      # = H + 34


def flaschen_y(D):
    """Flaschenmitte in Y: Prisma 90° -> Abstand Mitte-Scheitel = r * sqrt(2)."""
    return Y_APEX - D / 2 * math.sqrt(2)


ZP = drehachse_z(REF[2])        # Drehachse in Grundstellung (295 mm)


def grundgestell():
    # Gerätefüße (Gummi, M6) und Grundplatte
    for x in (-75, 130):
        for y in (-125, 80):
            add("gummi", zyl("z", (x, y, 0), 0, PL_U, 15))
    add("eigen", quader(-95, 150, -145, 100, PL_U, PL_O), teil="01_Grundplatte")
    add("gummi", quader(-45, 45, -75, 10, PL_O, STAND))           # Gummimatte

    # 90°-Prisma aus zwei Backen (3D-Druck PETG oder Alu)
    s = 37.0
    for sx in (-1, 1):
        poly = [(0, Y_APEX), (sx * s, Y_APEX - s), (sx * 55, Y_APEX - s),
                (sx * 55, 88), (0, 88)]
        add("druck", prisma(poly, "z", PL_O, 88), teil="07_Prisma_Backe_" + ("links" if sx < 0 else "rechts"))
        # Gummistreifen auf den Prismaflächen
        a, b = (sx * 4, Y_APEX - 4), (sx * (s - 2), Y_APEX - s + 2)
        n = np.array([sx * 1, 1]) / math.sqrt(2) * 2    # Dicke 2 mm nach außen
        add("gummi", prisma([a, b, (b[0] - n[0], b[1] - n[1]), (a[0] - n[0], a[1] - n[1])],
                            "z", 40, 80))

    # Säule: Systemprofil 40x40 Nut 8, L = 400, mit Abdeckkappe
    sx0, sy0 = SAEULE
    add("profil", profil40("z", sx0, sy0, PL_O, 400))
    add("gummi", quader(sx0, sx0 + 40, sy0, sy0 + 40, PL_O + 400, PL_O + 404))
    # 2 Winkel 40x40 (Profilsystem) + Schrauben
    add("normteil", quader(sx0 + 40, sx0 + 44, sy0 + 4, sy0 + 36, PL_O, PL_O + 40))
    add("normteil", quader(sx0 + 40, sx0 + 80, sy0 + 4, sy0 + 36, PL_O, PL_O + 4))
    add("normteil", quader(sx0 + 4, sx0 + 36, sy0 + 40, sy0 + 44, PL_O, PL_O + 40))
    add("normteil", quader(sx0 + 4, sx0 + 36, sy0 + 40, sy0 + 80, PL_O, PL_O + 4))
    for x, y in ((sx0 + 62, sy0 + 20), (sx0 + 20, sy0 + 62)):
        add("normteil", rot([(6.5, PL_O + 4), (6.5, PL_O + 9)], "z", (x, y, 0), 6))
    # Maßband an der Säulen-Außenseite (+X), Nullpunkt um 34 mm versetzt,
    # damit der Zeiger direkt die Flaschenhöhe anzeigt
    xs = sx0 + 40
    add("skala", quader(xs, xs + 0.6, sy0 + 22, sy0 + 38, 150, 410))
    for h in range(140, 290, 10):
        z = h + 34
        lang = 9 if h % 50 == 0 else 5
        add("normteil", quader(xs + 0.5, xs + 0.9, sy0 + 38 - lang, sy0 + 38, z - 0.6, z + 0.6))

    # Schubstangenspanner auf Profil-Stück 40x40 L=60 (Normteil)
    add("profil", profil40("y", -20, -140, PL_O, 60))
    add("normteil", quader(-14, 14, -140, -84, PL_O + 40, PL_O + 46))     # Fußplatte
    add("normteil", quader(-10, 10, -138, -86, PL_O + 46, SPANN_Z + 10))  # Gehäuse
    add("normteil", zyl("y", (0, 0, SPANN_Z), -86, -72, 8))               # Führung
    add("normteil", stab((0, -132, SPANN_Z + 8), (0, -172, PL_O + 150), 6))  # Handhebel
    add("griff", stab((0, -172, PL_O + 150), (0, -178, PL_O + 182), 11, 9))  # Griff
    for x in (-8, 8):
        add("normteil", stab((x, -100, SPANN_Z + 10), (x, -130, SPANN_Z + 22), 3))  # Lasche


def spanner_stange():
    """Bewegliche Schubstange mit Druckschraube M8 und Gummikappe (Grundstellung)."""
    vorne = flaschen_y(REF[3]) - REF[3] / 2           # Anlagepunkt an der Flasche
    add("normteil", zyl("y", (0, 0, SPANN_Z), -150, -80, 6), "k")
    add("normteil", zyl("y", (0, 0, SPANN_Z), vorne - 70, vorne - 10, 4), "k")
    add("normteil", rot([(7.5, vorne - 30), (7.5, vorne - 24)], "y", (0, 0, SPANN_Z), 6), "k")
    add("gummi", rot([(9, vorne - 12), (11, vorne - 10), (11, vorne - 2), (9, vorne)],
                     "y", (0, 0, SPANN_Z), 28), "k")


def schlitten():
    """Höhenverstellbarer Schlitten (Klasse 's'), Grundstellung für REF."""
    z = ZP
    s = "s"
    add("eigen", quader(50, 110, 5, 15, z - 60, z + 50), s, teil="02_Schlittenplatte")
    add("normteil", quader(76, 84, 15, 20, z - 60, z + 50), s)       # Passfeder DIN 6885 8x7
    for zk in (z + 35, z - 45):                                      # Klemmhebel M8 (Kipp-Stil)
        add("normteil", zyl("y", (PX, 0, zk), -6, 5, 11), s)
        add("griff", stab((PX, -6, zk), (PX + 34, -10, zk + 14), 5, 4), s)
        add("griff", kugel((PX + 34, -10, zk + 14), 7), s)
    # Zeiger fürs Maßband: liegt auf Höhe der Drehachse. Die Skala ist um
    # 34 mm versetzt aufgeklebt, daher zeigt er direkt die Flaschenhöhe an.
    add("eigen", quader(101, 104, 15, 50, z - 5, z + 5), s, teil="06_Zeiger")
    add("eigen", quader(101, 110, 5, 15, z - 5, z + 5), s, teil="06_Zeiger")
    add("warn", quader(104, 105, 36, 54, z - 0.6, z + 0.6), s)
    # Federhalter (Flachstahl-Winkel) mit Zugfeder und verstellbarem Gummipuffer
    add("eigen", quader(95, 111, -1, 5, z + 22, z + 81), s, teil="05_Federhalter")
    add("eigen", quader(95, 175, -12, 5, z + 75, z + 81), s, teil="05_Federhalter")
    add("normteil", zyl("z", (130, -3, 0), z + 30, z + 88, 3), s)        # Gewindestange M6
    for zz in (z + 81, z + 70):
        add("normteil", rot([(5.5, zz), (5.5, zz + 5)], "z", (130, -3, 0), 6), s)
    add("gummi", zyl("z", (130, -3, 0), z + 15, z + 30, 10), s)          # Anschlagpuffer
    add("feder", zyl("z", (162, -3, 0), z + 12, z + 70, 1.0), s)       # Ösen-Draht
    add("feder", zyl("z", (162, -3, 0), z + 24, z + 70, 5), s)
    for zz in np.arange(z + 26, z + 68, 3.2):
        add("feder", rot([(4.5, zz), (7, zz), (7, zz + 1.8), (4.5, zz + 1.8)], "z",
                         (162, -3, 0), 16, ring=True), s)
    add("feder", rot([(3, z + 70), (6, z + 70), (6, z + 75), (3, z + 75)], "z", (162, -3, 0), 16, ring=True), s)


def hebel():
    """Zweiseitiger Hebel mit Haken, Magnet und Kugelknopf (Klasse 'h')."""
    z = ZP
    h = "h"
    add("eigen", quader(HEBEL_X0, KNOPF_X + 15, HY0, HY1, z - 15, z + 15), h, teil="03_Hebel")
    # Hakenleiste: Flachstahl 40x10, Lippe mit Fase; Langlöcher im Hebel zum Nachstellen
    add("eigen", prisma([(13.4, z - 15), (48.4, z - 15), (48.4, z - 25), (19, z - 25)],
                        "y", -18, 17), h, teil="04_Hakenleiste")
    for x in (28, 40):
        add("normteil", zyl("z", (x, -3, 0), z + 15, z + 16, 4.5), h)    # Senkschrauben M5
    # Magnethalter + Flachgreifer-Topfmagnet Ø16
    add("eigen", quader(-12, 66, HY0 - 5, HY0, z - 1.5, z + 18.5), h, teil="08_Magnethalter")
    add("normteil", zyl("z", (0, HY0 - 2.5, 0), z - 6, z - 1.5, 8), h)
    for x in (50, 60):
        add("normteil", zyl("y", (x, 0, z + 9), HY0 - 7, HY0 - 5, 4.5), h)
    # Drehpunkt: Passschraube ISO 7379 Ø10 + 2 Bundbuchsen iglidur
    add("normteil", zyl("y", (PX, 0, z), HY0 - 10, HY0, 8), h)
    add("normteil", rot([(6, HY0 - 10.01), (6, HY0 - 7)], "y", (PX, 0, z), 6), h)
    add("kunststoff", zyl("y", (PX, 0, z), HY0 - 1.5, HY0, 9), h)
    add("kunststoff", zyl("y", (PX, 0, z), HY1, HY1 + 4, 9), h)
    # Federöse greift in Bohrung Ø5 im Hebel (7 mm unter Oberkante)
    add("feder", rot([(4, -4.5), (5.5, -4.5), (5.5, 4.5), (4, 4.5)], "y", (162, -3, z + 8), 16,
                     ring=True), h)
    # Kugelknopf DIN 319 Ø40 auf Stiftschraube M10
    add("normteil", zyl("z", (KNOPF_X, -3, 0), z + 15, z + 22, 5), h)
    add("griff", rot([(9, z + 20), (12, z + 22)] +
                     [(20 * math.sin(a), z + 40 - 20 * math.cos(a))
                      for a in np.linspace(0.65, math.pi, 12)], "z", (KNOPF_X, -3, 0), 32), h)


def flasche_profil(H, D, form):
    R = D / 2
    hb, hs, rn = {"nrw": (0.52, 0.80, 13.0), "lgn": (0.50, 0.64, 12.8),
                  "euro": (0.55, 0.80, 13.2), "stein": (0.60, 0.82, 16.0),
                  "vichy": (0.45, 0.70, 13.0)}[form]
    p = [(R - 3, 0), (R, 4), (R, hb * H)]
    for i in range(1, 11):
        t = i / 10
        s = t * t * (3 - 2 * t)
        p.append((R + (rn - R) * s, hb * H + (hs - hb) * H * t))
    p += [(rn, H - 16), (12.5, H - 9), (13.15, H - 7), (13.15, H)]
    return p


def flaschen():
    for fid, name, H, D, form in FLASCHEN:
        yc = flaschen_y(D)
        add("glas", rot(flasche_profil(H, D, form), "z", (0, yc, STAND), 48), flasche=fid)
        add("etikett", rot([(D / 2 - 0.1, 0.25 * H), (D / 2 + 0.6, 0.25 * H),
                            (D / 2 + 0.6, 0.45 * H), (D / 2 - 0.1, 0.45 * H)], "z",
                           (0, yc, STAND), 48, ring=True), flasche=fid)
        z0, z1 = STAND + H - 4.5, STAND + H + 1.5
        add("kronkorken", stern((0, yc), [14.4 if k % 2 == 0 else 14.9 for k in range(42)],
                                z0, z1 - 1.0), "c", flasche=fid)
        add("kronkorken", zyl("z", (0, yc, 0), z1 - 1.0, z1, 14.2, 42), "c", flasche=fid)


# ---------------------------------------------------------------------
# Szene: Tisch + Mensch (nur zur Veranschaulichung)
# ---------------------------------------------------------------------
TISCH_Z = 750.0
TISCH_Y0 = -240.0       # Vorderkante Tisch


def tisch():
    # Tischplatte in 100-mm-Felder unterteilt (bessere Tiefensortierung in der Vorschau)
    # Die Vorschau blendet die senkrechten Flächen der Felder aus ("tischplatte");
    # die Plattenkante bilden schmale Randleisten in 100-mm-Stücken.
    y0, y1 = int(TISCH_Y0), int(TISCH_Y0) + 800
    for x in range(-500, 900, 100):
        for y in range(y0, y1, 100):
            add("tischplatte", quader(x, x + 100, y, y + 100, TISCH_Z - 30, TISCH_Z), szene="tisch")
        for yy in (y0, y1 - 1):
            add("tisch", quader(x, x + 100, yy, yy + 1, TISCH_Z - 30, TISCH_Z - 0.5), szene="tisch")
    for y in range(y0, y1, 100):
        for xx in (-500, 899):
            add("tisch", quader(xx, xx + 1, y, y + 100, TISCH_Z - 30, TISCH_Z - 0.5), szene="tisch")
    for x in (-450, 790):
        for y in (TISCH_Y0 + 50, TISCH_Y0 + 690):
            add("tisch", quader(x, x + 60, y, y + 60, 0, TISCH_Z - 30), szene="tisch")


def mensch(X=200.0, Y=-400.0, hand_r=None, hand_l=None):
    """Stilisierte Person, ca. 1,76 m, Hände an Kugelknopf und Spanner."""
    for sx in (-1, 1):
        x = X + sx * 105
        add("mensch", prisma([(Y - 70, 0), (Y + 200, 0), (Y + 200, 30), (Y + 150, 70),
                              (Y - 70, 80)], "x", x - 48, x + 48), szene="mensch")
        knoechel, knie, huefte = (x, Y, 85), (X + sx * 100, Y + 12, 498), (X + sx * 92, Y, 908)
        add("mensch", stab(knoechel, knie, 46, 60), szene="mensch")
        add("mensch", kugel(knie, 60), szene="mensch")
        add("mensch", stab(knie, huefte, 62, 84), szene="mensch")
    add("mensch", ellipsoid((X, Y, 943), 175, 112, 125), szene="mensch")
    add("mensch", ellipsoid((X, Y, 1113), 158, 108, 155), szene="mensch")
    add("mensch", ellipsoid((X, Y + 5, 1308), 195, 122, 200), szene="mensch")
    add("mensch", stab((X, Y, 1478), (X, Y + 6, 1573), 50, 44), szene="mensch")
    add("mensch", ellipsoid((X, Y + 15, 1646), 82, 98, 112), szene="mensch")
    L1, L2 = 320.0, 300.0
    for sx, H in ((1, hand_r), (-1, hand_l)):
        S = np.array([X + sx * 188, Y + 5, 1418.0])
        H = np.array(H, float)
        d = H - S
        dist = np.linalg.norm(d)
        u = d / dist
        a = (L1 ** 2 - L2 ** 2 + dist ** 2) / (2 * dist)
        h = math.sqrt(max(L1 ** 2 - a ** 2, 0))
        pref = np.array([sx * 0.7, -0.2, -1.0])
        nv = pref - np.dot(pref, u) * u
        nv /= np.linalg.norm(nv)
        E = S + a * u + h * nv
        for t in (kugel(S, 58), stab(S, E, 50, 42), kugel(E, 42), stab(E, H, 40, 32),
                  ellipsoid(H, 42, 50, 40)):
            add("mensch", t, szene="mensch")


# =====================================================================
# Ausgabe
# =====================================================================

def stl(pfad, teile, skala=1.0, versatz=(0, 0, 0)):
    tris = (np.concatenate([p["t"] for p in teile]) + np.array(versatz, float)) * skala
    nv = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(nv, axis=1, keepdims=True)
    nv = np.divide(nv, ln, out=np.zeros_like(nv), where=ln > 0)
    d = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", 9), ("a", "<u2")])
    d["n"], d["v"] = nv, tris.reshape(-1, 9)
    pfad.parent.mkdir(exist_ok=True)
    with open(pfad, "wb") as f:
        f.write(b"Tisch-Flaschenoeffner".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        f.write(d.tobytes())
    g = tris.reshape(-1, 3).max(0) - tris.reshape(-1, 3).min(0)
    print(f"  {str(pfad.relative_to(AUSGABE)):46s} {len(tris):6d} Dreiecke  "
          f"{g[0]:6.1f} x {g[1]:6.1f} x {g[2]:6.1f} mm")


def vorschau(teile):
    pakete = {}
    for p in teile:
        dz = TISCH_Z if p["szene"] == "maschine" else 0.0
        key = (p["g"], p["k"], p["f"] or "", p["szene"])
        pakete.setdefault(key, []).append(p["t"] + [0, 0, dz])
    daten = [{"g": g, "k": k, "f": f, "s": s,
              "d": base64.b64encode(np.concatenate(v).astype("<f4").tobytes()).decode()}
             for (g, k, f, s), v in pakete.items()]
    ref_vorne = flaschen_y(REF[3]) - REF[3] / 2
    meta = [{"id": fid, "name": name, "H": H, "D": D,
             "dz": drehachse_z(H) - ZP,
             "dy": (flaschen_y(D) - D / 2) - ref_vorne,
             "zp": drehachse_z(H), "yc": flaschen_y(D)} for fid, name, H, D, _ in FLASCHEN]
    info = {"pivot": [PX, 0, ZP + TISCH_Z], "tisch": TISCH_Z, "knopf": ZP + 40,
            "einlege_y": EINLEGE_Y, "hub": SPANNER_HUB, "ref_vorne": ref_vorne}
    html = (AUSGABE / "vorschau_vorlage.html").read_text(encoding="utf-8")
    html = (html.replace("/*DATEN*/[]", json.dumps(daten))
                .replace("/*FLASCHEN*/[]", json.dumps(meta))
                .replace("/*INFO*/{}", json.dumps(info)))
    (AUSGABE / "vorschau.html").write_text(html, encoding="utf-8")


if __name__ == "__main__":
    grundgestell()
    spanner_stange()
    schlitten()
    hebel()
    flaschen()
    tisch()
    knopf = (KNOPF_X, -3, TISCH_Z + ZP + 58)
    spanngriff = (0, -176, TISCH_Z + PL_O + 172)
    mensch(hand_r=knopf, hand_l=spanngriff)

    falsch = [p["g"] for p in TEILE if volumen(p["t"]) <= 0]
    print(f"{len(TEILE)} Einzelkörper, falsch orientiert: {len(falsch)} {falsch[:5]}")

    maschine = [p for p in TEILE if p["szene"] == "maschine" and p["f"] is None]
    ref_fl = [p for p in TEILE if p["f"] == REF[0]]
    tisch_t = [p for p in TEILE if p["szene"] == "tisch"]
    mensch_t = [p for p in TEILE if p["szene"] == "mensch"]

    print("Gesamtdateien:")
    stl(AUSGABE / "Flaschenoeffner_1zu1_ohne_Flasche.stl", maschine)
    stl(AUSGABE / "Flaschenoeffner_1zu1_mit_Flasche.stl", maschine + ref_fl)
    # Szene: Maschine auf Tischhöhe anheben
    szene = [dict(p, t=p["t"] + [0, 0, TISCH_Z]) for p in maschine + ref_fl] + tisch_t + mensch_t
    stl(AUSGABE / "Flaschenoeffner_1zu1_Szene_mit_Mensch.stl", szene)
    stl(AUSGABE / "Mensch_Referenz_1zu1.stl", mensch_t)
    stl(AUSGABE / "Flaschenoeffner_1zu3_Druckmodell.stl", maschine + ref_fl, 1 / 3)

    print("Eigenfertigungsteile (Ordner teile/, jeweils auf Nullpunkt verschoben):")
    namen = sorted({p["teil"] for p in TEILE if p["teil"]})
    for n in namen:
        tt = [p for p in TEILE if p["teil"] == n]
        mn = np.concatenate([p["t"] for p in tt]).reshape(-1, 3).min(0)
        stl(TEILE_ORDNER / f"{n}.stl", tt, versatz=-mn)

    vorschau(TEILE)
    print("Vorschau: vorschau.html")
    print(f"Drehachse Grundstellung (NRW 0,5 l): {ZP:.0f} mm über Tisch")
    for fid, name, H, D, _ in FLASCHEN:
        print(f"  {name:17s} H={H:6.1f} D={D:5.1f}  Achse {drehachse_z(H):6.1f}  "
              f"Flaschenmitte y={flaschen_y(D):5.1f}  Spanner-Anlage y={flaschen_y(D) - D / 2:6.1f}")
