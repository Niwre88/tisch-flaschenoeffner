(* ============================================================================
   FB_Mover – ein Mover der Magnetbahn mit Flaschendaten
   Die Magnetbahn liefert jeden Mover als NC-Achse (absolute Position = Bahnweg).
   Bewegungen über Tc2_MC2 (MC_Power, MC_MoveAbsolute).
   ============================================================================ *)
TYPE E_Belegung :
(
    LEER := 0,           (* keine Flasche *)
    VOLL,                (* geladen, noch nicht gemessen *)
    GEMESSEN,            (* Höhe und Verschluss bekannt *)
    OFFEN,               (* geöffnet, wartet auf Ausgabe *)
    OHNE_KRONKORKEN      (* wird ohne Öffnen ausgegeben *)
);
END_TYPE

FUNCTION_BLOCK FB_Mover
VAR_INPUT
    bFreigabe   : BOOL;
    fZiel       : LREAL;         (* Bahnweg, auf den der Mover fahren soll *)
    fGeschw     : LREAL := GVL_Anlage.V_EILGANG;
    bStart      : BOOL;          (* Flanke startet die Fahrt *)
END_VAR
VAR_OUTPUT
    bInPos      : BOOL;
    bFehler     : BOOL;
    fIst        : LREAL;
END_VAR
VAR_IN_OUT
    Achse       : AXIS_REF;
END_VAR
VAR
    eBelegung   : E_Belegung := E_Belegung.LEER;
    fKronkorkenOk : LREAL;       (* gemessene Kronkorken-Oberkante (ZC) *)
    fbPower     : MC_Power;
    fbFahrt     : MC_MoveAbsolute;
END_VAR

fbPower(Axis := Achse, Enable := bFreigabe, Enable_Positive := TRUE, Enable_Negative := FALSE);
(* nur gegen den Uhrzeigersinn: Ziel immer vor der aktuellen Position (modulo Bahnlänge) *)
fbFahrt(Axis := Achse, Execute := bStart AND fbPower.Status,
        Position := fZiel, Velocity := fGeschw, Acceleration := 4000, Deceleration := 4000,
        Jerk := 40000, BufferMode := MC_Aborting);
fIst := Achse.NcToPlc.ModuloActPos;
bInPos := fbFahrt.Done;
bFehler := fbFahrt.Error OR fbPower.Error;
