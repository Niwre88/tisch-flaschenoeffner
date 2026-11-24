(* ============================================================================
   MAIN – Mover-Disposition, Messen, Laden, Ausgabe, Anzeige
   Jeder Mover fährt für sich zur nächsten freien Station (Flasche für Flasche).
   Sicherheit: TwinSAFE schaltet bei Not-Halt oder offener Klappe hart ab (STO).
   Dieses Programm wertet nur das Statusbit aus und startet nichts von selbst neu.
   ============================================================================ *)
PROGRAM MAIN
VAR
    Mover       : ARRAY[1..GVL_Anlage.N_MOVER] OF FB_Mover;
    AchseMover  : ARRAY[1..GVL_Anlage.N_MOVER] OF AXIS_REF;
    AchseZ, AchseRotor, AchseZustell : AXIS_REF;
    Station     : FB_Oeffnungsstation;
    fbPowerZ, fbPowerR, fbPowerS : MC_Power;
    i           : INT;
    nImKopf     : INT;               (* Mover in der Öffnungsstation, 0 = frei *)
    nMessen     : INT;
    fHoehe      : LREAL;
    tMessen     : TON;
    rtOeffnen   : R_TRIG;
    nAnforderungen : INT;            (* gedrückte "Öffnen", noch nicht ausgegeben *)
    bBetrieb    : BOOL;
END_VAR

(* ---------------------------------------------------------------- Freigaben *)
bBetrieb := GVL_Anlage.bSicherOk AND GVL_Anlage.bNetzteileOk AND GVL_Anlage.bStoppOk;
fbPowerZ(Axis := AchseZ, Enable := bBetrieb, Enable_Positive := TRUE, Enable_Negative := TRUE);
fbPowerR(Axis := AchseRotor, Enable := bBetrieb, Enable_Positive := TRUE, Enable_Negative := TRUE);
fbPowerS(Axis := AchseZustell, Enable := bBetrieb, Enable_Positive := TRUE, Enable_Negative := TRUE);
GVL_Anlage.bLedQuittieren := NOT GVL_Anlage.bSicherOk;

rtOeffnen(CLK := GVL_Anlage.bOeffnen OR GVL_Anlage.bAnforderung);
GVL_Anlage.bAnforderung := FALSE;
IF rtOeffnen.Q THEN
    IF NOT GVL_Anlage.bTurmDa THEN GVL_Anlage.sMeldung := 'Sammelturm fehlt';
    ELSIF GVL_Anlage.bTurmVoll THEN GVL_Anlage.sMeldung := 'Sammelturm voll – bitte leeren';
    ELSE nAnforderungen := nAnforderungen + 1;
    END_IF
END_IF

(* ---------------------------------------------------------------- Mover aufrufen *)
FOR i := 1 TO GVL_Anlage.N_MOVER DO
    Mover[i](bFreigabe := bBetrieb, Achse := AchseMover[i]);
END_FOR

(* ---------------------------------------------------------------- Messen (hinten rechts) *)
(* Ein voller Mover fährt unter Laser und Kamera, hält 0,3 s, Höhe = Laser - Abstand *)
IF nMessen = 0 THEN
    FOR i := 1 TO GVL_Anlage.N_MOVER DO
        IF Mover[i].eBelegung = E_Belegung.VOLL AND ABS(Mover[i].fIst - GVL_Anlage.U_MESSEN) < 0.5 THEN
            nMessen := i; tMessen(IN := FALSE);
        END_IF
    END_FOR
