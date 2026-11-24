"""
STL-Dateien und 3D-Vorschau des Flaschenöffner-Automaten TFO-A (Index D).
Die Geometrie wird aus modell_d.py (CadQuery) tesselliert, eine Quelle für alles.

Aufruf:  python erzeuge_automatik.py
"""
import base64
import json
import struct
import sys
from pathlib import Path

import numpy as np

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
sys.path.insert(0, str(HIER.parent / "gemeinsam"))
import modell_d as A    # noqa: E402
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
        f.write(b"TFO-A Flaschenoeffner-Automat Index D".ljust(80, b" "))
        f.write(struct.pack("<I", len(tris)))
        f.write(d.tobytes())
    g = tris.reshape(-1, 3).max(0) - tris.reshape(-1, 3).min(0)
    print(f"  {str(pfad.relative_to(HIER)):46s} {len(tris):7d} Dreiecke  {g[0]:6.1f} x {g[1]:6.1f} x {g[2]:6.1f} mm")


def drehe(n, w, x, y):
    """Netz (Mover-Koordinaten) um z drehen und verschieben."""
    c, s = np.cos(np.radians(w)), np.sin(np.radians(w))
    r = n.copy()
    r[..., 0], r[..., 1] = c * n[..., 0] - s * n[..., 1] + x, s * n[..., 0] + c * n[..., 1] + y
    return r


def b64(t):
    return base64.b64encode(np.asarray(t, "<f4").tobytes()).decode()


def tisch_und_mensch():
    M.TEILE.clear()
    y0 = A.RAHMEN[2] - 80
    teile = []
    for x in range(-700, 800, 100):
        for y in range(int(y0), int(y0) + 900, 100):
            teile.append(("tischplatte", M.quader(x, x + 100, y, y + 100, TISCH_Z - 30, TISCH_Z)))
    for x in (-650, 690):
        for y in (y0 + 50, y0 + 790):
            teile.append(("tisch", M.quader(x, x + 60, y, y + 60, 0, TISCH_Z - 30)))
    M.mensch(X=40.0, Y=-560.0, hand_r=(120.0, A.RAHMEN[2] - 40, TISCH_Z + A.DECK + 260),
             hand_l=(-120.0, A.RAHMEN[2] - 40, TISCH_Z + A.DECK + 260))
    teile += [("mensch", p["t"]) for p in M.TEILE]
    M.TEILE.clear()
    return teile


