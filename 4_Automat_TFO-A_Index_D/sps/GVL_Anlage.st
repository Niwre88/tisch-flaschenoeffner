(* ============================================================================
   Flaschenöffner-Automat TFO-A, Index D – globale Daten und Konstanten
   TwinCAT 3, Structured Text. Maße in mm, Zeiten als TIME.
   STATUS: Gerüst, ungetestet, nicht übersetzt.
   ============================================================================ *)
{attribute 'qualified_only'}
VAR_GLOBAL CONSTANT
    N_MOVER            : INT  := 6;
    L_BAHN             : LREAL := 1428.32;     (* Bahnlänge Mitte Motormodule *)
    (* Stationen als Bahnweg (gegen den Uhrzeigersinn, 0 = vorn links Anfang Gerade) *)
    U_AUSGABE          : LREAL := 80.0;
    U_LADEN            : LREAL := 320.0;
    U_MESSEN           : LREAL := 734.16;
    U_OEFFNEN          : LREAL := 914.16;
    ABSTAND_MIN        : LREAL := 180.0;       (* Mover-Abstand, Klemme bis Ø 100 *)
    V_EILGANG          : LREAL := 600.0;       (* mm/s *)
    V_EINFAHRT         : LREAL := 50.0;        (* letzte 60 mm in den Kopf *)
    (* Kopf *)
    Z0_STAND           : LREAL := 116.0;       (* Standfläche der Flaschen über Tisch *)
    ZC_MIN             : LREAL := 289.0;       (* Kronkorken-Oberkante kleinste Flasche *)
    ZC_MAX             : LREAL := 467.5;
    ABHEBEN            : LREAL := 8.0;
    LASER_HOEHE        : LREAL := 525.0;       (* Unterkante Laser über Tisch *)
    ROTOR_UMDREHUNGEN  : LREAL := 2.0;
    ROTOR_DREHZAHL     : LREAL := 720.0;       (* Grad/s *)
    SCHLITZ_EINFAHRT   : LREAL := 0.0;
    SCHLITZ_AUSFAHRT   : LREAL := 180.0;
    T_ENTLUEFTEN       : TIME := T#300MS;
    T_ABFUHR_MAX       : TIME := T#4S;
END_VAR

VAR_GLOBAL
    (* Eingänge (EtherCAT, siehe I/O-Liste im PDF) *)
    bOeffnen        AT %I* : BOOL;   (* E1 -S1 *)
    bStoppOk        AT %I* : BOOL;   (* E2 -S3, Öffner: TRUE = nicht gedrückt *)
    bSchutzZu       AT %I* : BOOL;   (* E3 Meldeausgang Klappen/Deckel *)
    bKamKronkorken  AT %I* : BOOL;   (* E4 -B4 *)
    bKamAnderer     AT %I* : BOOL;   (* E5 -B4 Bügel/Schraubverschluss *)
    bFlascheAusgabe AT %I* : BOOL;   (* E6 -B6 *)
    bFlascheLaden   AT %I* : BOOL;   (* E7 -B7 *)
    bKorkAmBand     AT %I* : BOOL;   (* E8 -B8 *)
    bKorkZaehlung   AT %I* : BOOL;   (* E9 -B11 *)
    bTurmVoll       AT %I* : BOOL;   (* E10 -B12 *)
    bTurmDa         AT %I* : BOOL;   (* E11 -B13 *)
    bNetzteileOk    AT %I* : BOOL;   (* E12 *)
    nLaserRoh       AT %I* : INT;    (* AI1 -B3, 4 … 20 mA *)
    bSicherOk       AT %I* : BOOL;   (* TwinSAFE: alle SF in Ordnung (Statusbit EL6910) *)
    (* Ausgänge *)
    bLichtAusgabe   AT %Q* : BOOL;
    bLichtLaden     AT %Q* : BOOL;
    bSaeuleGruen    AT %Q* : BOOL;
    bSaeuleGelb     AT %Q* : BOOL;
    bSaeuleRot      AT %Q* : BOOL;
    bLedOeffnen     AT %Q* : BOOL;
    bKameraTrigger  AT %Q* : BOOL;
    bLedQuittieren  AT %Q* : BOOL;
    nUeberband      AT %Q* : INT;    (* EL7332 Kanal 1, Sollwert *)
    nSteigband      AT %Q* : INT;    (* EL7332 Kanal 2 *)

    (* Zähler und Meldungen für Panel und MQTT *)
    nGeoeffnet      : UDINT;
    nKronkorken     : UDINT;
    sMeldung        : STRING(120);
    sStoerung       : STRING(120);
    bAnforderung    : BOOL;          (* aus Panel oder MQTT (Alexa) *)
END_VAR
