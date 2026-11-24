"""
Kollisions- und Konsistenzprüfung TFO-A, Index D (exakte Volumenkörper aus modell_d.py).

  K1  Durchfahrt Öffnungsstation: Flasche mit Kronkorken fährt durch den Schlitz ein
      (Rotor 0°, Rollen zurück), offene Flasche fährt aus (Rotor 180°, Kopf 8 mm höher)
  K2  Entbördeln: Rollen zugestellt, Rotor 0 … 360°, gegen das Glas
  K3  Kronkorkenweg: Kronkorken am Überband (nach dem Abheben) bis zum Steigband
  K4  Hubweg Kopf (kleinste … größte Flasche + Abheben) gegen alle festen Teile
  K5  Mover-Umlauf: Mover mit Flasche auf der ganzen Bahn gegen feste Teile und den Kopf
  K6  Mover-Abstände an den Stationen (größte Flasche)
  K7  Klemme: Backen auf jeden Durchmesser geschlossen, geöffnet frei
  K8  Kopf intern: Rotor, Zustellring und Hebel gegen Kopfrahmen
  K9  Konsistenz: Schlitz, Spalte, Neigungen, Turm

Aufruf:  python pruefe_kollisionen.py
"""
import math
import sys
import time
from pathlib import Path

from cadquery import Vector as V

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
import modell_d as A  # noqa: E402

