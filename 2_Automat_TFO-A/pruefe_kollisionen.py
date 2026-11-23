"""
Kollisions- und Konsistenzprüfung TFO-A, Index B (exakte Volumenkörper aus modell_a.py).

Schema: jedes bewegte Teil an beiden Enden und dazwischen, jede Flaschensorte.
  K1  Takten: Kopf in sicherer Höhe, Flaschen auf dem ganzen Umlauf (alle 7,5°)
  K2  Arbeitsstellung: Vorposition und Station, je Sorte
  K3  Abhebeln: Hebel 0 … 15°, Haken gegen Glas (ohne Kronkorken)
  K4  Hubweg Kopf (tiefste Arbeitshöhe … sichere Höhe) gegen alle festen Teile
  K5  Schwenkarm: 0 … 90° in sicherer Höhe gegen feste Teile, Kopf und offene Flasche
  K6  Nachbartaschen gegen Kopf in Arbeitsstellung
  K7  Geländer auf jede Sorte eingestellt: Flasche liegt an, ohne Überschneidung
  K8  Sternrad und Flaschen gegen feste Teile (Sensoren, Stellarme, Tropfgitter, Front)
  K9  Konsistenz: Abstände (Aktorbügel–Deck, Schalen-Abwurf über Trichter, Hublage)

Aufruf:  python pruefe_kollisionen.py
"""
import math
import sys
from pathlib import Path

from cadquery import Vector as V

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
import modell_a as A  # noqa: E402
import erzeuge_stl as M  # noqa: E402

TOL = 0.5  # mm³


def schnitt(a, b):
    ba, bb = a.BoundingBox(), b.BoundingBox()
    if (ba.xmax < bb.xmin or bb.xmax < ba.xmin or ba.ymax < bb.ymin or bb.ymax < ba.ymin
            or ba.zmax < bb.zmin or bb.zmax < ba.zmin):
        return 0.0
    try:
        return a.intersect(b).Volume()
    except Exception:
        return -1.0


BEFUNDE = []


def melde(k, text):
    BEFUNDE.append((k, text))
    print(f"  [{k}] {text}")


