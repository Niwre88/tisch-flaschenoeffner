"""
STL-Dateien und 3D-Vorschau des Flaschenöffner-Automaten TFO-A (Index B).
Die Geometrie wird aus modell_a.py (CadQuery) tesselliert – eine Quelle für alles.

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
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent))
import modell_a as A    # noqa: E402
import erzeuge_stl as M  # noqa: E402

TISCH_Z = 750.0


def netz(form, tol=0.3, ang=0.3):
    v, f = form.tessellate(tol, ang)
    if not f:
        return np.zeros((0, 3, 3))
    v = np.array([(p.x, p.y, p.z) for p in v])
    return v[np.array(f)]


def stl(pfad, netze, skala=1.0, versatz=(0, 0, 0)):
    tris = (np.concatenate(netze) + np.array(versatz, float)) * skala
    nv = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    ln = np.linalg.norm(nv, axis=1, keepdims=True)
    nv = np.divide(nv, ln, out=np.zeros_like(nv), where=ln > 0)
    d = np.zeros(len(tris), dtype=[("n", "<f4", 3), ("v", "<f4", 9), ("a", "<u2")])
    d["n"], d["v"] = nv, tris.reshape(-1, 9)
    pfad.parent.mkdir(parents=True, exist_ok=True)
    with open(pfad, "wb") as f:
        f.write(b"TFO-A Flaschenoeffner-Automat Index B".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        f.write(d.tobytes())
    g = tris.reshape(-1, 3).max(0) - tris.reshape(-1, 3).min(0)
    print(f"  {str(pfad.relative_to(HIER)):42s} {len(tris):7d} Dreiecke  {g[0]:6.1f} x {g[1]:6.1f} x {g[2]:6.1f} mm")


def b64(t):
    return base64.b64encode(np.asarray(t, "<f4").tobytes()).decode()


def tisch_und_mensch():
    """Werkbank und Bedienperson (aus dem Generator des Handgeräts)."""
    M.TEILE.clear()
    y0 = A.RAHMEN[2] - 80
    teile = []
    for x in range(-500, 900, 100):
        for y in range(int(y0), int(y0) + 800, 100):
            teile.append(("tischplatte", M.quader(x, x + 100, y, y + 100, TISCH_Z - 30, TISCH_Z)))
    for x in (-450, 790):
        for y in (y0 + 50, y0 + 690):
            teile.append(("tisch", M.quader(x, x + 60, y, y + 60, 0, TISCH_Z - 30)))
    xb = A.RAHMEN[1] - 25
    oeffnen = (xb - 50 + 18, A.RAHMEN[2] - 50, TISCH_Z + A.DECK + 270)
    M.mensch(X=110.0, Y=-470.0, hand_r=oeffnen, hand_l=(-40.0, -420.0, 830.0))
    teile += [("mensch", p["t"]) for p in M.TEILE]
    M.TEILE.clear()
    return teile


def main():
    A.aufbauen()
    print(f"{len(A.TEILE)} Teile aus modell_a.py")
    fein = {t.name: netz(t.form, 0.2, 0.25) for t in A.TEILE}
    flaschen = {}
    for fid, name, H, D, _ in M.FLASCHEN:
        _, _, _, glas, etik, kork = A.flaschen_formen(fid)
        flaschen[fid] = (netz(glas, 0.4, 0.35), netz(etik, 0.5, 0.4), netz(kork, 0.2, 0.3))

    print("Gesamtdateien:")
    maschine = [fein[t.name] for t in A.TEILE if not t.name.startswith(("Scheibe_PC", "Frontscheibe", "Servicedeckel",
                                                                          "Bedienklappe", "Tuer_Kronkorkenfach"))]
    alle = [fein[t.name] for t in A.TEILE]
    glas, etik, kork = flaschen[A.REF[0]]
    fl = []
    for i in range(A.N_TASCHEN):
        x, y = A.tasche(i, A.REF[3])
        fl += [glas + [x, y, 0], etik + [x, y, 0], kork + [x, y, 0]]
    stl(HIER / "TFO-A_1zu1_Maschine.stl", maschine)
    stl(HIER / "TFO-A_1zu1_mit_Haube_und_Flaschen.stl", alle + fl)
    szene = [t + [0, 0, TISCH_Z] for t in alle + fl] + [t for _, t in tisch_und_mensch()]
    stl(HIER / "TFO-A_1zu1_Szene_mit_Mensch.stl", szene)
    stl(HIER / "TFO-A_1zu4_Druckmodell.stl", maschine + fl, 0.25)
    print("Eigenfertigungsteile (teile/):")
    alt = list((HIER / "teile").glob("A*.stl")) if (HIER / "teile").exists() else []
    nummern = sorted({t.nr for t in A.TEILE if t.nr})
    neu = set()
    for nr in nummern:
        tt = [t for t in A.TEILE if t.nr == nr]
        for t in tt:
            n = fein[t.name]
            mn = n.reshape(-1, 3).min(0)
            p = HIER / "teile" / f"{t.name}.stl"
            stl(p, [n], versatz=-mn)
            neu.add(p.name)
    veraltet = [p.name for p in alt if p.name not in neu]
    if veraltet:
        print("  nicht mehr erzeugt (veraltet):", ", ".join(sorted(veraltet)))

    # ---------------------------------------------------------------- Vorschau
    grob = {t.name: netz(t.form, 0.4, 0.3) for t in A.TEILE}
    pakete = {}
    for t in A.TEILE:
        pakete.setdefault((t.farbe, t.klasse, "maschine"), []).append(grob[t.name] + [0, 0, TISCH_Z])
    for g, n in tisch_und_mensch():
        pakete.setdefault((g, "", "mensch" if g == "mensch" else "tisch"), []).append(n)
    daten = [{"g": g, "k": k, "s": s, "d": b64(np.concatenate(v))} for (g, k, s), v in pakete.items()]
    fdat = []
    for fid, name, H, D, form in M.FLASCHEN:
        # Vorschau: voller Flaschenkörper, gröber aufgelöst (STEP/STL bleiben exakt und hohl)
        voll = A.revolve_profil(M.flasche_profil(H, D, form), (0, 0, A.Z0))
        _, _, _, _, etik_f, kork_f = A.flaschen_formen(fid)
        glas, etik, kork = netz(voll, 1.0, 0.5), netz(etik_f, 1.5, 0.6), netz(kork_f, 0.6, 0.5)
        fdat.append({"id": fid, "name": name, "H": H, "D": D, "r": A.flaschen_r(D), "zp": A.zp_arbeit(H),
                     "glas": b64(glas + [0, 0, TISCH_Z]), "etikett": b64(etik + [0, 0, TISCH_Z]),
                     "kork": b64(kork + [0, 0, TISCH_Z])})
    p0, p1 = A.rinnen_punkte()
    tx, ty = A.trichter_lage()
    farben = {k: [round(c * 255) for c in v[:3]] + [v[3]] for k, v in A.FARBEN.items()}
    farben.update({"tisch": [176, 140, 104, 1], "tischplatte": [176, 140, 104, 1], "mensch": [196, 184, 172, 1]})
    info = {"tisch": TISCH_Z, "zp_modell": A.ZP, "zp_sicher": A.ZP_SICHER, "ys": A.YS, "px": A.PX,
            "aktor_x": A.AKTOR_X, "n": A.N_TASCHEN, "schwenk": list(A.SCHWENK), "schwenk_winkel": A.SCHWENK_WINKEL,
            "c_offset": A.C_OFFSET, "trichter": [tx, ty, A.TRICHTER_OK], "rinne": [list(p0), list(p1)],
            "schublade": [-230.0, 228.0, A.DECK + 20], "klappe_x": A.FACH_X[0] - 4, "front_y": A.RAHMEN[2],
            "farben": farben}
    html = (HIER / "vorschau_vorlage.html").read_text(encoding="utf-8")
    html = (html.replace("/*DATEN*/[]", json.dumps(daten)).replace("/*FLASCHEN*/[]", json.dumps(fdat))
                .replace("/*INFO*/{}", json.dumps(info)))
    (HIER / "vorschau_automatik.html").write_text(html, encoding="utf-8")
    anz = sum(len(np.concatenate(v)) for v in pakete.values())
    print(f"Vorschau: vorschau_automatik.html ({anz} Dreiecke ohne Flaschen)")


if __name__ == "__main__":
    main()
