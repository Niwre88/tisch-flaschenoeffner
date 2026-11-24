"""
STEP-Baugruppe (AP214, Namen und Farben) des Flaschenöffner-Automaten TFO-A, Index D.
Die Geometrie stammt vollständig aus modell_d.py. Die 6 Mover stehen an ihren Stationen.

Aufruf:  python erzeuge_step.py      ->  TFO-A_Flaschenoeffner_Automatik.step
"""
import sys
from pathlib import Path

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
import modell_d as A  # noqa: E402

AUSGABE = HIER / "TFO-A_Flaschenoeffner_Automatik.step"


def main():
    A.aufbauen()
    asm = A.baugruppe(mit_flaschen=True)
    print(f"  {len(A.TEILE)} Teile (davon Mover-Satz × {A.N_MOVER}) – schreibe STEP …")
    asm.export(str(AUSGABE)) if hasattr(asm, "export") else asm.save(str(AUSGABE))
    txt = AUSGABE.read_text(encoding="latin-1")
    txt = txt.replace("FILE_NAME('Open CASCADE Shape Model'", "FILE_NAME('TFO-A Flaschenoeffner-Automat Index D'", 1)
    txt = txt.replace("FILE_DESCRIPTION(('Open CASCADE Model')",
                      "FILE_DESCRIPTION(('TFO-A Flaschenoeffner-Automat mit Magnetbahn und Orbital-Entboerdler')", 1)
    AUSGABE.write_text(txt, encoding="latin-1", newline="\n")
    print(f"{AUSGABE.name}: {AUSGABE.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
