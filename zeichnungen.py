"""
Technische Dokumentation des Tisch-Flaschenöffners als PDF.

Erzeugt "Technische_Dokumentation_TFO.pdf" mit
  - Deckblatt, technischen Daten, Funktionsbeschreibung
  - Montageanleitung, Einstell- und Bedienblatt, Wartung und Sicherheit
  - Zusammenbauzeichnung TFO-000 (Ansichten nach Projektionsmethode 1,
    automatisch aus dem 3D-Modell mit Verdeckungsrechnung, Positionsnummern)
  - Stückliste (TFO-000 Blatt 2)
  - Einzelteilzeichnungen TFO-001 ... TFO-008

Normbezug: Schriftfeld nach DIN EN ISO 7200, Linien nach DIN ISO 128,
Bemaßung nach DIN 406 / ISO 129, Gewindedarstellung nach DIN ISO 6410,
Allgemeintoleranzen ISO 2768-mK, Werkstückkanten ISO 13715.

Nur Standardbibliothek + numpy.   Aufruf:  python zeichnungen.py
"""
import math
import zlib
from pathlib import Path

import numpy as np

import erzeuge_stl as M

AUSGABE = Path(__file__).parent / "Technische_Dokumentation_TFO.pdf"
DATUM = "2026-11-22"
TITEL = "Tisch-Flaschenöffner"
MM = 72 / 25.4

# Linienbreiten (Liniengruppe 0,5 nach DIN ISO 128)
BREIT, SCHMAL = 0.5, 0.25
STRICH = {"sichtbar": None, "verdeckt": [3, 1.5], "mitte": [10, 2, 1, 2],
          "phantom": [10, 2, 1, 2, 1, 2]}

# =====================================================================
# Schriftbreiten Helvetica (1/1000 em) für die Textausrichtung
# =====================================================================
_W = dict(zip(" !\"#$%&'()*+,-./0123456789:;<=>?@", [278, 278, 355, 556, 556, 889, 667, 191,
          333, 333, 389, 584, 278, 333, 278, 278] + [556] * 10 + [278, 278, 584, 584, 584, 556, 1015]))
_W.update(zip("ABCDEFGHIJKLMNOPQRSTUVWXYZ", [667, 667, 722, 722, 667, 611, 778, 722, 278, 500,
          667, 556, 833, 722, 778, 667, 778, 722, 667, 611, 722, 667, 944, 667, 667, 611]))
_W.update(zip("abcdefghijklmnopqrstuvwxyz", [556, 556, 500, 556, 556, 278, 556, 556, 222, 222,
          500, 222, 833, 556, 556, 556, 556, 333, 500, 278, 556, 500, 722, 500, 500, 500]))
_W.update({"[": 278, "]": 278, "_": 556, "ä": 556, "ö": 556, "ü": 556, "Ä": 667, "Ö": 778,
           "Ü": 722, "ß": 611, "°": 400, "±": 584, "×": 584, "Ø": 778, "–": 556, "…": 1000,
           "²": 333, "µ": 556, "„": 333, "“": 333, "·": 278})


def tb(s, h, fett=False):
    """Textbreite in mm bei Schrifthöhe h (Versalhöhe)."""
    return sum(_W.get(c, 556) for c in s) / 1000 * (h / 0.72) * (1.06 if fett else 1)


def fz(v):
    """Zahl im deutschen Format ohne überflüssige Nullen."""
    s = f"{round(v, 2):.2f}".rstrip("0").rstrip(".")
    return s.replace(".", ",").replace("-", "–")


# =====================================================================
# Minimaler PDF-Schreiber (Vektorgrafik + Standardschriften)
# =====================================================================
class Seite:
    def __init__(self, b, h):
        self.b, self.h, self.ops = b, h, []
        self.svg = []          # parallele SVG-Ausgabe zur Sichtprüfung

    def _svg_stil(self, w, art, grau, fuellen=None):
        d = STRICH[art] if isinstance(art, str) else art
        g = int(grau * 255)
        if w <= 0:
            s = 'stroke="none"'
        else:
            s = f'stroke="rgb({g},{g},{g})" stroke-width="{w:.2f}" stroke-linecap="round"'
            if d:
                s += f' stroke-dasharray="{" ".join(str(x) for x in d)}"'
        if fuellen is not None:
            f = int(fuellen * 255)
            s += f' fill="rgb({f},{f},{f})"'
        else:
            s += ' fill="none"'
        return s

    def _stil(self, w, art="sichtbar", grau=0.0):
        d = STRICH[art] if isinstance(art, str) else art
        dash = "[" + " ".join(f"{x * MM:.2f}" for x in d) + "] 0 d" if d else "[] 0 d"
        return f"{w * MM:.3f} w {dash} {grau:.2f} G"

    def linie(self, x0, y0, x1, y1, w=SCHMAL, art="sichtbar", grau=0.0):
        self.ops.append(f"{self._stil(w, art, grau)} {x0 * MM:.2f} {y0 * MM:.2f} m "
                        f"{x1 * MM:.2f} {y1 * MM:.2f} l S")
        self.svg.append(f'<line x1="{x0:.2f}" y1="{self.h - y0:.2f}" x2="{x1:.2f}" '
                        f'y2="{self.h - y1:.2f}" {self._svg_stil(w, art, grau)}/>')

    def pfad(self, pts, w=SCHMAL, zu=False, fuellen=None, art="sichtbar", grau=0.0):
        if len(pts) < 2:
            return
        s = [self._stil(w, art, grau)]
        s.append(f"{pts[0][0] * MM:.2f} {pts[0][1] * MM:.2f} m")
        s += [f"{x * MM:.2f} {y * MM:.2f} l" for x, y in pts[1:]]
        if fuellen is not None:
            s.append(f"{fuellen:.2f} g h B" if w > 0 else f"{fuellen:.2f} g h f")
        else:
            s.append("h S" if zu else "S")
        self.ops.append(" ".join(s))
        pts_s = " ".join(f"{x:.2f},{self.h - y:.2f}" for x, y in pts)
        tag = "polygon" if (zu or fuellen is not None) else "polyline"
        self.svg.append(f'<{tag} points="{pts_s}" {self._svg_stil(w, art, grau, fuellen)}/>')

    def rechteck(self, x0, y0, x1, y1, w=SCHMAL, art="sichtbar", fuellen=None):
        self.pfad([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], w, True, fuellen, art)

    def bogen_pkte(self, cx, cy, r, a0, a1, n=None):
        n = n or max(8, int(abs(a1 - a0) / 6))
        return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
                 cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]

    def kreis(self, cx, cy, r, w=SCHMAL, art="sichtbar", fuellen=None):
        self.pfad(self.bogen_pkte(cx, cy, r, 0, 360, 48)[:-1], w, True, fuellen, art)

    def bogen(self, cx, cy, r, a0, a1, w=SCHMAL, art="sichtbar"):
        self.pfad(self.bogen_pkte(cx, cy, r, a0, a1), w, False, None, art)

    def text(self, x, y, s, h=3.5, fett=False, ausr="l", winkel=0.0, grau=0.0):
        s = str(s)
        for a, b in (("≈", "~"), ("→", "->"), ("≤", "<="), ("≥", ">="), ("√", "W")):
            s = s.replace(a, b)
        w = tb(s, h, fett)
        dx = {"l": 0, "m": -w / 2, "r": -w}[ausr]
        c, si = math.cos(math.radians(winkel)), math.sin(math.radians(winkel))
        x0, y0 = x + dx * c, y + dx * si
        esc = s.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        self.ops.append(f"BT /{'F2' if fett else 'F1'} {h / 0.72 * MM:.2f} Tf {grau:.2f} g "
                        f"{c:.4f} {si:.4f} {-si:.4f} {c:.4f} {x0 * MM:.2f} {y0 * MM:.2f} Tm "
                        f"({esc}) Tj ET")
        t = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        g = int(grau * 255)
        self.svg.append(f'<text x="{x0:.2f}" y="{self.h - y0:.2f}" font-family="Helvetica,Arial" '
                        f'font-size="{h / 0.72:.2f}" font-weight="{"bold" if fett else "normal"}" '
                        f'fill="rgb({g},{g},{g})" transform="rotate({-winkel:.1f} {x0:.2f} '
                        f'{self.h - y0:.2f})">{t}</text>')

    def als_svg(self):
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.b} {self.h}" '
                f'width="100%" style="background:#fff">'
                + "".join(self.svg) + "</svg>")

    def pfeil(self, x, y, winkel, laenge=2.6, breite=0.9):
        a = math.radians(winkel)
        bx, by = x - laenge * math.cos(a), y - laenge * math.sin(a)
        nx, ny = -math.sin(a) * breite / 2, math.cos(a) * breite / 2
        self.pfad([(x, y), (bx + nx, by + ny), (bx - nx, by - ny)], 0, True, 0.0)