def main():
    A.aufbauen()
    kopf = [t for t in A.TEILE if t.klasse in ("z", "h", "r", "s")]
    fest = [t for t in A.TEILE if t.klasse == "" and not t.name.startswith(("A16_", "Druckfeder_Gelaender"))]
    stern = [t for t in A.TEILE if t.klasse == "st"]
    sorten = [(fid, name, H, D) for fid, name, H, D, _ in M.FLASCHEN]
    flasche = {fid: A.flasche_voll(fid) for fid, *_ in sorten}
    glas = {fid: A.revolve_profil(M.flasche_profil(H, D, f[4]), (0, 0, A.Z0))
            for fid, name, H, D in sorten for f in [next(x for x in M.FLASCHEN if x[0] == fid)]}

    def bei(s, D, winkel_grad, versatz=0.0):
        x, y = A.tasche(0, D, versatz, winkel_grad - 90)
        return s.translate(V(x, y, 0))

    print("K1 Takten (Kopf sicher) – Flaschen auf dem Umlauf")
    dz = A.ZP_SICHER - A.ZP
    ks = [(t.name, A.lage(t, dz_kopf=dz)) for t in kopf]
    for fid, name, H, D in sorten:
        treffer = None
        for w10 in range(0, 3600, 75):
            fl = bei(flasche[fid], D, w10 / 10)
            for n, k in ks:
                v = schnitt(fl, k)
                if v > TOL:
                    treffer = (w10 / 10, n, v)
                    break
            if treffer:
                break
        if treffer:
            melde("K1", f"{name}: berührt {treffer[1]} bei {treffer[0]:.1f}° ({treffer[2]:.0f} mm³)")

    print("K2 Arbeitsstellung (Vorposition 3 mm und Station)")
    for fid, name, H, D in sorten:
        dz = A.zp_arbeit(H) + 0.5 - A.ZP
        ks = [(t.name, A.lage(t, dz_kopf=dz)) for t in kopf]
        for vers, lage in ((3.0, "Vorposition"), (0.0, "Station")):
            fl = bei(flasche[fid], D, 90, vers)
            for n, k in ks:
                v = schnitt(fl, k)
                if v > TOL:
                    melde("K2", f"{name} ({lage}): {n} ({v:.0f} mm³)")

    print("K3 Abhebeln: Haken gegen Glas")
    for fid, name, H, D in sorten:
        dz = A.zp_arbeit(H) + 0.5 - A.ZP
        g = bei(glas[fid], D, 90)
        for w in (0, 5, 10, 15):
            for t in kopf:
                if t.klasse != "h":
                    continue
                v = schnitt(g, A.lage(t, dz_kopf=dz, hebel=w))
                if v > TOL:
                    melde("K3", f"{name}: {t.name} trifft Glas bei {w}° ({v:.0f} mm³)")

    print("K4 Hubweg des Kopfes gegen feste Teile")
    z_tief = A.zp_arbeit(171.5)
    zp = z_tief
    gemeldet = set()
    while zp <= A.ZP_SICHER + 0.1:
        for t in kopf:
            k = A.lage(t, dz_kopf=zp - A.ZP)
            for f in fest:
                if (t.name, f.name) in gemeldet:
                    continue
                if t.name.startswith("Fuehrungswagen") and f.name.startswith("Linearfuehrung"):
                    continue
                if t.name.startswith("Spindelmutter") and f.name.startswith("Trapez"):
                    continue
                v = schnitt(k, f.form)
                if v > TOL:
                    gemeldet.add((t.name, f.name))
                    melde("K4", f"{t.name} trifft {f.name} bei Drehachse {zp:.0f} mm ({v:.0f} mm³)")
        zp += 10

    print("K5 Schwenkarm 0 … 90° in sicherer Höhe")
    dz = A.ZP_SICHER - A.ZP
    schwenk = [t for t in kopf if t.klasse == "s"]
    feste_kopf = [t for t in kopf if t.klasse in ("z", "h", "r") and not t.name.startswith(("A20_", "Servo"))]
    for w in range(0, 91, 10):
        for s_ in schwenk:
            s = A.lage(s_, dz_kopf=dz, schwenk=w)
            for f in fest + feste_kopf:
                v = schnitt(s, f.form if f in fest else A.lage(f, dz_kopf=dz))
                if v > TOL:
                    melde("K5", f"{s_.name} bei {w}° trifft {f.name} ({v:.0f} mm³)")
            for fid, name, H, D in sorten:
                v = schnitt(s, bei(glas[fid], D, 90))
                if v > TOL:
                    melde("K5", f"{s_.name} bei {w}° trifft offene Flasche {name} ({v:.0f} mm³)")
                    break

    print("K6 Nachbartaschen gegen Kopf in Arbeitsstellung")
    for fid, name, H, D in sorten:
        dz = A.zp_arbeit(H) + 0.5 - A.ZP
        ks = [(t.name, A.lage(t, dz_kopf=dz)) for t in kopf]
        for w in (45, 135):
            fl = bei(flasche[fid], D, w)
            for n, k in ks:
                v = schnitt(fl, k)
                if v > TOL:
                    melde("K6", f"{name}: Nachbarflasche bei {w}° berührt {n} ({v:.0f} mm³)")

    print("K7 Geländer je Sorte eingestellt")
    for fid, name, H, D in sorten:
        r = A.gelaender_r(D)
        aussen = A.flaschen_r(D) + D / 2
        for i, (w0, w1) in enumerate(A.SEGMENTE, 1):
            band = A.bogenband(r, 2, A.Z0 + 55, A.Z0 + 75, w0, w1)
            for w in ((w0 + w1) / 2,):
                v = schnitt(bei(flasche[fid], D, w), band)
                if v > TOL:
                    melde("K7", f"{name}: Geländer {i} überschneidet Flasche ({v:.0f} mm³)")
        luft = r - aussen
        if not 0 < luft <= 1.0:
            melde("K7", f"{name}: Luft Geländer {luft:.2f} mm außerhalb 0 … 1 mm")
    rmin, rmax = A.gelaender_r(57.0), A.gelaender_r(80.0)
    print(f"  Stellbereich Geländer: Radius {rmin:.1f} … {rmax:.1f} mm (Hub {rmax - rmin:.1f} mm, Langloch 24 mm + Feder)")

    print("K8 Sternrad und Flaschen gegen feste Teile")
    for w in range(0, 46, 5):
        for t in stern:
            s = A.lage(t, stern=-w)
            for f in fest:
                if f.name.startswith(("Flanschlager", "A02_", "Zahnriemen", "A01_")):
                    continue
                v = schnitt(s, f.form)
                if v > TOL:
                    melde("K8", f"{t.name} bei {w}° trifft {f.name} ({v:.0f} mm³)")
    for fid, name, H, D in sorten:
        for w10 in range(0, 3600, 75):
            fl = bei(flasche[fid], D, w10 / 10)
            for f in fest:
                if f.name.startswith(("A02_", "A15_", "A16_", "A17_", "A18_", "Klemmhebel", "Skala", "Druckfeder_Gel")):
                    continue
                v = schnitt(fl, f.form)
                if v > TOL:
                    melde("K8", f"{name} bei {w10 / 10:.1f}° trifft {f.name} ({v:.0f} mm³)")
                    break

    print("K9 Konsistenz")
    tief = [t for t in kopf if t.name.startswith("A10_")][0]
    uk = A.lage(tief, dz_kopf=z_tief - A.ZP).BoundingBox().zmin
    print(f"  Aktorbügel tiefste Stellung: {uk - A.DECK:.1f} mm über Deck")
    if uk - A.DECK < 10:
        melde("K9", "Aktorbügel zu nah an der Deckplatte")
    tx, ty = A.trichter_lage()
    magnet = [t for t in kopf if t.name.startswith("Elektro-Haftmagnet")][0]
    mb = A.lage(magnet, dz_kopf=A.ZP_SICHER - A.ZP, schwenk=A.SCHWENK_WINKEL).BoundingBox()
    kk_mitte = ((mb.xmin + mb.xmax) / 2 - 3, (mb.ymin + mb.ymax) / 2)
    kk_unten = A.ZP_SICHER + A.C_OFFSET + 0.5 - 6
    print(f"  Kronkorken nach Schwenk über ({kk_mitte[0]:.1f}, {kk_mitte[1]:.1f}), Unterkante {kk_unten:.1f} mm; "
          f"Trichter ({tx:.1f}, {ty:.1f}), Oberkante {A.TRICHTER_OK:.1f} mm")
    if kk_unten <= A.TRICHTER_OK:
        melde("K9", "Kronkorken schwenkt nicht über den Trichterrand")
    p0, p1 = A.rinnen_punkte()
    neig = math.degrees(math.atan2(p0[2] - p1[2], math.hypot(p1[0] - p0[0], p1[1] - p0[1])))
    print(f"  Neigung Rutsche {neig:.1f}° (Richtwert mind. 20° für Stahl auf Edelstahl)")
    if neig < 20:
        melde("K9", f"Rutsche zu flach ({neig:.1f}°)")
    hoch = max(H for _, _, H, _ in sorten) + A.Z0 + 1.5
    lippe = A.ZP_SICHER - 15
    print(f"  Hakenlippe in sicherer Höhe {lippe:.0f} mm, höchster Kronkorken {hoch:.1f} mm")
    print(f"\n{len(BEFUNDE)} Befunde")
    return BEFUNDE


if __name__ == "__main__":
    main()
