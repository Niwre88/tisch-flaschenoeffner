# SPS-Programm TFO-A Index D (TwinCAT 3, Structured Text)

**Status: Gerüst, ungetestet, nicht übersetzt.** Es zeigt Aufbau und Abläufe. Vor dem
Einsatz muss es in einem TwinCAT-Projekt angelegt, übersetzt und an der Anlage getestet werden.

| Datei | Inhalt |
|---|---|
| [`GVL_Anlage.st`](GVL_Anlage.st) | Konstanten (Stationen, Höhen, Zeiten) und alle Ein-/Ausgänge (`AT %I*` / `%Q*`, Verknüpfung im I/O-Baum) |
| [`FB_Mover.st`](FB_Mover.st) | ein Mover der Magnetbahn: Belegung (leer, voll, gemessen, offen), Fahrt mit `MC_MoveAbsolute` |
| [`FB_Oeffnungsstation.st`](FB_Oeffnungsstation.st) | Schrittkette S1 … S9: Einstellen, Entbördeln (Kurvenscheibe Zustellring = f(Rotor)), Entlüften, Abheben, Abfuhr |
| [`MAIN.st`](MAIN.st) | Freigaben, Messen (Laser, Kamera), Disposition der Mover, Ausgabe, Laden, Signalsäule |

## Einrichten

1. TwinCAT 3 XAE, neues Projekt, Zielsystem Embedded-PC. EtherCAT-Strang scannen.
2. Bibliotheken: `Tc2_MC2`, `Tc2_MC2_Camming`, für Alexa `Tc3_IotBase` (MQTT).
3. Die vier Dateien als GVL, DUT und POUs anlegen (Inhalt kopieren), Achsen in der NC
   anlegen: 6 Mover, Z, Rotor, Zustellring. Kurvenscheibe 1 (Zustellung über den
   Rotorwinkel) im Kurvenscheiben-Editor erstellen.
4. Sicherheitsfunktionen SF1 bis SF5 als TwinSAFE-Projekt (siehe PDF Kap. 4). Das
   Statusbit der EL6910 auf `GVL_Anlage.bSicherOk` legen.
5. Stationspositionen an der Anlage einteachen und in `GVL_Anlage` eintragen.

Zugangsdaten (WLAN, MQTT) gehören nicht in diese Dateien, sondern in die
TwinCAT-Zielkonfiguration bzw. eine lokale, nicht versionierte Datei.
