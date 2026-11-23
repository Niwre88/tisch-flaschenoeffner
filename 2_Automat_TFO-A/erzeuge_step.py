"""
STEP-Baugruppe (AP214, Namen und Farben) des Flaschenöffner-Automaten TFO-A, Index B.
Die Geometrie stammt vollständig aus modell_a.py.

Aufruf:  python erzeuge_step.py      ->  TFO-A_Flaschenoeffner_Automatik.step
"""
import sys
from pathlib import Path

HIER = Path(__file__).parent
sys.path.insert(0, str(HIER))
import modell_a as A  # noqa: E402

AUSGABE = HIER / "TFO-A_Flaschenoeffner_Automatik.step"


def main():
    A.aufbauen()
    asm = A.baugruppe(mit_flaschen=True)
    print(f"  {len(A.TEILE)} Teile in {len(A.gruppen())} Unterbaugruppen + 8 Flaschen – schreibe STEP …")
    asm.export(str(AUSGABE)) if hasattr(asm, "export") else asm.save(str(AUSGABE))
    txt = AUSGABE.read_text(encoding="latin-1")
    txt = txt.replace("FILE_NAME('Open CASCADE Shape Model'", "FILE_NAME('TFO-A Flaschenoeffner-Automat Index B'", 1)
    txt = txt.replace("FILE_DESCRIPTION(('Open CASCADE Model')",
                      "FILE_DESCRIPTION(('TFO-A Flaschenoeffner-Automat mit Bedienfach, Baugruppe')", 1)
    AUSGABE.write_text(txt, encoding="latin-1", newline="\n")
    print(f"{AUSGABE.name}: {AUSGABE.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
