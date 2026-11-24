(* ============================================================================
   FB_Oeffnungsstation – Schrittkette S1 … S9 (siehe PDF Kap. 3 und GRAFCET)
   Achsen: Z (M1), Rotor (M2), Zustellring (M3). Die Zustellung ist eine elektronische
   Kurvenscheibe: Phasenversatz M3 gegenüber M2 = f(Rotorwinkel).
   ============================================================================ *)
FUNCTION_BLOCK FB_Oeffnungsstation
VAR_INPUT
    bStart       : BOOL;     (* ein gemessener Mover steht vor dem Kopf *)
    nMover       : INT;      (* Index des Movers 1 … 6 *)
    fZc          : LREAL;    (* Kronkorken-Oberkante dieser Flasche *)
    bMitKronkorken : BOOL;
END_VAR
VAR_OUTPUT
    bMoverEinfahren : BOOL;  (* an MAIN: Mover in den Kopf fahren *)
    bMoverAusfahren : BOOL;  (* an MAIN: Mover weiter zur Ausgabe *)
    bFertig     : BOOL;
    bStoerung   : BOOL;
    nSchritt    : INT;
END_VAR
VAR_IN_OUT
    AchseZ, AchseRotor, AchseZustell : AXIS_REF;
END_VAR
VAR
    fbZ         : MC_MoveAbsolute;
    fbRotor     : MC_MoveAbsolute;
    fbRotorRel  : MC_MoveRelative;
    fbKurve     : MC_CamIn;          (* Tc2_MC2_Camming: Zustellring folgt dem Rotor *)
    fbKurveAus  : MC_CamOut;
    tSchritt    : TON;
    tAbfuhr     : TON;
    rtZaehl     : R_TRIG;
    fRotorStart : LREAL;
END_VAR

tSchritt(IN := TRUE);
CASE nSchritt OF
0:  (* Grundstellung / bereit *)
    bFertig := FALSE;
    IF bStart THEN
        IF bMitKronkorken AND fZc >= GVL_Anlage.ZC_MIN - 2 AND fZc <= GVL_Anlage.ZC_MAX + 2 THEN
            nSchritt := 2; tSchritt(IN := FALSE);
        ELSE
            GVL_Anlage.sMeldung := 'Flasche ohne Kronkorken oder Höhe unplausibel: Ausgabe ohne Öffnen';
            nSchritt := 7; tSchritt(IN := FALSE);
        END_IF
    END_IF

2:  (* S2 Einstellen: Z auf ZC, Rotorschlitz zur Einfahrt *)
    fbZ(Axis := AchseZ, Execute := TRUE, Position := fZc, Velocity := 150);
    fbRotor(Axis := AchseRotor, Execute := TRUE, Position := GVL_Anlage.SCHLITZ_EINFAHRT, Velocity := 720);
    IF fbZ.Done AND fbRotor.Done THEN
        fbZ(Axis := AchseZ, Execute := FALSE); fbRotor(Axis := AchseRotor, Execute := FALSE);
        bMoverEinfahren := TRUE; nSchritt := 3; tSchritt(IN := FALSE);
    ELSIF tSchritt.Q AND tSchritt.PT = T#2S THEN bStoerung := TRUE;
    END_IF

3:  (* S3 Einfahren: MAIN fährt den Mover, meldet über bStart = FALSE/TRUE zurück *)
    IF NOT bStart THEN               (* MAIN setzt bStart zurück, sobald der Mover in Position ist *)
        bMoverEinfahren := FALSE;
        fRotorStart := AchseRotor.NcToPlc.ActPos;
        nSchritt := 4; tSchritt(IN := FALSE);
    END_IF

4:  (* S4 Entbördeln: Zustellring über Kurvenscheibe an den Rotor koppeln, 2 Umdrehungen *)
    fbKurve(Master := AchseRotor, Slave := AchseZustell, Execute := TRUE, CamTableID := 1);
    fbRotorRel(Axis := AchseRotor, Execute := fbKurve.InSync,
               Distance := 360.0 * GVL_Anlage.ROTOR_UMDREHUNGEN, Velocity := GVL_Anlage.ROTOR_DREHZAHL);
    IF fbRotorRel.Done THEN
        fbRotorRel(Axis := AchseRotor, Execute := FALSE); fbKurve(Master := AchseRotor, Slave := AchseZustell, Execute := FALSE);
        fbKurveAus(Slave := AchseZustell, Execute := TRUE);
        nSchritt := 5; tSchritt(IN := FALSE);
    ELSIF fbRotorRel.Error OR fbKurve.Error THEN
        bStoerung := TRUE;           (* Momentgrenze: Rollen klemmen *)
    END_IF

5:  (* S5 Entlüften *)
    fbKurveAus(Slave := AchseZustell, Execute := FALSE);
    tSchritt(IN := TRUE, PT := GVL_Anlage.T_ENTLUEFTEN);
    IF tSchritt.Q THEN nSchritt := 6; tSchritt(IN := FALSE); END_IF

6:  (* S6 Abheben: Kronkorken hängt am Überband *)
    fbZ(Axis := AchseZ, Execute := TRUE, Position := fZc + GVL_Anlage.ABHEBEN, Velocity := 50);
    IF fbZ.Done THEN
        fbZ(Axis := AchseZ, Execute := FALSE);
        IF NOT GVL_Anlage.bKorkAmBand THEN
            GVL_Anlage.sMeldung := 'Kronkorken nicht am Überband – Station prüfen';
        END_IF
        nSchritt := 7; tSchritt(IN := FALSE);
    END_IF

7:  (* S7 Ausfahren: Schlitz zur Ausfahrt, Mover fährt weiter, Bänder ein *)
    fbRotor(Axis := AchseRotor, Execute := TRUE, Position := GVL_Anlage.SCHLITZ_AUSFAHRT, Velocity := 720);
    IF fbRotor.Done THEN
        fbRotor(Axis := AchseRotor, Execute := FALSE);
        bMoverAusfahren := TRUE;
        GVL_Anlage.nUeberband := 16000; GVL_Anlage.nSteigband := 20000;
        nSchritt := 8;
    END_IF

8:  (* S8 Abfuhr: Bänder laufen, bis -B11 den Kronkorken zählt *)
    bMoverAusfahren := FALSE;
    rtZaehl(CLK := GVL_Anlage.bKorkZaehlung);
    tAbfuhr(IN := TRUE, PT := GVL_Anlage.T_ABFUHR_MAX);
    IF rtZaehl.Q THEN
        GVL_Anlage.nKronkorken := GVL_Anlage.nKronkorken + 1;
    END_IF
    IF rtZaehl.Q OR tAbfuhr.Q OR NOT bMitKronkorken THEN
        IF tAbfuhr.Q AND bMitKronkorken THEN
            GVL_Anlage.sMeldung := 'Kronkorken nicht in der Rutsche gezählt';
        END_IF
        GVL_Anlage.nUeberband := 0; GVL_Anlage.nSteigband := 0;
        tAbfuhr(IN := FALSE);
        GVL_Anlage.nGeoeffnet := GVL_Anlage.nGeoeffnet + SEL(bMitKronkorken, 0, 1);
        bFertig := TRUE; nSchritt := 0;
    END_IF
END_CASE