def main():
    A.aufbauen()
    print(f"{len(A.TEILE)} Teile aus modell_d.py")
    fein = {t.name: netz(t.form, 0.2, 0.25) for t in A.TEILE}
    _, _, _, glas, etik, kork = A.flaschen_formen(A.REF[0])
    fl = [netz(glas, 0.4, 0.35), netz(etik, 0.5, 0.4), netz(kork, 0.2, 0.3)]

    print("Gesamtdateien:")
    scheiben = ("Scheibe_PC", "Frontscheibe", "Servicedeckel", "Klappe_")
    fest = [t for t in A.TEILE if t.klasse not in A.MOVER_KLASSEN]
    mover_netz = [fein[t.name] for t in A.TEILE if t.klasse in A.MOVER_KLASSEN]
    bewegt = []
    for i, slot in enumerate(A.SLOTS):
        (x, y), w = A.mover_lage(A.STATIONEN[slot])
        teile = mover_netz + fl[:2] + ([fl[2]] if slot not in ("Kurve links", "Ausgabe") else [])
        bewegt += [drehe(n, w, x, y) for n in teile]
    maschine = [fein[t.name] for t in fest if not t.name.startswith(scheiben)] + bewegt
    alle = [fein[t.name] for t in fest] + bewegt
    stl(HIER / "TFO-A_1zu1_Maschine.stl", maschine)
    stl(HIER / "TFO-A_1zu1_mit_Haube_und_Flaschen.stl", alle)
    stl(HIER / "TFO-A_1zu1_Szene_mit_Mensch.stl", [t + [0, 0, TISCH_Z] for t in alle] + [t for _, t in tisch_und_mensch()])
    stl(HIER / "TFO-A_1zu5_Druckmodell.stl", maschine, 0.2)
    print("Eigenfertigungsteile (teile/):")
    for nr in sorted({t.nr for t in A.TEILE if t.nr}):
        for t in [t for t in A.TEILE if t.nr == nr]:
            n = fein[t.name]
            stl(HIER / "teile" / f"{t.name}.stl", [n], versatz=-n.reshape(-1, 3).min(0))

    # ---------------------------------------------------------------- Vorschau
    grob = {t.name: netz(t.form, 0.4, 0.3) for t in A.TEILE}
    pakete = {}
    for t in A.TEILE:
        pakete.setdefault((t.farbe, t.klasse, "maschine"), []).append(grob[t.name] + [0, 0, TISCH_Z])
    for g, n in tisch_und_mensch():
        pakete.setdefault((g, "", "mensch" if g == "mensch" else "tisch"), []).append(n)
    daten = [{"g": g, "k": k, "s": s, "d": b64(np.concatenate(v))} for (g, k, s), v in pakete.items()]
    fdat = []
    for fid, name, H, D, form in A.FLASCHEN:
        _, _, _, _, etik_f, kork_f = A.flaschen_formen(fid)
        fdat.append({"id": fid, "name": name, "H": H, "D": D, "zc": A.zc_arbeit(H),
                     "glas": b64(netz(A.glas_voll(fid), 1.0, 0.5) + [0, 0, TISCH_Z]),
                     "etikett": b64(netz(etik_f, 1.5, 0.6) + [0, 0, TISCH_Z]),
                     "kork": b64(netz(kork_f, 0.6, 0.5) + [0, 0, TISCH_Z])})
    farben = {k: [round(c * 255) for c in v[:3]] + [v[3]] for k, v in A.FARBEN.items()}
    farben.update({"tisch": [176, 140, 104, 1], "tischplatte": [176, 140, 104, 1], "mensch": [196, 184, 172, 1]})
    x0, x1, y0, y1, z0, z1 = A.STEIG
    info = {"tisch": TISCH_Z, "zc_modell": A.ZC, "ys": A.YS, "z0": A.Z0, "n": A.N_MOVER,
            "a": A.A_GERADE, "rk": A.RK, "off": A.OFF, "L": A.L_BAHN,
            "slots": [A.STATIONEN[s] for s in A.SLOTS], "slot_namen": A.SLOTS,
            "arm_w": list(A.ARM_W), "zustell_weg": A.R_ROLLE_AUS - A.R_ROLLE_EIN, "rolle_hub": A.ROLLE_HUB,
            "abheben": A.ABHEBEN, "spalt": A.UEBERBAND_SPALT, "band_ende": A.YS + 118,
            "steig_y": y0 - 3, "steig_oben": z1 - 46, "turm": [*A.TURM, A.TURM_OK, A.DECK + 14],
            "backe_ref": A.backe_x(A.REF[3]), "backe_auf": A.backe_x(A.D_MAX) + A.BACKE_AUF,
            "fach": A.FACH, "fach_b": A.FACH_B, "front_y": A.RAHMEN[2], "farben": farben}
    html = (HIER / "vorschau_vorlage.html").read_text(encoding="utf-8")
    html = (html.replace("/*DATEN*/[]", json.dumps(daten)).replace("/*FLASCHEN*/[]", json.dumps(fdat))
                .replace("/*INFO*/{}", json.dumps(info)))
    (HIER / "vorschau_automatik.html").write_text(html, encoding="utf-8")
    anz = sum(len(np.concatenate(v)) for v in pakete.values())
    print(f"Vorschau: vorschau_automatik.html ({anz} Dreiecke ohne Flaschen)")


if __name__ == "__main__":
    main()