class PDF:
    def __init__(self):
        self.seiten = []

    def seite(self, b, h):
        s = Seite(b, h)
        self.seiten.append(s)
        return s

    def speichern(self, pfad):
        objs = []

        def neu(inhalt):
            objs.append(inhalt)
            return len(objs)

        neu(b"<< /Type /Catalog /Pages 2 0 R >>")
        neu(b"")  # Platzhalter Pages
        f1 = neu(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>")
        f2 = neu(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>")
        kids = []
        for s in self.seiten:
            daten = zlib.compress("\n".join(["1 J 1 j"] + s.ops).encode("cp1252", "replace"))
            c = neu(b"<< /Length %d /Filter /FlateDecode >>\nstream\n" % len(daten) + daten + b"\nendstream")
            p = neu(("<< /Type /Page /Parent 2 0 R /MediaBox [0 0 %.2f %.2f] /Resources << /Font << "
                     "/F1 %d 0 R /F2 %d 0 R >> >> /Contents %d 0 R >>" % (s.b * MM, s.h * MM, f1, f2, c)).encode())
            kids.append(p)
        objs[1] = ("<< /Type /Pages /Kids [%s] /Count %d >>" % (" ".join(f"{k} 0 R" for k in kids), len(kids))).encode()
        info = neu(("<< /Title (Technische Dokumentation %s) /Producer (zeichnungen.py) >>"
                    % "Tisch-Flaschenoeffner").encode())
        out = bytearray(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        pos = []
        for i, o in enumerate(objs, 1):
            pos.append(len(out))
            out += b"%d 0 obj\n" % i + o + b"\nendobj\n"
        x = len(out)
        out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
        out += b"".join(b"%010d 00000 n \n" % p for p in pos)
        out += b"trailer\n<< /Size %d /Root 1 0 R /Info %d 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, info, x)
        Path(pfad).write_bytes(out)


# =====================================================================
# Blatt mit Rahmen und Schriftfeld
# =====================================================================
FORMATE = {"A4h": (210, 297), "A4q": (297, 210), "A3q": (420, 297)}
BLAETTER = []      # (Sachnummer, Titel, Format) für das Zeichnungsverzeichnis


def projektionssymbol(S, x, y):
    """Symbol Projektionsmethode 1 (DIN ISO 5456-2), Mittelpunkt links unten (x, y)."""
    S.pfad([(x, y + 1.5), (x + 9, y), (x + 9, y + 8), (x, y + 6.5)], SCHMAL, True)
    S.linie(x - 1.5, y + 4, x + 10.5, y + 4, 0.18, "mitte")
    S.kreis(x + 16, y + 4, 4, SCHMAL)
    S.kreis(x + 16, y + 4, 2.25, SCHMAL)
    S.linie(x + 11, y + 4, x + 21, y + 4, 0.18, "mitte")


def blatt(pdf, fmt, titel, sachnr, massstab="", werkstoff="", rohmass="", masse="",
          zusatz="", blatt_nr="1/1", toleranz=True):
    b, h = FORMATE[fmt]
    S = pdf.seite(b, h)
    S.rechteck(20, 10, b - 10, h - 10, 0.7)
    for i in range(1, 4):                            # Zentriermarken
        pass
    for xm in (b / 2 + 5,):
        S.linie(xm, h - 10, xm, h - 5, 0.7)
        S.linie(xm, 10, xm, 5, 0.7)
    S.linie(20, h / 2, 15, h / 2, 0.7)
    S.linie(b - 10, h / 2, b - 5, h / 2, 0.7)
    x0, y0, W = b - 10 - 180, 10, 180
    S.rechteck(x0, y0, x0 + W, y0 + 44, 0.5)
    # Zeile oben: Toleranzen / Kanten / Oberfläche / Maßstab / Projektion
    def feld(xa, ya, xb, yb, lab, wert, hw=2.5, fett=False):
        S.rechteck(xa, ya, xb, yb, SCHMAL)
        S.text(xa + 1, yb - 2.2, lab, 1.6, grau=0.3)
        if wert:
            S.text(xa + 1.2, ya + 1.6, wert, hw, fett)
    feld(x0, y0 + 36, x0 + 50, y0 + 44, "Allgemeintoleranzen",
         "ISO 2768-mK" if toleranz else "–")
    feld(x0 + 50, y0 + 36, x0 + 92, y0 + 44, "Werkstückkanten", "ISO 13715  -0,3" if toleranz else "–")
    feld(x0 + 92, y0 + 36, x0 + 125, y0 + 44, "Oberfläche", "Ra 6,3" if toleranz else "–")
    feld(x0 + 125, y0 + 36, x0 + 148, y0 + 44, "Maßstab", massstab, 3.0, True)
    S.rechteck(x0 + 148, y0 + 36, x0 + W, y0 + 44, SCHMAL)
    projektionssymbol(S, x0 + 153, y0 + 36.5)
    # Zeile 2: Werkstoff / Rohmaß / Masse / Format
    feld(x0, y0 + 28, x0 + 70, y0 + 36, "Werkstoff", werkstoff, 2.3)
    feld(x0 + 70, y0 + 28, x0 + 125, y0 + 36, "Halbzeug / Rohmaß", rohmass, 2.3)
    feld(x0 + 125, y0 + 28, x0 + 155, y0 + 36, "Masse", masse, 2.3)
    feld(x0 + 155, y0 + 28, x0 + W, y0 + 36, "Format", fmt[:2], 2.5)
    # Block links: Verantwortung (ISO 7200)
    feld(x0, y0 + 19, x0 + 35, y0 + 28, "Erstellt durch", "KI-Entwurf", 2.2)
    feld(x0 + 35, y0 + 19, x0 + 70, y0 + 28, "Ausgabedatum", DATUM, 2.2)
    feld(x0, y0 + 10, x0 + 35, y0 + 19, "Geprüft", "", 2.2)
    feld(x0 + 35, y0 + 10, x0 + 70, y0 + 19, "Genehmigt", "", 2.2)
    feld(x0, y0, x0 + 35, y0 + 10, "Dokumentenstatus", "Entwurf", 2.2)
    feld(x0 + 35, y0, x0 + 70, y0 + 10, "Dokumentenart", "Zeichnung", 2.2)
    # Block rechts: Titel / Sachnummer / Blatt
    feld(x0 + 70, y0 + 10, x0 + W, y0 + 28, "Titel, zusätzlicher Titel", "", 0)
    S.text(x0 + 72, y0 + 20.5, titel, 4.2, True)
    S.text(x0 + 72, y0 + 13, zusatz or TITEL, 2.5)
    feld(x0 + 70, y0, x0 + 135, y0 + 10, "Sachnummer", sachnr, 3.5, True)
    feld(x0 + 135, y0, x0 + 150, y0 + 10, "Änd.", "A", 3.0)
    feld(x0 + 150, y0, x0 + 165, y0 + 10, "Sprache", "de", 2.5)
    feld(x0 + 165, y0, x0 + W, y0 + 10, "Blatt", blatt_nr, 2.5)
    BLAETTER.append((sachnr, titel, fmt, blatt_nr))
    return S


# =====================================================================
# Ansicht: lokale Bauteilkoordinaten (mm) -> Blatt
# =====================================================================
KERN = {3: 2.5, 4: 3.3, 5: 4.2, 6: 5.0, 8: 6.8, 10: 8.5}


class Ansicht:
    def __init__(self, S, ox, oy, m):
        self.S, self.ox, self.oy, self.m = S, ox, oy, m

    def P(self, u, v):
        return self.ox + u * self.m, self.oy + v * self.m

    def linie(self, u0, v0, u1, v1, art="sichtbar", w=None):
        w = w or (BREIT if art == "sichtbar" else SCHMAL)
        self.S.linie(*self.P(u0, v0), *self.P(u1, v1), w, art)

    def poly(self, pts, art="sichtbar", zu=True, w=None):
        w = w or (BREIT if art == "sichtbar" else SCHMAL)
        self.S.pfad([self.P(u, v) for u, v in pts], w, zu, None, art)

    def rechteck(self, u0, v0, u1, v1, art="sichtbar"):
        self.poly([(u0, v0), (u1, v0), (u1, v1), (u0, v1)], art)

    def kreis(self, u, v, r, art="sichtbar", w=None):
        w = w or (BREIT if art == "sichtbar" else SCHMAL)
        self.S.kreis(*self.P(u, v), r * self.m, w, art)

    def kreuz(self, u, v, r, ueber=2.0):
        x, y = self.P(u, v)
        a = r * self.m + ueber
        self.S.linie(x - a, y, x + a, y, 0.18, "mitte")
        self.S.linie(x, y - a, x, y + a, 0.18, "mitte")

    def mittellinie(self, u0, v0, u1, v1, ueber=2.0):
        (x0, y0), (x1, y1) = self.P(u0, v0), self.P(u1, v1)
        L = math.hypot(x1 - x0, y1 - y0) or 1
        ex, ey = (x1 - x0) / L * ueber, (y1 - y0) / L * ueber
        self.S.linie(x0 - ex, y0 - ey, x1 + ex, y1 + ey, 0.18, "mitte")

    def bohrung(self, u, v, d, art="sichtbar"):
        self.kreis(u, v, d / 2, art)
        self.kreuz(u, v, d / 2)

    def gewinde(self, u, v, nenn, sichtbar=True):
        """Draufsicht Gewindebohrung nach ISO 6410: Kernloch breit, 3/4-Kreis schmal."""
        x, y = self.P(u, v)
        if sichtbar:
            self.S.kreis(x, y, KERN[nenn] / 2 * self.m, BREIT)
            self.S.bogen(x, y, nenn / 2 * self.m, 100, 370, SCHMAL)
        else:
            self.S.kreis(x, y, KERN[nenn] / 2 * self.m, SCHMAL, "verdeckt")
        self.kreuz(u, v, nenn / 2)

    def langloch(self, u, v, b, l, art="sichtbar"):
        """Langloch, Länge l in u-Richtung, Breite b."""
        r = b / 2
        a = (l - b) / 2
        pts = [(u - a + r * math.cos(math.radians(t)), v + r * math.sin(math.radians(t)))
               for t in range(90, 271, 15)]
        pts += [(u + a + r * math.cos(math.radians(t)), v + r * math.sin(math.radians(t)))
                for t in range(-90, 91, 15)]
        self.poly(pts, art)
        self.mittellinie(u - a - r, v, u + a + r, v)
        self.mittellinie(u - a, v - r, u - a, v + r, 1.5)
        self.mittellinie(u + a, v - r, u + a, v + r, 1.5)

    def bohrung_seite(self, u, v0, v1, d, achse="v", art="verdeckt", gewinde=None):
        """Bohrung im Schnitt/als verdeckte Kanten: Achse in v (senkrecht) oder u."""
        r = (KERN[gewinde] if gewinde else d) / 2
        if achse == "v":
            self.linie(u - r, v0, u - r, v1, art)
            self.linie(u + r, v0, u + r, v1, art)
            if gewinde:
                self.linie(u - gewinde / 2, v0, u - gewinde / 2, v1, art, SCHMAL)
                self.linie(u + gewinde / 2, v0, u + gewinde / 2, v1, art, SCHMAL)
            self.mittellinie(u, v0, u, v1)
        else:
            self.linie(v0, u - r, v1, u - r, art)
            self.linie(v0, u + r, v1, u + r, art)
            if gewinde:
                self.linie(v0, u - gewinde / 2, v1, u - gewinde / 2, art, SCHMAL)
                self.linie(v0, u + gewinde / 2, v1, u + gewinde / 2, art, SCHMAL)
            self.mittellinie(v0, u, v1, u)

    # ---------------------------------------------------- Bemaßung
    def mass(self, p1, p2, r, ab, text=None, vor="", nach="", h=3.5):
        """Maß zwischen p1 und p2 (lokal). r='h' waagerecht, 'v' senkrecht.
        ab = Abstand der Maßlinie in Blatt-mm (+ oben/rechts, - unten/links)."""
        S = self.S
        (x1, y1), (x2, y2) = self.P(*p1), self.P(*p2)
        if r == "h":
            wert = abs(p2[0] - p1[0])
            yl = (max(y1, y2) + ab) if ab > 0 else (min(y1, y2) + ab)
            for x, y in ((x1, y1), (x2, y2)):
                sg = 1 if yl > y else -1
                if abs(yl - y) > 1.2:
                    S.linie(x, y + sg * 1.0, x, yl + sg * 2.0, 0.18)
            xa, xb = sorted((x1, x2))
            t = text if text is not None else vor + fz(wert) + nach
            w = tb(t, h)
            if xb - xa >= 9:
                S.linie(xa, yl, xb, yl, 0.18)
                S.pfeil(xa, yl, 180)
                S.pfeil(xb, yl, 0)
            else:
                S.linie(xa - 6, yl, xb + 6, yl, 0.18)
                S.pfeil(xa, yl, 0)
                S.pfeil(xb, yl, 180)
            if xb - xa > w + 6:
                S.text((xa + xb) / 2, yl + 1.0, t, h, ausr="m")
            else:
                S.text(xb + 7, yl + 1.0, t, h)
        else:
            wert = abs(p2[1] - p1[1])
            xl = (max(x1, x2) + ab) if ab > 0 else (min(x1, x2) + ab)
            for x, y in ((x1, y1), (x2, y2)):
                sg = 1 if xl > x else -1
                if abs(xl - x) > 1.2:
                    S.linie(x + sg * 1.0, y, xl + sg * 2.0, y, 0.18)
            ya, yb = sorted((y1, y2))
            t = text if text is not None else vor + fz(wert) + nach
            w = tb(t, h)
            if yb - ya >= 9:
                S.linie(xl, ya, xl, yb, 0.18)
                S.pfeil(xl, ya, 270)
                S.pfeil(xl, yb, 90)
            else:
                S.linie(xl, ya - 6, xl, yb + 6, 0.18)
                S.pfeil(xl, ya, 90)
                S.pfeil(xl, yb, 270)
            if yb - ya > w + 6:
                S.text(xl - 1.0, (ya + yb) / 2, t, h, ausr="m", winkel=90)
            else:
                S.text(xl - 1.0, yb + 7, t, h, winkel=90)

    def hinweis(self, p, winkel, laenge, text, h=3.5, pfeil=True):
        """Hinweislinie mit Pfeil auf Punkt p (lokal) und waagerechter Schulter."""
        S = self.S
        x, y = self.P(*p)
        a = math.radians(winkel)
        x1, y1 = x + laenge * math.cos(a), y + laenge * math.sin(a)
        S.linie(x, y, x1, y1, 0.18)
        if pfeil:
            S.pfeil(x, y, winkel + 180)
        zeilen = text.split("\n")
        w = max(tb(z, h) for z in zeilen)
        rechts = math.cos(a) >= 0
        x2 = x1 + (w + 2) * (1 if rechts else -1)
        S.linie(x1, y1, x2, y1, 0.18)
        for i, z in enumerate(zeilen):
            S.text(min(x1, x2) + 1, y1 + 1.0 - i * (h + 1.8), z, h)

    def winkelmass(self, c, r, a0, a1, text, h=3.5):
        S = self.S
        cx, cy = self.P(*c)
        rr = r * self.m
        S.bogen(cx, cy, rr, a0, a1, 0.18)
        S.pfeil(cx + rr * math.cos(math.radians(a0)), cy + rr * math.sin(math.radians(a0)), a0 - 90)
        S.pfeil(cx + rr * math.cos(math.radians(a1)), cy + rr * math.sin(math.radians(a1)), a1 + 90)
        am = math.radians((a0 + a1) / 2)
        S.text(cx + (rr + 2) * math.cos(am), cy + (rr + 2) * math.sin(am) - 1.2, text, h,
               ausr="l" if math.cos(am) >= 0 else "r")


def titel_ansicht(S, x, y, t, h=3.5):
    S.text(x, y, t, h, ausr="m")


def notizen(S, x, y, zeilen, h=2.8, kopf="Hinweise"):
    S.text(x, y, kopf, 3.2, True)
    y -= 5.5
    for z in zeilen:
        S.text(x, y, z, h)
        y -= h + 2.2
    return y


# =====================================================================
# Verdeckungsrechnung für Zusammenbauansichten
# =====================================================================
def ansichtsbasis(name):
    """Liefert Funktion Welt -> (u, v, Tiefe) für Ansicht nach Projektionsmethode 1."""
    if name == "vorne":
        R = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]], float)
    elif name == "oben":
        R = np.array([[1, 0, 0], [0, 1, 0], [0, 0, -1]], float)
    elif name == "links":
        R = np.array([[0, -1, 0], [0, 0, 1], [1, 0, 0]], float)
    else:  # isometrisch, Blick von vorn links oben
        f = np.array([1.0, 1.0, -0.82])
        f /= np.linalg.norm(f)
        r = np.cross(f, [0, 0, 1.0])
        r /= np.linalg.norm(r)
        up = np.cross(r, f)
        R = np.array([r, up, f])
    return R


