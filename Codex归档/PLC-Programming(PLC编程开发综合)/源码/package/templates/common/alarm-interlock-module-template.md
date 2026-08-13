# AS228T alarm/interlock module template

Separate permissive evaluation, process interlocks, alarm trigger, fault latch, reset permissive, and final run-enable decision.

```st
bRunEnable := FALSE;

(* Set-dominant fault latch. *)
IF bFaultTrigger THEN
    bFaultActive := TRUE;
ELSIF bFaultResetCmd AND bResetPermissive THEN
    bFaultActive := FALSE;
END_IF;

bInterlockOK := bProcessGuardStatusOK AND bPressureOK AND NOT bStopCmd;
bPermissiveOK := bAutoMode AND bSystemReady;

IF bRunRequest AND bPermissiveOK AND bInterlockOK AND NOT bFaultActive THEN
    bRunEnable := TRUE;
END_IF;
```

`bProcessGuardStatusOK` is monitoring/permissive information only. It does not replace a verified safety relay/controller, guard circuit, or STO path.

