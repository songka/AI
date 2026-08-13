# AS228T start/stop interlock template

Use for a standard logical motor or actuator request with explicit stop priority.

```st
IF bStopCmd OR bFaultActive OR NOT bInterlockOK OR NOT bProcessEnableOK THEN
    bRunCmd := FALSE;
ELSIF bStartCmd AND bModeAuto THEN
    bRunCmd := TRUE;
END_IF;
```

Give `bRunCmd` one owner, make seal-in/reset behavior explicit, and treat `bProcessEnableOK` as a standard-PLC permissive rather than a complete safety function.