def kanten_sichtbar(teile_verdeckend, teile_zeichnen, name, res=0.4, eps=0.9):
    """Sichtbare Körperkanten (Kanten mit Knick > 25° und Umrisslinien) als 2D-Strecken."""
    R = ansichtsbasis(name)
    alle = np.concatenate([t @ R.T for t in teile_verdeckend])
    umin, vmin = alle[:, :, 0].min() - 2, alle[:, :, 1].min() - 2
    umax, vmax = alle[:, :, 0].max() + 2, alle[:, :, 1].max() + 2
    W, H = int((umax - umin) / res) + 2, int((vmax - vmin) / res) + 2
    zb = np.full((H, W), np.inf)
    for t in alle:
        (u0, v0, d0), (u1, v1, d1), (u2, v2, d2) = t
        fl = (u1 - u0) * (v2 - v0) - (u2 - u0) * (v1 - v0)
        if abs(fl) < 1e-9:
            continue
        i0 = max(int((min(u0, u1, u2) - umin) / res), 0)
        i1 = min(int((max(u0, u1, u2) - umin) / res) + 1, W - 1)
        j0 = max(int((min(v0, v1, v2) - vmin) / res), 0)
        j1 = min(int((max(v0, v1, v2) - vmin) / res) + 1, H - 1)
        us = umin + (np.arange(i0, i1 + 1) + 0.5) * res
        vs = vmin + (np.arange(j0, j1 + 1) + 0.5) * res
        UU, VV = np.meshgrid(us, vs)
        w0 = ((u1 - UU) * (v2 - VV) - (u2 - UU) * (v1 - VV)) / fl
        w1 = ((u2 - UU) * (v0 - VV) - (u0 - UU) * (v2 - VV)) / fl
        w2 = 1 - w0 - w1
        m = (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
        d = w0 * d0 + w1 * d1 + w2 * d2
        sub = zb[j0:j1 + 1, i0:i1 + 1]
        upd = m & (d < sub)
        sub[upd] = d[upd]
    # 3x3-Minimum, damit Kanten nicht von der eigenen Fläche verdeckt werden
    zm = zb.copy()
    for di in (-1, 0, 1):
        for dj in (-1, 0, 1):
            zm = np.minimum(zm, np.roll(np.roll(zb, di, 0), dj, 1))

    blick = R[2]
    strecken = []
    cos_knick = math.cos(math.radians(25))
    for tris in teile_zeichnen:
        n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
        ln = np.linalg.norm(n, axis=1, keepdims=True)
        n = np.divide(n, ln, out=np.zeros_like(n), where=ln > 0)
        key = {}
        ids = np.zeros((len(tris), 3), int)
        for i, t in enumerate(tris):
            for k in range(3):
                kk = tuple(np.round(t[k], 3))
                ids[i, k] = key.setdefault(kk, len(key))
        pkt = np.zeros((len(key), 3))
        for kk, i in key.items():
            pkt[i] = kk
        kanten = {}
        for i in range(len(tris)):
            a, b, c = ids[i]
            for e in ((a, b), (b, c), (c, a)):
                kanten.setdefault((min(e), max(e)), []).append(i)
        for (a, b), fl in kanten.items():
            if len(fl) == 2:
                n1, n2 = n[fl[0]], n[fl[1]]
                if np.dot(n1, n2) > cos_knick and np.dot(n1, blick) * np.dot(n2, blick) > 0:
                    continue
            p0, p1 = pkt[a] @ R.T, pkt[b] @ R.T
            L = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
            if L < 0.05:
                continue
            k = max(2, int(L / 0.3) + 1)
            ts = np.linspace(0, 1, k)
            P = p0[None, :] + (p1 - p0)[None, :] * ts[:, None]
            ii = np.clip(((P[:, 0] - umin) / res).astype(int), 0, W - 1)
            jj = np.clip(((P[:, 1] - vmin) / res).astype(int), 0, H - 1)
            sicht = P[:, 2] <= zm[jj, ii] + eps
            # zusammenhängende sichtbare Abschnitte
            start = None
            for idx in range(k):
                if sicht[idx] and start is None:
                    start = idx
                if (not sicht[idx] or idx == k - 1) and start is not None:
                    ende = idx if sicht[idx] else idx - 1
                    if ende > start:
                        strecken.append((P[start, 0], P[start, 1], P[ende, 0], P[ende, 1]))
                    start = None
    return strecken


def zeichne_strecken(A, strecken, w=0.35, art="sichtbar"):
    for u0, v0, u1, v1 in strecken:
        A.S.linie(*A.P(u0, v0), *A.P(u1, v1), w, art)


def einpassen(S, strecken, x0, y0, x1, y1, m=None):
    """Ansicht so legen, dass die Strecken mittig in das Rechteck passen."""
    a = np.array(strecken)
    umin, umax = min(a[:, 0].min(), a[:, 2].min()), max(a[:, 0].max(), a[:, 2].max())
    vmin, vmax = min(a[:, 1].min(), a[:, 3].min()), max(a[:, 1].max(), a[:, 3].max())
    if m is None:
        m = min((x1 - x0) / (umax - umin), (y1 - y0) / (vmax - vmin))
    ox = (x0 + x1) / 2 - (umin + umax) / 2 * m
    oy = (y0 + y1) / 2 - (vmin + vmax) / 2 * m
    return Ansicht(S, ox, oy, m)


# =====================================================================
# Modell aufbauen
# =====================================================================
def modell():
    M.TEILE.clear()
    M.grundgestell()
    M.spanner_stange()
    M.schlitten()
    M.hebel()
    M.flaschen()
    maschine = [p for p in M.TEILE if p["f"] is None]
    flasche = [p for p in M.TEILE if p["f"] == M.REF[0]]
    return maschine, flasche


DICHTE = {"01_Grundplatte": 2.70, "02_Schlittenplatte": 2.70, "03_Hebel": 7.85,
          "04_Hakenleiste": 7.85, "05_Federhalter": 7.85, "06_Zeiger": 2.70,
          "07_Prisma_Backe_rechts": 1.27 * 0.55, "07_Prisma_Backe_links": 1.27 * 0.55,
          "08_Magnethalter": 7.85}


def masse_kg(teilname):
    v = sum(M.volumen(p["t"]) for p in M.TEILE if p["teil"] == teilname) / 1000.0  # cm³
    return v * DICHTE[teilname] / 1000.0


def mtext(kg):
    return f"{fz(kg)} kg" if kg >= 0.1 else f"{fz(kg * 1000)} g"


# =====================================================================
# Stückliste (eine Quelle für Zeichnung und Text)
# =====================================================================
STUECKLISTE = [
    # Pos, Menge, Einheit, Benennung, Sachnummer / Norm, Werkstoff, Bemerkung
    (1, 1, "Stk", "Grundplatte", "TFO-001", "EN AW-5754 H111", ""),
    (2, 1, "Stk", "Schlittenplatte", "TFO-002", "EN AW-5754 H111", ""),
    (3, 1, "Stk", "Hebel", "TFO-003", "S235JR", "Flachstahl 30×12"),
    (4, 1, "Stk", "Hakenleiste", "TFO-004", "C45", "Lippe scharfkantig"),
    (5, 1, "Stk", "Federhalter (Baugruppe 5.1 + 5.2)", "TFO-005", "S235JR", ""),
    (6, 1, "Stk", "Zeiger", "TFO-006", "EN AW-5754 H22", "Blech 3"),
    (7, 2, "Stk", "Prisma-Backe", "TFO-007", "PETG (3D-Druck)", "1× wie gez., 1× spiegelbildl."),
    (8, 1, "Stk", "Magnethalter", "TFO-008", "S235JR", "Flachstahl 20×5"),
    (10, 1, "Stk", "Systemprofil 40×40 Nut 8, L = 400", "Profilsystem Nut 8", "EN AW-6063 T66", "unten M8 in Kernbohrung"),
    (11, 1, "Stk", "Systemprofil 40×40 Nut 8, L = 60", "Profilsystem Nut 8", "EN AW-6063 T66", "Spanner-Unterbau"),
    (12, 2, "Satz", "Winkelsatz 40 Nut 8", "Profilsystem Nut 8", "Zn-Druckguss", "inkl. Schrauben + Nutensteine"),
    (13, 1, "Stk", "Abdeckkappe 40×40", "Profilsystem Nut 8", "PA", ""),
    (14, 1, "Stk", "Passfeder A 8×7×20", "DIN 6885", "C45+C", "mittig M4 nachgeschnitten, verdeckt"),
    (15, 1, "Stk", "Passfeder A 8×7×18", "DIN 6885", "C45+C", "mittig M4 nachgeschnitten, verdeckt"),
    (16, 2, "Stk", "Hammermutter Nut 8 M8", "Profilsystem Nut 8", "Stahl verzinkt", "verdeckt"),
    (17, 2, "Stk", "Hammermutter Nut 8 M6", "Profilsystem Nut 8", "Stahl verzinkt", "verdeckt"),
    (18, 4, "Stk", "Hammermutter Nut 8 M5", "Profilsystem Nut 8", "Stahl verzinkt", "verdeckt"),
    (19, 2, "Stk", "Klemmhebel mit Gewindebolzen M8×20", "Normteil (Klemmhebel)", "PA / Stahl", ""),
    (20, 1, "Stk", "Passschraube 10 f9 × 16 – M8", "ISO 7379", "12.9", "Drehachse"),
    (21, 2, "Stk", "Bundbuchse 10×12×6, Bund Ø18×1", "Gleitlager (z. B. iglidur G)", "Polymer", "verdeckt"),
    (22, 1, "Stk", "Scheibe 10", "ISO 7089", "200 HV", "verdeckt"),
    (23, 1, "Stk", "Kugelknopf Ø40, Innengewinde M10", "DIN 319", "Duroplast", ""),
    (24, 1, "Stk", "Gewindestift M10×25", "ISO 4026", "45H", "mit Schraubensicherung"),
    (25, 1, "Stk", "Schubstangenspanner, Hub ≥ 35 (40)", "Normteil (Spanner)", "Stahl verzinkt", "Haltekraft ≥ 1000 N"),
    (26, 1, "Stk", "Gummi-Druckkappe für M8", "Normteil", "NBR", ""),
    (27, 1, "Stk", "Flachgreifer Ø16, Gewindezapfen M4", "Normteil (Magnet)", "NdFeB/Stahl", "ca. 40 N"),
    (28, 1, "Stk", "Distanzhülse Ø8 × 16, Bohrung 4,3", "Normteil", "Stahl verzinkt", ""),
    (29, 1, "Stk", "Zugfeder, L0 45–50, Da 12–14", "Normteil (Feder)", "Federstahl", "F0 12–15 N, R 0,3–0,5 N/mm"),
    (30, 1, "Stk", "Gummipuffer Ø20×15, Innengewinde M6", "Normteil", "NR", "Anschlag"),
    (31, 1, "Stk", "Gewindestange M6×60", "DIN 976-1", "5.6", ""),
    (32, 2, "Stk", "Sechskantmutter M6", "ISO 4032", "8", ""),
    (33, 4, "Stk", "Gerätefuß Ø30×10, Gewindebolzen M6", "Normteil", "NR / Stahl", ""),
    (34, 1, "Stk", "Gummimatte 90×85×3, selbstklebend", "–", "EPDM", ""),
    (35, 2, "Stk", "Gummistreifen 40×40×2, selbstklebend", "–", "EPDM", "auf Prismaflächen"),
    (36, 1, "Stk", "Maßband selbstklebend, steigend, 300", "–", "Stahl", "Höhenskala"),
    (37, 4, "Stk", "Einschmelzmutter M5 (Bohrung Ø6,4)", "Normteil", "Messing", "verdeckt"),
    (40, 1, "Stk", "Zylinderschraube M8×20", "ISO 4762", "8.8", "Säule, o. Abb."),
    (41, 2, "Stk", "Zylinderschraube M6×12", "ISO 4762", "8.8", "Winkel/Platte, o. Abb."),
    (42, 2, "Stk", "Zylinderschraube M6×16", "ISO 4762", "8.8", "Profil 11 von unten, o. Abb."),
    (43, 4, "Stk", "Zylinderschraube M5×12", "ISO 4762", "8.8", "Spanner, o. Abb."),
    (44, 4, "Stk", "Senkschraube M5×20", "ISO 10642", "8.8", "Prisma-Backen, o. Abb."),
    (45, 2, "Stk", "Senkschraube M4×40", "ISO 10642", "8.8", "Pos. 8 + 3 + 4"),
    (46, 4, "Stk", "Senkschraube M4×16", "ISO 10642", "8.8", "Passfedern, Federhalter, o. Abb."),
    (47, 2, "Stk", "Zylinderschraube M5×16", "ISO 4762", "8.8", "Federhalter, o. Abb."),
    (48, 2, "Stk", "Zylinderschraube M4×10", "ISO 4762", "8.8", "Zeiger, o. Abb."),
    (49, 1, "Stk", "Sechskantmutter M4", "ISO 4032", "8", "Magnet"),
]


# =====================================================================
# Zusammenbau TFO-000
# =====================================================================
def zusammenbau(pdf, maschine, flasche):
    m = 0.25
    S = blatt(pdf, "A3q", "Zusammenbau", "TFO-000", "1:4", "–", "–", "≈ 5 kg",
              "Tisch-Flaschenöffner, Grundstellung NRW 0,5 l", "1/2", toleranz=False)
    T = [p["t"] for p in maschine]
    F = [p["t"] for p in flasche]
    ZP = M.ZP
    # Vorderansicht (Blick in +Y), Draufsicht darunter, Seitenansicht von links rechts daneben
    AV = Ansicht(S, 72, 165, m)
    AD = Ansicht(S, 72, 115, m)
    AL = Ansicht(S, 245, 165, m)
    sv = kanten_sichtbar(T, T, "vorne")
    zeichne_strecken(AV, sv)
    zeichne_strecken(AV, kanten_sichtbar(T, F, "vorne"), 0.18, "phantom")
    sd = kanten_sichtbar(T, T, "oben")
    zeichne_strecken(AD, [(u, v, u2, v2) for u, v, u2, v2 in sd])
    zeichne_strecken(AD, kanten_sichtbar(T, F, "oben"), 0.18, "phantom")
    sl = kanten_sichtbar(T, T, "links")
    zeichne_strecken(AL, sl)
    zeichne_strecken(AL, kanten_sichtbar(T, F, "links"), 0.18, "phantom")
    # Isometrie 1:5 unten rechts über dem Schriftfeld
    iso_t = kanten_sichtbar(T, T, "iso", res=0.6)
    AI = einpassen(S, iso_t, 300, 62, 405, 144)
    zeichne_strecken(AI, iso_t, 0.3)
    zeichne_strecken(AI, kanten_sichtbar(T, F, "iso", res=0.6), 0.18, "phantom")
    S.text(352, 150, "Isometrie (ohne Maßstab)", 3.0, ausr="m")

    # Mittellinien Flasche und Drehachse
    AV.mittellinie(0, M.STAND, 0, M.STAND + M.REF[2] + 2, 3)
    AV.kreuz(M.PX, ZP, 6)
    AD.kreuz(0, M.flaschen_y(M.REF[3]), M.REF[3] / 2)
    AL.mittellinie(-M.flaschen_y(M.REF[3]), M.STAND, -M.flaschen_y(M.REF[3]), M.STAND + M.REF[2] + 2, 3)

    # Hauptmaße
    alle = np.concatenate(T).reshape(-1, 3)
    xmin, ymin, zmin = alle.min(0)
    xmax, ymax, zmax = alle.max(0)
    AV.mass((xmin, 0), (xmax, 0), "h", -7, text=fz(round(xmax - xmin)))
    AV.mass((xmin, 0), (xmin, zmax), "v", -10, text=fz(round(zmax)))
    AV.mass((xmin, 0), (M.PX, ZP), "v", -22, text=f"{fz(ZP)} (205,5 … 304)")
    AD.mass((13.4, ymin), (M.PX, ymin), "h", -15)
    AD.mass((M.PX, ymin), (M.KNOPF_X, ymin), "h", -15)
    AD.mass((-95, ymin), (150, ymin), "h", -7)
    AD.mass((xmax, ymin), (xmax, ymax), "v", 8, text=fz(round(ymax - ymin)))
    AL.mass((-ymax, 0), (-ymin, 0), "h", -7, text=fz(round(ymax - ymin)))
    AL.mass((-ymin, 0), (-ymin, M.STAND), "v", 8)
    AL.mass((-ymin, 0), (-ymin, M.SPANN_Z), "v", 17)

    # Positionsnummern: (Pos, Ankerpunkt 3D, Seite)
    pos_v = [(8, (-8, -13, ZP + 18), "o"), (28, (0, -7, ZP + 9), "o"), (27, (0, -11, ZP - 3), "o"),
             (4, (36, -18, ZP - 21), "o"), (2, (54, 6, ZP - 52), "o"), (20, (80, -20, ZP + 6), "o"),
             (19, (M.PX + 34, -9, ZP + 49), "o"), (6, (90, 6, ZP + 52), "o"),
             (5, (100, -14, ZP + 78), "o"), (30, (130, -13, ZP + 22), "o"),
             (31, (130, -6, ZP + 60), "o"), (32, (130, -8.5, ZP + 72), "o"),
             (29, (162, -10, ZP + 45), "o"),
             (3, (250, -9, ZP + 4), "r"), (23, (370, -55, ZP + 8), "r"),
             (1, (-80, -145, 16), "u"), (7, (-50, 11, 70), "u"), (11, (-17, -140, 40), "u"),
             (25, (-8, -138, 70), "u"), (33, (130, -140, 5), "u")]
    pos_l = [(13, (80, 36, 425), "r"), (36, (100.3, 46, 385), "r"), (10, (60, 56, 330), "r"),
             (12, (100, 80, 30), "r")]
    pos_d = [(34, (-38, -68, 25), "l"), (26, (6, -40, 84), "l"), (35, (-22, 26, 80), "l"),
             (24, (370, -16, ZP + 15), "o")]
    ballons(S, AV, "vorne", pos_v, (AV.P(xmin, zmin), AV.P(xmax, zmax)), {"o": 10, "u": 17, "r": 10})
    ballons(S, AL, "links", pos_l, (AL.P(-ymax, zmin), AL.P(-ymin, zmax)), {"r": 30})
    ballons(S, AD, "oben", pos_d, (AD.P(xmin, ymin), AD.P(xmax, ymax)), {"l": 12, "o": 8})

    notizen(S, 25, 42, [
        "Flasche (NRW 0,5 l) als Anschlussteil in Strich-Zweipunktlinie dargestellt.",
        "Verdeckte Normteile und Schrauben siehe Stückliste Blatt 2 (\"verdeckt\", \"o. Abb.\").",
        "Maße in mm. Grundstellung: Hebel waagerecht, Spanner geschlossen.",
        "Verstellbereich Drehachse 205,5 … 304 über Tisch (Flaschenhöhe 171,5 … 270).",
    ], 2.5, "Hinweise")


def ballons(S, A, name, liste, bbox, abst):
    """Positionsnummern auf der angegebenen Seite der Ansicht aufreihen
    (o/u/l/r, Abstand zur Ansicht in abst), sortiert nach Lage des Ankerpunkts."""
    R = ansichtsbasis(name)
    (bx0, by0), (bx1, by1) = bbox
    seiten = {"o": [], "u": [], "l": [], "r": []}
    for pos, p3, s in liste:
        q = np.array(p3, float) @ R.T
        x, y = A.P(q[0], q[1])
        seiten[s].append((pos, x, y))
    teilung, r = 10.0, 4.0
    for s, l in seiten.items():
        if not l:
            continue
        idx = 1 if s in "ou" else 2
        l.sort(key=lambda e: e[idx])
        lage = [e[idx] for e in l]
        # gleichmäßig verteilen, Mindestabstand einhalten, Mitte beibehalten
        for i in range(1, len(lage)):
            lage[i] = max(lage[i], lage[i - 1] + teilung)
        versatz = (sum(e[idx] for e in l) - sum(lage)) / len(lage)
        lage = [p + versatz for p in lage]
        for (pos, x, y), p in zip(l, lage):
            if s == "o":
                ballon(S, p, by1 + abst["o"], x, y, pos, r)
            elif s == "u":
                ballon(S, p, by0 - abst["u"], x, y, pos, r)
            elif s == "r":
                ballon(S, bx1 + abst["r"], p, x, y, pos, r)
            else:
                ballon(S, bx0 - abst["l"], p, x, y, pos, r)


def ballon(S, xb, yb, x, y, pos, r):
    L = math.hypot(x - xb, y - yb) or 1
    S.linie(xb + (x - xb) / L * r, yb + (y - yb) / L * r, x, y, 0.18)
    S.kreis(x, y, 0.6, 0.1, fuellen=0.0)
    S.kreis(xb, yb, r, SCHMAL, fuellen=1.0)
    S.text(xb, yb - 1.6, str(pos), 3.5, ausr="m")


def stueckliste_blatt(pdf):
    S = blatt(pdf, "A3q", "Stückliste", "TFO-000", "–", "–", "–", "≈ 5 kg",
              "Tisch-Flaschenöffner", "2/2", toleranz=False)
    spalten = [("Pos.", 13), ("Menge", 14), ("Einh.", 12), ("Benennung", 100),
               ("Sachnummer / Norm", 68), ("Werkstoff", 46), ("Bemerkung", 137)]
    x0, y = 20, 287
    zh = 4.25
    def zeile(werte, fett=False, grau=None):
        nonlocal y
        x = x0
        if grau is not None:
            S.rechteck(x0, y - zh, x0 + 390, y, 0, fuellen=grau)
        for (kopf, b), wv in zip(spalten, werte):
            S.text(x + 1.5, y - zh + 1.4, wv, 2.5, fett)
            x += b
        S.linie(x0, y - zh, x0 + 390, y - zh, 0.18)
        y -= zh
    zeile([k for k, _ in spalten], True, 0.88)
    gruppe = None
    for pos, menge, einh, ben, norm, werk, bem in STUECKLISTE:
        g = "E" if pos < 10 else ("N" if pos < 40 else "S")
        if g != gruppe:
            gruppe = g
            zeile(["", "", "", {"E": "Eigenfertigungsteile", "N": "Norm- und Kaufteile",
                                "S": "Schrauben und Muttern"}[g], "", "", ""], True, 0.95)
        zeile([str(pos), str(menge), einh, ben, norm, werk, bem])
    x = x0
    for _, b in spalten[:-1]:
        x += b
        S.linie(x, 287, x, y, 0.18)


# =====================================================================
# Einzelteilzeichnungen
# =====================================================================
def tfo001(pdf):
    S = blatt(pdf, "A3q", "Grundplatte", "TFO-001", "1:2", "EN AW-5754 H111",
              "Platte 250×250×12", mtext(masse_kg("01_Grundplatte")))
    m = 0.5
    AD = Ansicht(S, 70, 75, m)            # Draufsicht
    AV = Ansicht(S, 70, 225, m)           # Vorderansicht darüber (Methode 1)
    AD.rechteck(0, 0, 245, 245)
    AV.rechteck(0, 0, 245, 12)
    # Bohrungen (u, v, Kennung, Art)
    loecher = [
        ("A1", 20, 20, "M6"), ("A2", 225, 20, "M6"), ("A3", 20, 225, "M6"), ("A4", 225, 225, "M6"),
        ("B1", 175, 181, "SB8"),
        ("C1", 217, 181, "M6"), ("C2", 175, 223, "M6"),
        ("D1", 53, 170, "SK5"), ("D2", 137, 170, "SK5"), ("D3", 65, 217, "SK5"), ("D4", 125, 217, "SK5"),
        ("E1", 95, 20, "SB6"), ("E2", 95, 50, "SB6"),
    ]
    for k, u, v, art in loecher:
        if art == "M6":
            AD.gewinde(u, v, 6)
            AV.bohrung_seite(u, 0, 12, 6, gewinde=6)
        elif art == "SB8":
            AD.bohrung(u, v, 9)
            AD.kreis(u, v, 7.5, "verdeckt")
            AV.bohrung_seite(u, 8.6, 12, 9)
            AV.rechteck(u - 7.5, 0, u + 7.5, 8.6, "verdeckt")
        elif art == "SB6":
            AD.bohrung(u, v, 6.6)
            AD.kreis(u, v, 5.5, "verdeckt")
            AV.bohrung_seite(u, 6.4, 12, 6.6)
            AV.rechteck(u - 5.5, 0, u + 5.5, 6.4, "verdeckt")
        else:  # Kegelsenkung von unten
            AD.bohrung(u, v, 5.5)
            AD.kreis(u, v, 5.2, "verdeckt")
            AV.poly([(u - 5.2, 0), (u - 2.75, 2.45), (u - 2.75, 12)], "verdeckt", False)
            AV.poly([(u + 5.2, 0), (u + 2.75, 2.45), (u + 2.75, 12)], "verdeckt", False)
            AV.mittellinie(u, 0, u, 12)
        x, y = AD.P(u, v)
        S.text(x + 2.4, y + 1.6, k, 2.5)
    # Bezugspunkt und Hauptmaße
    x, y = AD.P(0, 0)
    S.kreis(x, y, 1.6, SCHMAL)
    S.text(x - 3, y - 4.5, "0", 3.0)
    AD.mass((0, 0), (245, 0), "h", -10)
    AD.mass((0, 0), (0, 245), "v", -10)
    AV.mass((245, 0), (245, 12), "v", 8)
    # Bohrungstabelle (Koordinatenbemaßung)
    tx, ty = 232, 272
    S.text(tx, ty + 3, "Bohrungstabelle (Koordinaten ab Bezugspunkt 0)", 3.2, True)
    kopf = [("Kennung", 18), ("X", 14), ("Y", 14), ("Ausführung", 130)]
    ausf = {"M6": "M6 durchgehend", "SB8": "Ø9 durch, Senkung Ø15 × 8,6 tief von unten (DIN 974-1, ISO 4762 M8)",
            "SB6": "Ø6,6 durch, Senkung Ø11 × 6,4 tief von unten (DIN 974-1, ISO 4762 M6)",
            "SK5": "Ø5,5 durch, Kegelsenkung 90° Ø10,4 von unten (ISO 10642 M5)"}
    y = ty - 2
    def zeile(w, fett=False):
        nonlocal y
        x = tx
        for (_, b), t in zip(kopf, w):
            S.text(x + 1, y - 3.6, t, 2.4, fett)
            x += b
        y -= 5
        S.linie(tx, y, tx + 176, y, 0.18)
    S.linie(tx, y, tx + 176, y, 0.18)
    zeile([k for k, _ in kopf], True)
    for k, u, v, art in loecher:
        zeile([k, fz(u), fz(v), ausf[art]])
    notizen(S, 232, 178, [
        "Bezugspunkt 0 = vordere linke Ecke (Bedienerseite vorn).",
        "A: Gerätefüße (Pos. 33)   B: Säule (Pos. 10, Schraube Pos. 40)",
        "C: Winkel (Pos. 12)   D: Prisma-Backen (Pos. 7)   E: Spanner-Unterbau (Pos. 11)",
        "Alternativ Multiplex Birke 18 mm (Gewinde dann als Einschlagmuttern M6).",
        "Bohrbild C/D/E vor dem Bohren mit den Kaufteilen abgleichen.",
    ])


def tfo002(pdf):
    S = blatt(pdf, "A4h", "Schlittenplatte", "TFO-002", "1:1", "EN AW-5754 H111",
              "Flach 60×10, L = 110", mtext(masse_kg("02_Schlittenplatte")))
    AV = Ansicht(S, 72, 150, 1)            # Vorderansicht (Bedienerseite)
    AL = Ansicht(S, 172, 150, 1)           # von links (rechts daneben)
    AD = Ansicht(S, 72, 118, 1)            # Draufsicht (darunter)
    AV.rechteck(0, 0, 60, 110)
    AL.rechteck(0, 0, 10, 110)
    AD.rechteck(0, 0, 60, 10)
    AV.gewinde(30, 60, 8)
    AV.bohrung(30, 15, 8.5)
    AV.bohrung(30, 95, 8.5)
    for w in (34, 77):
        AV.bohrung(30, w, 4.5)
        AV.kreis(30, w, 4.2)
    for w in (90, 102):
        AV.gewinde(52, w, 5)
    # Seitenansicht: Blick von links, Vorderseite (y = 6) rechts
    for w, d, g in ((60, 8, 8), (15, 8.5, None), (95, 8.5, None), (90, 5, 5), (102, 5, 5)):
        AL.bohrung_seite(w, 0, 10, d, "u", gewinde=g)
    for w in (34, 77):
        AL.poly([(10, w - 4.2), (7.95, w - 2.25), (0, w - 2.25)], "verdeckt", False)
        AL.poly([(10, w + 4.2), (7.95, w + 2.25), (0, w + 2.25)], "verdeckt", False)
    # Draufsicht: 2x M4 für den Zeiger
    for u in (35, 50):
        AD.gewinde(u, 5, 4)
    # Maße
    # Höhen links von der Unterkante (Bezug), Federhalter-Gewinde rechts
    for i, w in enumerate((15, 34, 60, 77, 95, 110)):
        AV.mass((0, 0), (0 if w == 110 else 30, w), "v", -7 - 7 * i)
    AV.mass((60, 0), (52, 90), "v", 8)
    AV.mass((60, 0), (52, 102), "v", 15)
    AV.mass((0, 110), (30, 110), "h", 7)
    AV.mass((0, 110), (52, 110), "h", 14)
    AV.mass((0, 0), (60, 0), "h", -8)
    # Kennbuchstaben an den Bohrungen (Legende in den Hinweisen)
    for k, u, w in (("A", 30, 60), ("B", 30, 15), ("B", 30, 95), ("C", 30, 34), ("C", 30, 77),
                    ("D", 52, 90), ("D", 52, 102)):
        x, y = AV.P(u, w)
        S.text(x - 7.5 if u == 30 else x - 6.5, y + 2.0, k, 3.0, True)
    x, y = AD.P(35, 5)
    S.text(x + 2.5, y + 1.8, "E", 3.0, True)
    x, y = AD.P(50, 5)
    S.text(x + 2.5, y + 1.8, "E", 3.0, True)
    AL.mass((0, 0), (10, 0), "h", -8)
    AD.mass((0, 0), (35, 0), "h", -7)
    AD.mass((0, 0), (50, 0), "h", -14)
    AD.mass((0, 0), (0, 5), "v", -7)
    notizen(S, 25, 100, [
        "A  M8 durch (Drehachse, Pos. 20). Gewinde rechtwinklig, Schulter liegt plan an.",
        "B  2× Ø8,5 durch (Klemmhebel Pos. 19).",
        "C  2× Ø4,5 durch, Kegelsenkung 90° Ø8,4 vorn (Passfedern, Pos. 46).",
        "D  2× M5 durch (Federhalter, Pos. 47).     E  2× M4, 8 tief, oben (Zeiger, Pos. 48).",
        "Vorderseite = Seite zum Hebel. Passfedern Pos. 14/15 hinten mittig:",
        "Pos. 14 bei 24 … 44, Pos. 15 bei 68 … 86 (ab Unterkante), M4 mittig.",
    ], 2.5)


def tfo003(pdf):
    S = blatt(pdf, "A3q", "Hebel", "TFO-003", "1:1", "S235JR (1.0038)",
              "Flachstahl EN 10058 30×12, L = 365", mtext(masse_kg("03_Hebel")))
    AV = Ansicht(S, 30, 185, 1)
    AD = Ansicht(S, 30, 130, 1)
    AV.rechteck(0, 0, 365, 30)
    AD.rechteck(0, 0, 365, 12)
    AV.bohrung(60, 15, 12)
    AV.gewinde(350, 15, 10)
    AV.bohrung(142, 23, 5)
    for u in (10, 22):
        AD.langloch(u, 6, 4.5, 8.5)
        AV.linie(u - 4.25, 0, u - 4.25, 30, "verdeckt")
        AV.linie(u + 4.25, 0, u + 4.25, 30, "verdeckt")
        AV.mittellinie(u, 0, u, 30)
    AD.bohrung_seite(6, 54, 66, 12, "u")
    AD.bohrung_seite(6, 339.75 + 5.75, 354.25, 0, "u")
    AD.linie(354.25 - 8.5, 0, 354.25 - 8.5, 12, "verdeckt")
    AD.linie(345.75 + 8.5, 0, 345.75 + 8.5, 12, "verdeckt")
    AD.mittellinie(350, 0, 350, 12)
    AD.linie(139.5, 0, 139.5, 12, "verdeckt")
    AD.linie(144.5, 0, 144.5, 12, "verdeckt")
    AD.mittellinie(142, 0, 142, 12)
    AD.linie(54, 0, 54, 12, "verdeckt")
    AD.linie(66, 0, 66, 12, "verdeckt")
    AD.mittellinie(60, 0, 60, 12)
    # Maße
    AV.mass((0, 30), (365, 30), "h", 26)
    AV.mass((0, 30), (60, 30), "h", 8)
    AV.mass((0, 30), (142, 30), "h", 14)
    AV.mass((0, 30), (350, 30), "h", 20)
    AV.mass((365, 0), (365, 30), "v", 8)
    AV.mass((365, 0), (365, 15), "v", 18)
    AV.mass((142, 30), (142, 23), "v", 6)
    AD.mass((0, 0), (10, 0), "h", -8)
    AD.mass((0, 0), (22, 0), "h", -15)
    AD.mass((365, 0), (365, 12), "v", 8)
    AD.mass((0, 0), (0, 6), "v", -8)
    AV.hinweis((60 + 6 * 0.7, 15 - 6 * 0.7), -40, 18, "Ø12 H7 durch")
    AV.hinweis((350 - 5 * 0.7, 15 - 5 * 0.7), -140, 18, "M10 durch")
    AV.hinweis((142 + 2.5 * 0.7, 23 - 2.5 * 0.7), -40, 20, "Ø5 durch")
    AD.hinweis((22 + 2.5, 6 - 2), -30, 22, "2× Langloch 4,5 × 8,5 durch (Nachstellweg ±2)")
    notizen(S, 30, 100, [
        "Ø12 H7: Aufnahme Bundbuchsen Pos. 21 (von beiden Seiten einpressen).",
        "M10: Gewindestift Pos. 24 für Kugelknopf Pos. 23 (Kugel zeigt zur Vorderseite).",
        "Ø5: Öse der Zugfeder Pos. 29.  Langlöcher: Senkschrauben Pos. 45 zur Hakenleiste.",
        "Vorderseite = Seite des Kugelknopfs. Ecken und Kanten gebrochen.",
    ])


def tfo004(pdf):
    S = blatt(pdf, "A4h", "Hakenleiste", "TFO-004", "2:1", "C45 (1.0503)",
              "Flachstahl 35×10, L = 35", mtext(masse_kg("04_Hakenleiste")))
    m = 2
    AV = Ansicht(S, 55, 195, m)
    AD = Ansicht(S, 55, 105, m)
    f = 10 * math.tan(math.radians(30))
    AV.poly([(0, 10), (35, 10), (35, 0), (f, 0)])
    AD.rechteck(0, 0, 35, 35)
    AD.linie(f, 0, f, 35, "sichtbar", SCHMAL)
    for a in (16.6, 28.6):
        AD.gewinde(a, 15, 4)
        AV.bohrung_seite(a, 0, 10, 4, gewinde=4)
    AV.mass((0, 10), (35, 10), "h", 10)
    AV.mass((35, 0), (35, 10), "v", 8)
    AV.mass((0, 0), (f, 0), "h", -8, text="5,8")
    AV.linie(0, 10, 0, -2, "sichtbar", 0.18)          # Bezugslinie für den Fasenwinkel
    AV.winkelmass((0, 10), 7, 270, 270 + 30, "30°")
    AD.mass((0, 0), (16.6, 0), "h", -8)
    AD.mass((0, 0), (28.6, 0), "h", -16)
    AD.mass((35, 0), (35, 35), "v", 8)
    AD.mass((35, 0), (35, 15), "v", 18)
    AD.hinweis((28.6 + 1.5, 15 + 1.5), 45, 16, "2× M4 durch")
    AV.hinweis((0, 10), 75, 24, "Lippe scharfkantig (Kante -0, nicht verrunden)")
    notizen(S, 25, 76, [
        "Lippe (Kante bei 0) greift unter den Kronkorkenrand, zeigt zur Flasche.",
        "Optional härten: 50 + 5 HRC, danach Lippe nachschleifen.",
        "Lage in X über die Langlöcher im Hebel (TFO-003) nachstellbar.",
    ], 2.6)


def tfo005(pdf):
    S = blatt(pdf, "A4q", "Federhalter", "TFO-005", "1:1", "S235JR (1.0038)",
              "5.1: Flach 16×10   5.2: Flach 20×6", mtext(masse_kg("05_Federhalter")))
    # 5.1 Steg
    AV = Ansicht(S, 40, 115, 1)
    AD = Ansicht(S, 40, 88, 1)
    AV.rechteck(0, 0, 16, 53)
    AD.rechteck(0, 0, 16, 10)
    for w in (8, 20):
        AV.bohrung(8, w, 5.5)
    for u in (4, 12):
        AD.gewinde(u, 5, 4)
        AV.bohrung_seite(u, 45, 53, 4, gewinde=4)
    AV.mass((0, 0), (16, 0), "h", -7)
    AV.mass((16, 0), (16, 53), "v", 16)
    AV.mass((16, 0), (16, 8), "v", 6)
    AV.mass((16, 0), (16, 20), "v", 11)
    AD.mass((0, 0), (4, 0), "h", -6)
    AD.mass((0, 0), (12, 0), "h", -12)
    AD.mass((16, 0), (16, 10), "v", 6)
    AV.hinweis((8 - 2, 20 + 2), 135, 12, "2× Ø5,5 durch")
    AD.hinweis((4 - 1.5, 5 - 1.5), 220, 10, "2× M4, 8 tief")
    S.text(AV.P(8, 0)[0], 178, "5.1 Steg (1×)", 3.5, True, "m")
    # 5.2 Arm
    AD2 = Ansicht(S, 125, 125, 1)
    AV2 = Ansicht(S, 125, 172, 1)
    AD2.rechteck(0, 0, 80, 20)
    AV2.rechteck(0, 0, 80, 6)
    for u in (4, 12):
        AD2.bohrung(u, 15, 4.5)
        AD2.kreis(u, 15, 4.2)
    AD2.gewinde(36, 11, 6)
    AD2.bohrung(68, 11, 5)
    AD2.mass((0, 0), (80, 0), "h", -14)
    AD2.mass((0, 0), (36, 0), "h", -8)
    AD2.mass((80, 0), (80, 20), "v", 14)
    AD2.mass((80, 0), (80, 11), "v", 7)
    AD2.mass((0, 20), (4, 20), "h", 7)
    AD2.mass((0, 20), (12, 20), "h", 14)
    AD2.mass((0, 20), (0, 15), "v", -6)
    AD2.mass((68, 20), (80, 20), "h", 7, text="12")
    AV2.mass((80, 0), (80, 6), "v", 7)
    AD2.hinweis((36 + 2.5, 11 + 2.5), 50, 12, "M6 durch")
    AD2.hinweis((68 + 1.8, 11 - 1.8), -40, 10, "Ø5 durch")
    x, y = AD2.P(8, 15)
    S.text(x - 1.2, y - 7.5, "F", 3.0, True)
    S.text(AD2.P(40, 0)[0], 186, "5.2 Arm (1×)", 3.5, True, "m")
    notizen(S, 232, 150, [
        "F: 2× Ø4,5 durch,",
        "Kegelsenkung 90° Ø8,4 oben.",
        "Arm 5.2 auf Steg 5.1 mit",
        "2× Pos. 46 (ISO 10642 M4×16).",
        "Steg mit 2× Pos. 47",
        "(ISO 4762 M5×16) an die",
        "Schlittenplatte TFO-002.",
        "M6: Gewindestange Pos. 31.",
        "Ø5: Öse Zugfeder Pos. 29.",
    ], 2.5)


def tfo006(pdf):
    S = blatt(pdf, "A4h", "Zeiger", "TFO-006", "2:1", "EN AW-5754 H22",
              "Blech 3", mtext(masse_kg("06_Zeiger")))
    m = 2
    AD = Ansicht(S, 60, 120, m)
    AL = Ansicht(S, 150, 120, m)
    AD.poly([(0, 0), (29, 0), (29, 44), (21, 44), (21, 10), (0, 10)])
    for u in (5, 20):
        AD.bohrung(u, 5, 4.5)
    AL.rechteck(0, 0, 3, 44)
    AD.linie(21, 34, 29, 34, "sichtbar", SCHMAL)
    AD.mass((0, 0), (29, 0), "h", -10)
    AD.mass((0, 0), (5, 0), "h", -18 - 0)
    AD.mass((0, 0), (20, 0), "h", -26)
    AD.mass((29, 0), (29, 44), "v", 10)
    AD.mass((0, 0), (0, 10), "v", -8)
    AD.mass((21, 44), (29, 44), "h", 8)
    AD.mass((21, 44), (21, 34), "v", -8)
    AL.mass((0, 0), (3, 0), "h", -8)
    AD.hinweis((5 + 1.6, 5 + 1.6), 60, 14, "2× Ø4,5")
    AD.hinweis((25, 39), 20, 16, "Ablesebereich:\nUnterkante rot markieren")
    notizen(S, 25, 92, [
        "Ebenes Teil: lasern, wasserstrahlschneiden oder sägen/feilen.",
        "Auf Oberseite der Schlittenplatte mit 2× Pos. 48 (M4×10).",
        "Ablesekante = Unterkante (liegt 50 mm über der Drehachse).",
    ], 2.6)


def tfo007(pdf):
    S = blatt(pdf, "A3q", "Prisma-Backe", "TFO-007", "1:1", "PETG (3D-Druck)",
              "Druckteil", mtext(masse_kg("07_Prisma_Backe_rechts")),
              "rechts dargestellt, links spiegelbildlich", toleranz=True)
    AV = Ansicht(S, 80, 180, 1)          # von vorn
    AL = Ansicht(S, 185, 180, 1)         # von links
    AD = Ansicht(S, 80, 75, 1)           # Draufsicht
    poly = [(0, 37), (37, 0), (55, 0), (55, 77), (0, 77)]
    AD.poly(poly)
    AV.rechteck(0, 0, 55, 66)
    AV.linie(37, 0, 37, 66, "sichtbar", SCHMAL)
    AL.rechteck(0, 0, 77, 66)
    AL.linie(77 - 37, 0, 77 - 37, 66, "sichtbar", SCHMAL)
    for u, v in ((42, 14), (30, 61)):
        AD.kreis(u, v, 3.2, "verdeckt")
        AD.kreuz(u, v, 3.2)
        AV.bohrung_seite(u, 0, 10, 6.4)
    AV.rechteck(0, 18, 37, 58, "verdeckt")
    AD.mass((0, 0), (55, 0), "h", -8)
    AD.mass((0, 0), (37, 0), "h", -15)
    AD.mass((0, 0), (0, 77), "v", -16)
    AD.mass((0, 0), (0, 37), "v", -8)
    AD.mass((55, 0), (55, 14), "v", 7)
    AD.mass((55, 0), (55, 61), "v", 14)
    AD.mass((0, 0), (30, 61), "h", -22)
    AD.mass((0, 0), (42, 14), "h", -29)
    AD.winkelmass((37, 0), 12, 135, 180, "45°")
    AV.mass((55, 0), (55, 66), "v", 8)
    AV.mass((0, 0), (0, 18), "v", -7)
    AV.mass((0, 18), (0, 58), "v", -7)
    AD.hinweis((42 + 2.3, 14 - 2.3), -20, 30, "2× Ø6,4 × 10 tief von unten\nfür Einschmelzmutter M5")
    notizen(S, 285, 250, [
        "3D-Druck Bambu Lab P1S: PETG, 0,2 mm Schicht, 4 Wände,",
        "5 Böden/Decken, 40 % Gyroid, ohne Stütze, auf der Grundfläche liegend.",
        "Einschmelzmuttern Pos. 37 mit Lötkolben (ca. 230 °C) einsetzen.",
        "Gummistreifen Pos. 35 auf die Prismafläche kleben (Bereich 18 … 58,",
        "in der Vorderansicht verdeckt dargestellt).",
        "Linke Backe spiegelbildlich (Spiegelebene = Fläche bei Maß 0).",
    ], 2.6)


def tfo008(pdf):
    S = blatt(pdf, "A4h", "Magnethalter", "TFO-008", "2:1", "S235JR (1.0038)",
              "Flachstahl 20×5, L = 60", mtext(masse_kg("08_Magnethalter")))
    m = 2
    AD = Ansicht(S, 45, 130, m)
    AV = Ansicht(S, 45, 200, m)
    AD.rechteck(0, 0, 60, 20)
    AV.rechteck(0, 0, 60, 5)
    AD.bohrung(12, 10, 4.5)
    AV.bohrung_seite(12, 0, 5, 4.5)
    for u in (42, 54):
        AD.bohrung(u, 10, 4.5)
        AD.kreis(u, 10, 4.2)
        AV.poly([(u - 4.2, 5), (u - 2.25, 3.05), (u - 2.25, 0)], "verdeckt", False)
        AV.poly([(u + 4.2, 5), (u + 2.25, 3.05), (u + 2.25, 0)], "verdeckt", False)
        AV.mittellinie(u, 0, u, 5)
    AD.mass((0, 0), (60, 0), "h", -10)
    AD.mass((0, 0), (12, 0), "h", -18)
    AD.mass((0, 0), (42, 0), "h", -26)
    AD.mass((0, 0), (54, 0), "h", -34)
    AD.mass((60, 0), (60, 20), "v", 10)
    AD.mass((60, 0), (60, 10), "v", 18)
    AV.mass((60, 0), (60, 5), "v", 8)
    AD.hinweis((12 + 1.6, 10 + 1.6), 60, 16, "Ø4,5 (Magnet Pos. 27)")
    AD.hinweis((54 - 3, 10 + 3), 115, 26, "2× Ø4,5, Senkung 90° Ø8,4 oben")
    notizen(S, 25, 92, [
        "Liegt oben auf dem Hebel TFO-003, Senkungen oben.",
        "Gemeinsame Verschraubung mit Hakenleiste TFO-004: 2× Pos. 45.",
        "Magnet Pos. 27 mit Distanzhülse Pos. 28 und Mutter Pos. 49.",
    ], 2.6)


# =====================================================================
# Textseiten (A4 hoch)
# =====================================================================
def kopfzeile(S, titel, nr):
    S.linie(20, 282, 200, 282, 0.3)
    S.text(20, 284.5, f"Technische Dokumentation  {TITEL}", 2.6, grau=0.35)
    S.text(200, 284.5, "TFO-D01", 2.6, ausr="r", grau=0.35)
    S.linie(20, 15, 200, 15, 0.3)
    S.text(20, 10.5, f"Entwurf, Stand {DATUM}", 2.4, grau=0.35)
    S.text(200, 10.5, f"Seite {nr}", 2.4, ausr="r", grau=0.35)
    S.text(20, 268, titel, 6, True)
    return 256


def absatz(S, x, y, breite, text, h=3.0, fett=False, einzug=0):
    woerter = text.split()
    zeile = ""
    for w in woerter:
        probe = (zeile + " " + w).strip()
        if tb(probe, h, fett) > breite - einzug and zeile:
            S.text(x + einzug, y, zeile, h, fett)
            y -= h * 1.75
            zeile = w
        else:
            zeile = probe
    if zeile:
        S.text(x + einzug, y, zeile, h, fett)
        y -= h * 1.75
    return y - h * 0.5


def ueberschrift(S, y, t):
    S.text(20, y, t, 4.0, True)
    return y - 7


def liste(S, y, punkte, h=3.0, nummern=False):
    for i, p in enumerate(punkte, 1):
        marke = f"{i}." if nummern else "–"
        S.text(22, y, marke, h)
        y = absatz(S, 28, y, 172, p, h) + h * 0.3
    return y


def tabelle(S, x, y, spalten, zeilen, h=2.8, kopf=True):
    zh = h + 2.6
    breite = sum(b for _, b in spalten)
    if kopf:
        S.rechteck(x, y - zh, x + breite, y, 0, fuellen=0.88)
        xx = x
        for k, b in spalten:
            S.text(xx + 1.5, y - zh + 1.6, k, h, True)
            xx += b
        y -= zh
    for z in zeilen:
        xx = x
        for (k, b), t in zip(spalten, z):
            S.text(xx + 1.5, y - zh + 1.6, t, h)
            xx += b
        S.linie(x, y - zh, x + breite, y - zh, 0.15)
        y -= zh
    return y - 7


def deckblatt(pdf, iso_strecken):
    S = pdf.seite(210, 297)
    S.rechteck(20, 10, 200, 287, 0.7)
    S.text(110, 262, "Technische Dokumentation", 6, True, "m")
    S.text(110, 247, TITEL, 9, True, "m")
    S.text(110, 237, "Manuell betätigtes Tischgerät zum Öffnen von Kronkorken-Flaschen", 3.5, ausr="m")
    A = einpassen(S, iso_strecken, 40, 108, 180, 225)
    zeichne_strecken(A, iso_strecken, 0.3)
    y = 92
    tabelle(S, 40, y, [("Dokument", 55), ("Angabe", 85)], [
        ("Dokumentnummer", "TFO-D01"), ("Zeichnungssatz", "TFO-000 … TFO-008"),
        ("Änderungsindex", "A"), ("Ausgabedatum", DATUM),
        ("Dokumentenstatus", "Entwurf, nicht freigegeben"),
        ("Erstellt durch", "KI-Entwurf (Prüfung durch Fachkraft erforderlich)"),
    ], 3.0)
    S.text(110, 22, "Alle Maße in mm. Zeichnungen nach Projektionsmethode 1 (DIN ISO 5456-2).", 2.8,
           ausr="m", grau=0.3)


def inhalt_seite(pdf, eintraege):
    S = pdf.seite(210, 297)
    y = kopfzeile(S, "Inhalt", 2)
    rows = [(str(i), t, s) for i, (t, s) in enumerate(eintraege, 1)]
    y = tabelle(S, 20, y, [("Nr.", 12), ("Inhalt", 120), ("Seite / Blatt", 48)], rows, 3.0)
    y = ueberschrift(S, y - 4, "Zeichnungsverzeichnis")
    rows = [(s, t, f, b) for s, t, f, b in BLAETTER_PLAN]
    tabelle(S, 20, y, [("Sachnummer", 32), ("Benennung", 90), ("Format", 25), ("Blatt", 33)], rows, 3.0)


BLAETTER_PLAN = [
    ("TFO-000", "Zusammenbau", "A3", "1/2"), ("TFO-000", "Stückliste", "A3", "2/2"),
    ("TFO-001", "Grundplatte", "A3", "1/1"), ("TFO-002", "Schlittenplatte", "A4", "1/1"),
    ("TFO-003", "Hebel", "A3", "1/1"), ("TFO-004", "Hakenleiste", "A4", "1/1"),
    ("TFO-005", "Federhalter (Baugruppe)", "A4", "1/1"), ("TFO-006", "Zeiger", "A4", "1/1"),
    ("TFO-007", "Prisma-Backe", "A4", "1/1"), ("TFO-008", "Magnethalter", "A4", "1/1"),
]


def daten_seite(pdf):
    S = pdf.seite(210, 297)
    y = kopfzeile(S, "1  Technische Daten und Funktion", 3)
    y = ueberschrift(S, y, "1.1 Technische Daten")
    ref = M.REF
    y = tabelle(S, 20, y, [("Merkmal", 80), ("Wert", 100)], [
        ("Abmessungen B × T × H", "485 × 287 × 426 mm"),
        ("Grundfläche (Platte)", "245 × 245 mm"),
        ("Masse", "ca. 5 kg"),
        ("Flaschen (Kronkorken 26 mm)", "Höhe 171,5 … 270 mm, Ø 57 … 80 mm"),
        ("Verstellbereich Drehachse", "205,5 … 304 mm über Tisch"),
        ("Hebelübersetzung", "ca. 4,4 : 1 (Haken 66 mm, Knopf 290 mm)"),
        ("Hebelweg", "20° (ca. 100 mm am Knopf)"),
        ("Handkraft (Abschätzung)", "ca. 25 … 50 N"),
        ("Spannhub Schubstangenspanner", "40 mm"),
        ("Knopfhöhe bei Tischhöhe 750 mm", "ca. 955 … 1055 mm über Boden"),
        ("Bedienung", "1 Person: links spannen, rechts öffnen"),
    ], 3.0)
    y = ueberschrift(S, y, "1.2 Funktionsbeschreibung")
    y = absatz(S, 20, y, 180, "Die Flasche wird vorn auf die Gummimatte gestellt und mit dem "
               "Schubstangenspanner (Pos. 25) in das 90°-Prisma (Pos. 7) geschoben. Das Prisma "
               "zentriert jede Flasche quer zur Bedienrichtung (X). Ein anderer Durchmesser "
               "verschiebt die Flasche nur in Bedienrichtung (Y): Mitte = Scheitel − r · 1,414.")
    y = absatz(S, 20, y, 180, "Die Hakenleiste (Pos. 4) liegt genau in dieser Richtung. Beim "
               "Spannen gleitet der Kronkorkenrand über die Lippe, ohne dass etwas eingestellt "
               "werden muss. Drückt der Bediener den Kugelknopf (Pos. 23) nach unten, dreht der "
               "Hebel (Pos. 3) um die Passschraube (Pos. 20). Die Lippe hebt den Kronkorken an "
               "einer Seite ab, der Magnet (Pos. 27) hält ihn fest. Die Zugfeder (Pos. 29) holt "
               "den Hebel gegen den einstellbaren Puffer (Pos. 30) zurück.")
    y = absatz(S, 20, y, 180, "Für eine andere Flaschensorte wird nur der Schlitten (Pos. 2) "
               "nach Lösen der beiden Klemmhebel (Pos. 19) verschoben. Der Zeiger (Pos. 6) zeigt "
               "auf dem Maßband (Pos. 36) direkt die Flaschenhöhe.")
    y = ueberschrift(S, y, "1.3 Auslegung")
    y = liste(S, y, [
        "Abhebekraft am Haken angenommen 100 … 200 N. Daraus ergeben sich 23 … 45 N Handkraft "
        "plus ca. 4 N aus Feder und Hebelgewicht. Am ersten Muster messen (Federwaage am Knopf).",
        "Rückholfeder: Moment aus Hebelgewicht ca. 1,3 Nm, bei 82 mm Hebelarm ca. 15 N "
        "Vorspannung. Federweg bei 20° ca. 28 mm.",
        "Kronkorken nach DIN EN 17177: Höhe 6 mm, Außen-Ø vor dem Verschließen 32,1 mm. "
        "Annahme verschlossen ca. 28,8 mm. Die Lippe sitzt 1,5 mm unter dem Rand, die Lage in "
        "X lässt sich über die Langlöcher nachstellen.",
    ])


def montage_seite(pdf):
    S = pdf.seite(210, 297)
    y = kopfzeile(S, "2  Montageanleitung", 4)
    y = absatz(S, 20, y, 180, "Werkzeug: Innensechskantschlüssel 2,5 / 3 / 4 / 5 / 6, Gabelschlüssel "
               "7 / 10, Lötkolben für Einschmelzmuttern, Winkel, Messschieber, mittelfeste "
               "Schraubensicherung. Positionsnummern siehe Stückliste TFO-000 Blatt 2.")
    y = liste(S, y, [
        "Gerätefüße (33) in die Gewinde A1…A4 der Grundplatte (1) schrauben.",
        "Einschmelzmuttern (37) in die Prisma-Backen (7) setzen. Backen mit 4× Senkschraube (44) "
        "von unten an der Platte befestigen (Bohrungen D). Gummistreifen (35) auf die "
        "Prismaflächen kleben.",
        "Säule (10): unten Gewinde M8 in die Kernbohrung schneiden. Von unten mit (40) "
        "anschrauben (Bohrung B). Winkelsätze (12) einsetzen und mit (41) auf die Platte "
        "schrauben (Bohrungen C). Rechtwinkligkeit mit dem Winkel prüfen.",
        "Profilstück (11) mit Hammermuttern (17) und 2× (42) von unten befestigen (Bohrungen E). "
        "Schubstangenspanner (25) mit Hammermuttern (18) und 4× (43) oben aufschrauben. "
        "Gummi-Druckkappe (26) auf die Druckschraube stecken.",
        "Schlitten vormontieren: Passfedern (14, 15) mit (46) hinten an die Schlittenplatte (2). "
        "Zeiger (6) mit 2× (48) oben aufschrauben. Federhalter (5): Arm 5.2 mit 2× (46) auf "
        "Steg 5.1, dann mit 2× (47) vorn an die Platte. Gewindestange (31) mit Muttern (32) "
        "und Gummipuffer (30) eindrehen.",
        "Klemmhebel (19) durch die Platte stecken und Hammermuttern (16) aufdrehen. Schlitten "
        "mit den Passfedern in die vordere Nut der Säule schieben, Hammermuttern einschwenken, "
        "leicht klemmen.",
        "Bundbuchsen (21) von beiden Seiten in den Hebel (3) pressen. Passschraube (20) durch "
        "die Buchsen und die Scheibe (22) in die Platte schrauben, bis die Schulter plan "
        "anliegt. Der Hebel muss sich leicht und ohne Spiel drehen.",
        "Gewindestift (24) mit Schraubensicherung in den Hebel, Kugelknopf (23) aufschrauben.",
        "Hakenleiste (4) unter und Magnethalter (8) auf den Hebel legen, mit 2× (45) durch die "
        "Langlöcher verschrauben (noch nicht fest). Distanzhülse (28) und Magnet (27) mit "
        "Mutter (49) befestigen.",
        "Zugfeder (29) in die Bohrung Ø5 im Hebel und im Federhalter einhängen. Puffer so "
        "einstellen, dass der Hebel waagerecht steht.",
        "Gummimatte (34) vorn auf die Grundplatte kleben.",
        "Kalibrieren siehe Abschnitt 3.2, danach Funktionsprüfung nach Abschnitt 4.",
    ], 3.0, True)


def einstell_seite(pdf):
    S = pdf.seite(210, 297)
    y = kopfzeile(S, "3  Einstellung und Bedienung", 5)
    y = ueberschrift(S, y, "3.1 Einstelltabelle (Flaschenmaße VLB, Stand Jan. 2025)")
    rows = []
    for fid, name, H, D, _ in sorted(M.FLASCHEN, key=lambda f: -f[2]):
        rows.append((name, fz(H), fz(D), fz(H), fz(M.drehachse_z(H)), fz(M.flaschen_y(D))))
    y = tabelle(S, 20, y, [("Flasche", 42), ("Höhe", 20), ("Ø", 18), ("Skala auf", 26),
                           ("Drehachse ü. Tisch", 38), ("Flaschenmitte Y", 36)], rows, 2.9)
    y = ueberschrift(S, y, "3.2 Erstmaliges Kalibrieren")
    y = liste(S, y, [
        "Referenzflasche NRW 0,5 l (H = 260) einlegen und spannen.",
        "Schlitten so einstellen, dass die Oberkante der Hakenleiste ca. 1,5 mm unter dem "
        "Kronkorkenrand liegt. Klemmhebel festziehen.",
        "Hakenleiste in den Langlöchern so verschieben, dass die Lippe ca. 1 mm unter den Rand "
        "greift, ohne das Glas zu berühren. Schrauben (45) festziehen.",
        "Maßband (36) so an die Säule kleben, dass die Unterkante des Zeigers auf 260 steht.",
    ], 3.0, True)
    y = ueberschrift(S, y, "3.3 Bedienung (eine Person)")
    y = liste(S, y, [
        "Bei Sortenwechsel: Klemmhebel lösen, Zeiger auf die Flaschenhöhe stellen, festziehen.",
        "Spanner öffnen (Griff zurück) und die Flasche vorn auf die Gummimatte stellen.",
        "Mit der linken Hand spannen: Die Flasche wird ins Prisma geschoben, der "
        "Kronkorkenrand gleitet über die Lippe.",
        "Mit der rechten Hand den Kugelknopf gleichmäßig nach unten drücken, bis der "
        "Kronkorken abspringt.",
        "Hebel loslassen, Kronkorken vom Magneten nehmen, Spanner öffnen, Flasche entnehmen.",
    ], 3.0, True)


def wartung_seite(pdf):
    S = pdf.seite(210, 297)
    y = kopfzeile(S, "4  Prüfung, Wartung und Sicherheit", 6)
    y = ueberschrift(S, y, "4.1 Funktionsprüfung nach der Montage")
    y = liste(S, y, [
        "Hebel dreht leichtgängig, ohne Spiel. Er kehrt sicher an den Puffer zurück.",
        "Säule steht rechtwinklig zur Platte, der Schlitten klemmt bei angezogenen Klemmhebeln "
        "ohne Rutschen.",
        "Spanner hält jede Flaschensorte spielfrei. Die Druckschraube darauf einstellen, nicht "
        "übermäßig vorspannen.",
        "Probeöffnen mit je einer Flasche der kleinsten und der größten Sorte. Dabei die "
        "Handkraft messen.",
    ], 3.0)
    y = ueberschrift(S, y, "4.2 Wartung")
    y = tabelle(S, 20, y, [("Bauteil", 50), ("Maßnahme", 95), ("Intervall", 35)], [
        ("Hakenleiste (4)", "Lippe auf Verschleiß/Grat prüfen, nachschleifen", "monatlich"),
        ("Bundbuchsen (21)", "wartungsfrei, bei Spiel tauschen", "bei Bedarf"),
        ("Gummiteile (26, 30, 34, 35)", "auf Risse prüfen, ersetzen", "jährlich"),
        ("Schraubverbindungen", "nachziehen", "halbjährlich"),
        ("Magnet (27)", "von Kronkorken und Spänen befreien", "bei Bedarf"),
    ], 2.9)
    y = ueberschrift(S, y, "4.3 Sicherheitshinweise")
    y = liste(S, y, [
        "Glas kann unter Punktlast brechen. Spannkraft begrenzen, Gummikappe und Gummistreifen "
        "nie weglassen. Beim ersten Test Schutzbrille tragen.",
        "Die Lippe der Hakenleiste ist scharfkantig. Beim Einstellen Handschuhe tragen.",
        "Quetschstelle zwischen Hebel und Puffer bzw. Federhalter: nicht in den Schwenkbereich "
        "greifen.",
        "Gerät auf ebener, rutschfester Unterlage betreiben. Nicht von Kindern bedienen lassen.",
    ], 3.0)
    y = ueberschrift(S, y, "4.4 Quellen")
    liste(S, y, [
        "VLB Berlin: Einheitliche Leergut-GTIN der Standardpoolflaschen (Stand Jan. 2025).",
        "VLB Berlin / Deutscher Brauer-Bund: Technische Lieferbedingungen Kronenkorken (2016).",
        "DIN EN 17177: Glasverpackungen, Kronenkorken 26 mm Durchmesser, 6 mm Höhe.",
    ], 2.8)


def stueckliste_md():
    """Stueckliste.md aus derselben Datenquelle wie die Zeichnung erzeugen."""
    z = ["# Tisch-Flaschenöffner – Stückliste", "",
         "Diese Datei wird von `zeichnungen.py` erzeugt. Maßgebend für die Fertigung ist der "
         "Zeichnungssatz in [`Technische_Dokumentation_TFO.pdf`](Technische_Dokumentation_TFO.pdf) "
         "(Zusammenbau TFO-000, Einzelteile TFO-001 … TFO-008, Montage, Einstellung, Wartung).", "",
         "| Pos | Menge | Einh. | Benennung | Sachnummer / Norm | Werkstoff | Bemerkung |",
         "|---:|---:|---|---|---|---|---|"]
    gruppe = None
    for pos, menge, einh, ben, norm, werk, bem in STUECKLISTE:
        g = "Eigenfertigungsteile" if pos < 10 else ("Norm- und Kaufteile" if pos < 40 else
                                                     "Schrauben und Muttern")
        if g != gruppe:
            gruppe = g
            z.append(f"| | | | **{g}** | | | |")
        z.append(f"| {pos} | {menge} | {einh} | {ben} | {norm} | {werk} | {bem} |")
    z += ["", "## Einstelltabelle (Flaschenmaße VLB, Stand Jan. 2025)", "",
          "| Flasche | Höhe | Ø | Skala auf | Drehachse über Tisch | Flaschenmitte Y |",
          "|---|---:|---:|---:|---:|---:|"]
    for fid, name, H, D, _ in sorted(M.FLASCHEN, key=lambda f: -f[2]):
        z.append(f"| {name} | {fz(H)} | {fz(D)} | {fz(H)} | {fz(M.drehachse_z(H))} | "
                 f"{fz(M.flaschen_y(D))} |")
    z += ["", "## Eigenfertigung auf einen Blick", "",
          "| Pos | Zeichnung | Halbzeug | Masse |", "|---:|---|---|---:|"]
    for pos, teil, halb in ((1, "01_Grundplatte", "Alu-Platte 250×250×12"),
                            (2, "02_Schlittenplatte", "Alu-Flach 60×10, L 110"),
                            (3, "03_Hebel", "Flachstahl 30×12, L 365"),
                            (4, "04_Hakenleiste", "Flachstahl C45 35×10, L 35"),
                            (5, "05_Federhalter", "Flachstahl 16×10 + 20×6"),
                            (6, "06_Zeiger", "Alu-Blech 3"),
                            (7, "07_Prisma_Backe_rechts", "3D-Druck PETG (P1S)"),
                            (8, "08_Magnethalter", "Flachstahl 20×5, L 60")):
        z.append(f"| {pos} | TFO-00{pos} | {halb} | {mtext(masse_kg(teil))} |")
    z += ["", "## Annahmen", "",
          "- Abhebekraft am Kronkorken 100 … 200 N (geschätzt), am ersten Muster messen.",
          "- Außen-Ø des verschlossenen Kronkorkens ca. 28,8 mm (ohne Primärquelle), "
          "Lippe über Langlöcher nachstellbar.",
          "- Bohrbild von Schubstangenspanner und Winkelsätzen vor dem Bohren mit den Kaufteilen "
          "abgleichen.", "",
          "## Quellen", "",
          "- VLB Berlin: [Einheitliche Leergut-GTIN der Standardpoolflaschen]"
          "(https://www.vlb-berlin.org/sites/default/files/2021-05/Einheitliche-Pfandartikelnummern-"
          "Standardpoolflaschen-GTIN-Basis_StandApr2021_0.pdf) (Stand Jan. 2025)",
          "- VLB Berlin: [Technische Lieferbedingungen Kronenkorken]"
          "(https://www.vlb-berlin.org/sites/default/files/2020-04/STLB%20Kronenkorken_November%202016_0.pdf)",
          "- [DIN EN 17177](https://www.dinmedia.de/en/standard/din-en-17177/314562097): "
          "Kronenkorken 26 mm Durchmesser, 6 mm Höhe", ""]
    (Path(__file__).parent / "Stueckliste.md").write_text("\n".join(z), encoding="utf-8")


# =====================================================================
def main():
    maschine, flasche = modell()
    T = [p["t"] for p in maschine]
    F = [p["t"] for p in flasche]
    print("Berechne Isometrie für das Deckblatt …")
    iso = kanten_sichtbar(T, T, "iso", res=0.6)
    pdf = PDF()
    deckblatt(pdf, iso)
    inhalt_seite(pdf, [("Deckblatt", "1"), ("Inhalt, Zeichnungsverzeichnis", "2"),
                       ("Technische Daten und Funktion", "3"), ("Montageanleitung", "4"),
                       ("Einstellung und Bedienung", "5"), ("Prüfung, Wartung, Sicherheit", "6"),
                       ("Zusammenbau TFO-000 Blatt 1", "7"), ("Stückliste TFO-000 Blatt 2", "8"),
                       ("Einzelteilzeichnungen TFO-001 … TFO-008", "9 … 16")])
    daten_seite(pdf)
    montage_seite(pdf)
    einstell_seite(pdf)
    wartung_seite(pdf)
    print("Berechne Zusammenbauansichten (Verdeckungsrechnung) …")
    zusammenbau(pdf, maschine, flasche)
    stueckliste_blatt(pdf)
    for f in (tfo001, tfo002, tfo003, tfo004, tfo005, tfo006, tfo007, tfo008):
        f(pdf)
    pdf.speichern(AUSGABE)
    stueckliste_md()
    print(f"{AUSGABE.name}: {len(pdf.seiten)} Seiten, Stueckliste.md aktualisiert")
    import os
    pruef = os.environ.get("TFO_SVG")          # optional: Seiten als SVG zur Sichtprüfung
    if pruef:
        Path(pruef).mkdir(parents=True, exist_ok=True)
        for i, s in enumerate(pdf.seiten, 1):
            (Path(pruef) / f"seite_{i:02d}.svg").write_text(s.als_svg(), encoding="utf-8")


if __name__ == "__main__":
    main()
