"""
Kollisions- und Konsistenzprüfung TFO-A, Index C (exakte Volumenkörper aus modell_c.py).

Schema: jedes bewegte Teil an beiden Enden und dazwischen, jede Flaschensorte (12).
  K1  Takten: Kopf in Abwurfhöhe, Fangrinne geparkt, Flaschen auf dem ganzen Umlauf
  K2  Arbeitsstellung: Kopf aufgesetzt, Backen offen und zu, je Sorte (Flasche mit Kronkorken)
  K3  Kippen 0 … 25° mit geschlossenen Backen: Kopf gegen Glas (ohne Kronkorken)
  K4  Hubweg Kopf (tiefste Arbeitshöhe … Abwurfhöhe) gegen alle festen Teile und die geparkte Rinne
  K5  Fangrinne 0 … 119,5° gegen feste Teile, Kopf in Abwurfhöhe und alle Flaschen
  K6  Nachbartaschen gegen Kopf in Arbeitsstellung (offen, zu, gekippt)
  K7  Geländer je Sorte eingestellt: Flasche liegt an, ohne Überschneidung
  K8  Sternrad und Flaschen gegen feste Teile, Geländer jeweils auf die Sorte eingestellt
  K9  Konsistenz: Rinne über allen Kronkorken, Abwurf, Neigungen, Greifgeometrie
  K10 Kopf intern: Greiferschwinge und Backen gegen Kopfrahmen in allen Stellungen

Aufruf:  python pruefe_kollisionen.py
"""
import math
import sys
import time
from pathlib import Path

from cadquery import Vector as V

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
import modell_c as A  # noqa: E402

TOL = 0.5  # mm³
BEFUNDE = []


def schnitt(a, b):
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
            or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
        return 0.0
    try:
        return a.intersect(b).Volume()
    except Exception:
        return -1.0


def melde(k, text):
    BEFUNDE.append((k, text))
    print(f"  [{k}] {text}")