ELSE
    GVL_Anlage.bKameraTrigger := TRUE;
    tMessen(IN := TRUE, PT := T#300MS);
    IF tMessen.Q THEN
        GVL_Anlage.bKameraTrigger := FALSE;
        (* 4 … 20 mA = 50 … 500 mm Abstand: Rohwert 0 … 32767 *)
        fHoehe := GVL_Anlage.LASER_HOEHE - (50.0 + 450.0 * INT_TO_LREAL(GVL_Anlage.nLaserRoh) / 32767.0);
        Mover[nMessen].fKronkorkenOk := fHoehe;
        IF GVL_Anlage.bKamKronkorken THEN Mover[nMessen].eBelegung := E_Belegung.GEMESSEN;
        ELSE Mover[nMessen].eBelegung := E_Belegung.OHNE_KRONKORKEN;
        END_IF
        nMessen := 0;
    END_IF
END_IF

(* ---------------------------------------------------------------- Öffnungsstation *)
IF nImKopf = 0 AND nAnforderungen > 0 THEN
    FOR i := 1 TO GVL_Anlage.N_MOVER DO
        IF (Mover[i].eBelegung = E_Belegung.GEMESSEN OR Mover[i].eBelegung = E_Belegung.OHNE_KRONKORKEN)
           AND ABS(Mover[i].fIst - GVL_Anlage.U_MESSEN) < 0.5 AND nImKopf = 0 THEN
            nImKopf := i;
        END_IF
    END_FOR
END_IF
IF nImKopf > 0 THEN
    Station(bStart := Mover[nImKopf].fIst < GVL_Anlage.U_OEFFNEN - 0.1 OR Station.nSchritt = 0,
            nMover := nImKopf, fZc := Mover[nImKopf].fKronkorkenOk,
            bMitKronkorken := Mover[nImKopf].eBelegung = E_Belegung.GEMESSEN,
            AchseZ := AchseZ, AchseRotor := AchseRotor, AchseZustell := AchseZustell);
    IF Station.bMoverEinfahren THEN
        Mover[nImKopf](fZiel := GVL_Anlage.U_OEFFNEN, fGeschw := GVL_Anlage.V_EINFAHRT, bStart := TRUE, Achse := AchseMover[nImKopf]);
    END_IF
    IF Station.bMoverAusfahren THEN
        Mover[nImKopf].eBelegung := E_Belegung.OFFEN;
        Mover[nImKopf](fZiel := GVL_Anlage.U_AUSGABE + GVL_Anlage.L_BAHN, bStart := TRUE, Achse := AchseMover[nImKopf]);
    END_IF
    IF Station.bFertig THEN
        nAnforderungen := nAnforderungen - 1; nImKopf := 0;
    END_IF
    IF Station.bStoerung THEN
        GVL_Anlage.sStoerung := CONCAT('Öffnungsstation Schritt ', INT_TO_STRING(Station.nSchritt));
    END_IF
END_IF

(* ---------------------------------------------------------------- Ausgabe und Laden *)
FOR i := 1 TO GVL_Anlage.N_MOVER DO
    IF ABS(Mover[i].fIst - GVL_Anlage.U_AUSGABE) < 0.5 AND Mover[i].eBelegung <> E_Belegung.LEER THEN
        GVL_Anlage.bLichtAusgabe := TRUE;
        IF NOT GVL_Anlage.bFlascheAusgabe AND GVL_Anlage.bSchutzZu THEN   (* entnommen und Klappe zu *)
            Mover[i].eBelegung := E_Belegung.LEER; GVL_Anlage.bLichtAusgabe := FALSE;
            Mover[i](fZiel := GVL_Anlage.U_LADEN, bStart := TRUE, Achse := AchseMover[i]);
        END_IF
    END_IF
    IF ABS(Mover[i].fIst - GVL_Anlage.U_LADEN) < 0.5 AND Mover[i].eBelegung = E_Belegung.LEER THEN
        GVL_Anlage.bLichtLaden := TRUE;
        IF GVL_Anlage.bFlascheLaden AND GVL_Anlage.bSchutzZu THEN         (* eingesetzt und Klappe zu *)
            Mover[i].eBelegung := E_Belegung.VOLL; GVL_Anlage.bLichtLaden := FALSE;
            Mover[i](fZiel := GVL_Anlage.U_MESSEN, bStart := TRUE, Achse := AchseMover[i]);
        END_IF
    END_IF
END_FOR
(* Abstandsregel (mind. 180 mm) übernimmt die Kollisionsvermeidung der Magnetbahn-Software. *)

(* ---------------------------------------------------------------- Anzeige *)
GVL_Anlage.bSaeuleRot := NOT GVL_Anlage.bSicherOk OR LEN(GVL_Anlage.sStoerung) > 0;
GVL_Anlage.bSaeuleGelb := LEN(GVL_Anlage.sMeldung) > 0;
GVL_Anlage.bSaeuleGruen := bBetrieb AND NOT GVL_Anlage.bSaeuleRot;
GVL_Anlage.bLedOeffnen := bBetrieb AND GVL_Anlage.bTurmDa AND NOT GVL_Anlage.bTurmVoll;