TOL = 0.5
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
    t0 = time.time()
    A.aufbauen()
    kopf = [t for t in A.TEILE if t.klasse in A.KOPF_KLASSEN]
    dreh = [t for t in kopf if t.klasse != "z"]
    rahmen = [t for t in kopf if t.klasse == "z"]
    mov = [t for t in A.TEILE if t.klasse in A.MOVER_KLASSEN]
    fest = [t for t in A.TEILE if t.klasse == ""]
    sorten = [(fid, n, H, D) for fid, n, H, D, _ in A.FLASCHEN]
    voll = {f: A.flasche_voll(f) for f, *_ in sorten}
    glas = {f: A.glas_voll(f) for f, *_ in sorten}
    u_mess, u_oeff = A.STATIONEN["Messen"], A.STATIONEN["Oeffnen"]

    def kopf_lage(zc, rotor=0.0, zustell=0.0):
        return [(t.name, A.lage(t, zc=zc, rotor=rotor, zustell=zustell)) for t in kopf]

    def mover_lage(u, D, flasche_form=None):
        teile = [(t.name, A.lage(t, u=u, klemme=D)) for t in mov]
        if flasche_form is not None:
            teile.append(("Flasche", A.platziere(flasche_form, u)))
        return teile

    print("K1 Durchfahrt Öffnungsstation")
    for fid, name, H, D in sorten:
        zc = A.zc_arbeit(H)
        for phase, (ua, ub, rot, dz, form) in (("Einfahrt", (u_mess, u_oeff, 0.0, 0.0, voll[fid])),
                                                ("Ausfahrt", (u_oeff, u_oeff + 175, 180.0, A.ABHEBEN, glas[fid]))):
            ks = kopf_lage(zc + dz, rot)
            hit = None
            u = ua
            while u <= ub + 0.1 and not hit:
                for n1, f1 in mover_lage(u, D, form):
                    for n2, f2 in ks:
                        v = schnitt(f1, f2)
                        if v > TOL:
                            hit = (u, n1, n2, v)
                            break
                    if hit:
                        break
                u += 10
            if hit:
                melde("K1", f"{name} {phase} bei u {hit[0]:.0f}: {hit[1]} trifft {hit[2]} ({hit[3]:.0f} mm³)")

    print("K2 Entbördeln: Rollen zugestellt, Rotor 0 … 360°, gegen das Glas")
    for fid, name, H, D in sorten:
        g_ = A.platziere(glas[fid], u_oeff)
        for rot in range(0, 360, 30):
            for t in dreh:
                v = schnitt(g_, A.lage(t, zc=A.zc_arbeit(H), rotor=rot, zustell=1.0))
                if v > TOL:
                    melde("K2", f"{name}: {t.name} trifft Glas bei {rot}° ({v:.0f} mm³)")

    print("K3 Kronkorkenweg am Überband bis zum Steigband")
    for fid, name, H, D in sorten:
        zc = A.zc_arbeit(H) + A.ABHEBEN
        ks = kopf_lage(zc, 180.0)
        hit = None
        for dy in range(0, 116, 5):
            k = A.kronkorken(H, zc + A.UEBERBAND_SPALT).translate(V(0, A.YS + dy, 0))
            for n, f in ks:
                if n.startswith(("Magnet-Ueberband", "Magnetleiste")):
                    continue
                v = schnitt(k, f)
                if v > TOL:
                    hit = (dy, n, v)
                    break
            if hit:
                break
        if hit:
            melde("K3", f"{name}: Kronkorken trifft {hit[1]} nach {hit[0]} mm ({hit[2]:.0f} mm³)")

    print("K4 Hubweg des Kopfes gegen feste Teile")
    gemeldet = set()
    zc = A.ZC_MIN
    while zc <= A.ZC_MAX + A.ABHEBEN + 0.1:
        for n, k in kopf_lage(zc):
            for f in fest:
                if (n, f.name) in gemeldet:
                    continue
                if n.startswith(("Schlitten_Linearmodul", "A45_")) and f.name.startswith("Linearmodul"):
                    continue
                v = schnitt(k, f.form)
                if v > TOL:
                    gemeldet.add((n, f.name))
                    melde("K4", f"{n} trifft {f.name} bei ZC {zc:.0f} mm ({v:.0f} mm³)")
        zc += 10

    print("K5 Mover-Umlauf gegen feste Teile und Kopf")
    ok_paare = (("Laufrolle_Mover", "Magnetbahn"), ("Mover_Magnetbahn", "Magnetbahn"),
                ("Kurvenrolle_Klemme", "A20_Kurvenschiene"))
    kopf_extrem = [kopf_lage(A.ZC_MIN), kopf_lage(A.ZC_MAX + A.ABHEBEN)]
    for fid, name, H, D in sorten:
        hit = None
        u = 0.0
        while u < A.L_BAHN and not hit:
            teile = mover_lage(u, D, voll[fid])
            for n1, f1 in teile:
                for f in fest:
                    if any(n1.startswith(a) and f.name.startswith(b) for a, b in ok_paare):
                        continue
                    v = schnitt(f1, f.form)
                    if v > TOL:
                        hit = (u, n1, f.name, v)
                        break
                if hit:
                    break
            if not hit and not (u_mess + 5 < u < u_oeff + 180):
                for ks in kopf_extrem:
                    for n1, f1 in teile:
                        for n2, f2 in ks:
                            v = schnitt(f1, f2)
                            if v > TOL:
                                hit = (u, n1, n2, v)
                                break
                        if hit:
                            break
                    if hit:
                        break
            u += 20
        if hit:
            melde("K5", f"{name} bei u {hit[0]:.0f}: {hit[1]} trifft {hit[2]} ({hit[3]:.0f} mm³)")

    print("K6 Mover-Abstände an den Stationen (größte Flasche)")
    D = A.D_MAX
    fid = "grenz"
    for i, s1 in enumerate(A.SLOTS):
        s2 = A.SLOTS[(i + 1) % len(A.SLOTS)]
        a = mover_lage(A.STATIONEN[s1], D, voll[fid])
        b = mover_lage(A.STATIONEN[s2], D, voll[fid])
        for n1, f1 in a:
            for n2, f2 in b:
                v = schnitt(f1, f2)
                if v > TOL:
                    melde("K6", f"{s1} / {s2}: {n1} trifft {n2} ({v:.0f} mm³)")
    # engster Abstand: wartende Flasche (Messen) und Flasche im Kopf
    print(f"  Abstand Messen–Öffnen {u_oeff - u_mess:.0f} mm, Backen bei Ø 100 je {A.backe_x(100) + 12:.1f} mm")

    print("K7 Klemme je Durchmesser")
    for fid, name, H, D in sorten:
        fl = glas[fid]
        for t in mov:
            if t.klasse not in ("jl", "jr"):
                if t.klasse == "mov":
                    v = schnitt(fl, t.form)
                    if v > TOL:
                        melde("K7", f"{name}: {t.name} im Glas ({v:.0f} mm³)")
                continue
            v_zu = schnitt(fl, A.lage(t, klemme=D))
            v_auf = schnitt(fl, A.lage(t, klemme="auf"))
            if v_zu > 5.0 or v_auf > TOL:
                melde("K7", f"{name}: {t.name} zu {v_zu:.1f} mm³ / auf {v_auf:.1f} mm³")

    print("K8 Kopf intern: Rotor, Zustellring, Hebel gegen Kopfrahmen")
    ok_intern = ("Ritzel", "Fuehrungsrolle", "A40_Statorsegment")
    for rot in range(0, 360, 30):
        for zu in (0.0, 1.0):
            for t in dreh:
                s = A.lage(t, rotor=rot, zustell=zu)
                for r_ in rahmen:
                    if r_.name.startswith(ok_intern) and t.klasse in ("ro", "zr"):
                        continue
                    v = schnitt(s, r_.form)
                    if v > TOL:
                        melde("K8", f"{t.name} trifft {r_.name} (Rotor {rot}°, Zustellung {zu:.0f}) ({v:.0f} mm³)")

    print("K9 Konsistenz")
    sehne = 2 * A.R_ROTOR[0] * math.sin(math.radians(A.SCHLITZ / 2))
    print(f"  Schlitz Rotor: Sehne {sehne:.1f} mm innen (Hals mit Kronkorken max. 29,8 mm)")
    if sehne < 34:
        melde("K9", "Schlitz zu schmal")
    p0 = A.STEIG[2] - (A.YS + 115)
    print(f"  Spalt Überband-Ende / Steigband: {p0:.1f} mm")
    x0, x1, y0, y1, z0, z1 = A.STEIG
    tx, ty = A.TURM
    q0, q1 = (8.0, y0 - 24, z1 - 46), (tx + 18, ty - 6, A.TURM_OK + 6)
    neig = math.degrees(math.atan2(q0[2] - q1[2], math.hypot(q1[0] - q0[0], q1[1] - q0[1])))
    print(f"  Abwurfrutsche Steigband -> Turm: {neig:.1f}°")
    if neig < 20:
        melde("K9", f"Abwurfrutsche zu flach ({neig:.1f}°)")
    lage_k = (A.ZC_MAX + A.ABHEBEN + A.UEBERBAND_SPALT, A.ZC_MIN + A.ABHEBEN + A.UEBERBAND_SPALT)
    print(f"  Übergabe an das Steigband zwischen {lage_k[1]:.0f} und {lage_k[0]:.0f} mm (Steigband {z0:.0f} … {z1:.0f})")
    if lage_k[1] - 6 < z0 + 14:
        melde("K9", "Übergabe unterhalb des Steigbands")
    vol = math.pi * (A.TURM_R - 3) ** 2 * (A.TURM_OK - A.DECK - 44)
    print(f"  Sammelturm: Innenvolumen {vol / 1e6:.2f} l, ca. {vol / 9000:.0f} Kronkorken (lose geschüttet)")
    print(f"  Rollenkante zugestellt {A.R_ROLLE_EIN - A.ROLLE_R:.1f} mm (Glas 13,15 mm), Rollenoberkante "
          f"{-A.Z_ARM[1]:.1f} mm unter Kronkorken-Oberkante (Zahnkante 6,0 mm)")
    print(f"\n{len(BEFUNDE)} Befunde ({time.time() - t0:.0f} s)")
    return BEFUNDE


if __name__ == "__main__":
    main()