def main():
    t_start = time.time()
    A.aufbauen()
    kopf = [t for t in A.TEILE if t.klasse in A.KOPF_KLASSEN]
    schwinge = [t for t in A.TEILE if t.klasse in A.SCHWINGE_KLASSEN]
    rahmen = [t for t in A.TEILE if t.klasse == "z"]
    rinne = [t for t in A.TEILE if t.klasse == "f"]
    gel_fmt = ("A16_", "A18_", "Klemmhebel", "Druckfeder_Gel")      # vom Format abhängig
    fest = [t for t in A.TEILE if t.klasse == "" and not t.name.startswith(gel_fmt)]
    stern = [t for t in A.TEILE if t.klasse == "st"]
    sorten = [(fid, name, H, D) for fid, name, H, D, _ in A.FLASCHEN]
    voll = {fid: A.flasche_voll(fid) for fid, *_ in sorten}
    glas = {fid: A.glas_voll(fid) for fid, *_ in sorten}

    def bei(s, D, winkel_grad, versatz=0.0):
        x, y = A.tasche(0, D, versatz, winkel_grad - 90)
        return s.translate(V(x, y, 0))

    def kopf_lage(zk, kipp=0.0, greif=1.0):
        return [(t.name, A.lage(t, zk=zk, kipp=kipp, greif=greif)) for t in kopf]

    print("K1 Takten (Kopf in Abwurfhöhe, Rinne geparkt) – Flaschen auf dem Umlauf")
    hindernis = kopf_lage(A.ZK_ABWURF, greif=0.0) + [(t.name, t.form) for t in rinne]
    for fid, name, H, D in sorten:
        treffer = None
        for w10 in range(0, 3600, 75):
            fl = bei(voll[fid], D, w10 / 10)
            for n, k in hindernis:
                v = schnitt(fl, k)
                if v > TOL:
                    treffer = (w10 / 10, n, v)
                    break
            if treffer:
                break
        if treffer:
            melde("K1", f"{name}: berührt {treffer[1]} bei {treffer[0]:.1f}° ({treffer[2]:.0f} mm³)")

    print("K2 Arbeitsstellung (Kopf aufgesetzt, Backen offen und zu)")
    for fid, name, H, D in sorten:
        fl = bei(voll[fid], D, 90)
        for g in (0.0, 1.0):
            for n, k in kopf_lage(A.zk_arbeit(H), greif=g):
                v = schnitt(fl, k)
                if v > TOL:
                    melde("K2", f"{name} (Backen {'zu' if g else 'offen'}): {n} ({v:.0f} mm³)")

    print("K3 Kippen 0 … 25°: Kopf gegen Glas")
    for fid, name, H, D in sorten:
        g_ = bei(glas[fid], D, 90)
        for w in (0, 5, 10, 15, 20, 25):
            for t in kopf:
                v = schnitt(g_, A.lage(t, zk=A.zk_arbeit(H), kipp=w, greif=1.0))
                if v > TOL:
                    melde("K3", f"{name}: {t.name} trifft Glas bei {w}° ({v:.0f} mm³)")

    print("K4 Hubweg des Kopfes gegen feste Teile")
    gemeldet = set()
    zk = A.ZK_MIN
    feste_k4 = fest + [t for t in A.TEILE if t.klasse == "" and t.name.startswith(gel_fmt)] + rinne
    while zk <= A.ZK_ABWURF + 0.1:
        for t in kopf:
            k = A.lage(t, zk=zk, greif=0.0)
            for f in feste_k4:
                if (t.name, f.name) in gemeldet:
                    continue
                if t.name.startswith("Fuehrungswagen") and f.name.startswith("Linearfuehrung"):
                    continue
                if t.name.startswith("Spindelmutter") and f.name.startswith("Trapez"):
                    continue
                v = schnitt(k, f.form)
                if v > TOL:
                    gemeldet.add((t.name, f.name))
                    melde("K4", f"{t.name} trifft {f.name} bei ZK {zk:.0f} mm ({v:.0f} mm³)")
        zk += 10

    print(f"K5 Fangrinne 0 … {A.RINNE_WINKEL:.1f}° (Kopf in Abwurfhöhe, Backen zu)")
    kopf_ab = kopf_lage(A.ZK_ABWURF, greif=1.0)
    stellungen = [A.RINNE_WINKEL * i / 12 for i in range(13)]
    for w in stellungen:
        for r_ in rinne:
            s = A.lage(r_, rinne_w=w)
            for f in fest:
                if f.name.startswith(("A22_", "Lagerbock_Drehring", "Trichterhalter", "Stirnrad_m1_Z33")):
                    continue
                v = schnitt(s, f.form)
                if v > TOL:
                    melde("K5", f"{r_.name} bei {w:.0f}° trifft {f.name} ({v:.0f} mm³)")
            for n, k in kopf_ab:
                v = schnitt(s, k)
                if v > TOL:
                    melde("K5", f"{r_.name} bei {w:.0f}° trifft {n} ({v:.0f} mm³)")
    for fid, name, H, D in sorten:
        hit = None
        for w in stellungen:
            for r_ in rinne:
                s = A.lage(r_, rinne_w=w)
                for i in range(A.N_TASCHEN):
                    fl = bei(glas[fid] if i == 0 else voll[fid], D, 90 + 45 * i)
                    v = schnitt(s, fl)
                    if v > TOL:
                        hit = (w, r_.name, i, v)
                        break
                if hit:
                    break
            if hit:
                break
        if hit:
            melde("K5", f"{name}: {hit[1]} bei {hit[0]:.0f}° trifft Flasche in Tasche {hit[2]} ({hit[3]:.0f} mm³)")

    print("K6 Nachbartaschen gegen Kopf in Arbeitsstellung")
    for fid, name, H, D in sorten:
        for kipp, g in ((0.0, 0.0), (0.0, 1.0), (A.KIPP_WINKEL, 1.0)):
            ks = kopf_lage(A.zk_arbeit(H), kipp, g)
            for w in (45, 135):
                fl = bei(voll[fid], D, w)
                for n, k in ks:
                    v = schnitt(fl, k)
                    if v > TOL:
                        melde("K6", f"{name}: Nachbarflasche bei {w}° berührt {n} (Kippen {kipp:.0f}°) ({v:.0f} mm³)")

    print("K7 Geländer je Sorte eingestellt")
    for fid, name, H, D in sorten:
        r = A.gelaender_r(D)
        aussen = A.flaschen_r(D) + D / 2
        for i, (w0, w1) in enumerate(A.SEGMENTE, 1):
            band = A.bogenband(r, 2, *A.GEL_Z, w0, w1)
            v = schnitt(bei(voll[fid], D, (w0 + w1) / 2), band)
            if v > TOL:
                melde("K7", f"{name}: Geländer {i} überschneidet Flasche ({v:.0f} mm³)")
        luft = r - aussen
        if not 0 < luft <= 1.0:
            melde("K7", f"{name}: Luft Geländer {luft:.2f} mm außerhalb 0 … 1 mm")
        klemme = r + 66
        if not A.SOCKEL_R[0] + 5 <= klemme <= A.SOCKEL_R[1] - 5:
            melde("K7", f"{name}: Klemmhebel bei Radius {klemme:.1f} mm außerhalb des Langlochs")
    rmin, rmax = A.gelaender_r(A.D_MIN), A.gelaender_r(A.D_MAX)
    print(f"  Stellbereich Geländer: Radius {rmin:.1f} … {rmax:.1f} mm (Hub {rmax - rmin:.1f} mm), "
          f"Langloch {A.SOCKEL_R[0] + 5:.0f} … {A.SOCKEL_R[1] - 5:.0f} mm")

    print("K8 Sternrad und Flaschen gegen feste Teile (Geländer je Sorte)")
    for fid, name, H, D in sorten:
        gel = [(n, f) for n, f, _, _ in A.gelaender_teile(D) if not n.startswith(("A16_", "Druckfeder"))]
        for w in range(0, 46, 5):
            for t in stern:
                s = A.lage(t, stern=-w)
                for n, f in [(f.name, f.form) for f in fest] + gel:
                    if n.startswith(("Flanschlager", "A02_", "Zahnriemen", "A01_")):
                        continue
                    v = schnitt(s, f)
                    if v > TOL:
                        melde("K8", f"[{name}] {t.name} bei {w}° trifft {n} ({v:.0f} mm³)")
        hit = None
        for w10 in range(0, 3600, 75):
            fl = bei(voll[fid], D, w10 / 10)
            for n, f in [(f.name, f.form) for f in fest] + gel:
                if n.startswith(("A02_", "A15_")):
                    continue
                v = schnitt(fl, f)
                if v > TOL:
                    hit = (w10 / 10, n, v)
                    break
            if hit:
                break
        if hit:
            melde("K8", f"{name} bei {hit[0]:.1f}° trifft {hit[1]} ({hit[2]:.0f} mm³)")

    print("K9 Konsistenz")
    hoch = A.H_MAX + A.Z0 + 1.5
    tief_kopf = min(A.lage(t, zk=A.ZK_ABWURF, greif=0.0).BoundingBox().zmin for t in kopf)
    print(f"  Kopf in Abwurfhöhe: tiefster Punkt {tief_kopf:.1f} mm, höchster Kronkorken {hoch:.1f} mm")
    if tief_kopf - hoch < 10:
        melde("K9", "Kopf in Abwurfhöhe weniger als 10 mm über dem höchsten Kronkorken")
    # Rinne über den Hälsen: kleinster Abstand Schwenkachse -> Hals ist 298 - 197 = 101 mm
    r_hals = max(A.flaschen_r(D) for _, _, _, D in sorten) + 16
    rho = math.hypot(*A.PIVOT) - r_hals
    print(f"  Rinnenboden über den Hälsen (ab {rho:.0f} mm von der Achse): {A.rinne_boden(rho):.1f} mm, "
          f"höchster Kronkorken {hoch:.1f} mm")
    if A.rinne_boden(rho) < hoch + 3:
        melde("K9", "Fangrinne zu tief über den Hälsen")
    p0, p1 = A.rinne_punkte()
    oben = p0[2] + 12
    lippe_ab = A.ZK_ABWURF - 10
    print(f"  Rinne Oberkante am Ende {oben:.1f} mm, Backen in Abwurfhöhe {lippe_ab:.1f} mm")
    if lippe_ab - oben < 5:
        melde("K9", "Fangrinne schwenkt zu knapp unter den Backen")
    rho_st = math.hypot(A.PIVOT[0], A.YS - A.PIVOT[1])
    fall = (A.ZK_ABWURF - 6.5) - (A.rinne_boden(rho_st) + 1.2)
    print(f"  Fallhöhe Kronkorken in die Rinne: {fall:.1f} mm; Rinne {A.RINNE_NEIGUNG:.0f}°")
    q0, q1 = A.rutsche_punkte()
    neig = math.degrees(math.atan2(q0[2] - q1[2], math.hypot(q1[0] - q0[0], q1[1] - q0[1])))
    print(f"  Neigung Rutsche {neig:.1f}° (Richtwert mind. 20° für Stahl auf Edelstahl)")
    if neig < 20 or A.RINNE_NEIGUNG < 20:
        melde("K9", "Rinne oder Rutsche zu flach")
    for fid, name, H, D in sorten:
        y_off = A.flaschen_r(D) - A.YS
        sehne = math.sqrt(14.4 ** 2 - A.LIPPE_X ** 2)
        if abs(y_off) + sehne > A.BACKE_Y:
            melde("K9", f"{name}: Hals {y_off:+.1f} mm außerhalb der Backenlänge")
    print(f"  Halslage ±{A.Y_VERSATZ:.1f} mm, Backe ±{A.BACKE_Y:.0f} mm, Lippe {A.LIPPE_X} mm (Glas 13,15)")
    hebel = A.KX + A.LIPPE_X
    print(f"  Hebelarm Lippe–Kippachse {hebel:.1f} mm: 150 N Abhebekraft = {150 * hebel / 1000:.1f} Nm "
          f"(Servo -M6 5,9 Nm × Zahnräder 2 = 11,8 Nm)")

    print("K10 Kopf intern: Schwinge und Backen gegen Kopfrahmen")
    paare_ok = (("Stirnrad_m1_Z40", "Stirnrad_m1_Z20"), ("Lagerbolzen", "Bundbuchse"), ("Lagerbolzen", "A28_"))
    for w in (0, 12.5, A.KIPP_WINKEL):
        for g in (0.0, 1.0):
            for t in schwinge:
                s = A.lage(t, kipp=w, greif=g)
                for r_ in rahmen:
                    if any(t.name.startswith(a) and r_.name.startswith(b) for a, b in paare_ok):
                        continue
                    v = schnitt(s, r_.form)
                    if v > TOL:
                        melde("K10", f"{t.name} trifft {r_.name} (Kippen {w}°, Backen {g:.0f}) ({v:.0f} mm³)")
    print(f"\n{len(BEFUNDE)} Befunde ({time.time() - t_start:.0f} s)")
    return BEFUNDE


if __name__ == "__main__":
    main()
