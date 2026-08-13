# AS228T pause/resume sequence template

Preserve the logical step during a controlled pause. Axis/motion requests drop during pause; valve state requests remain at their step-defined state unless the project-specific safe-state analysis requires another state.

```st
(* Capture peer interaction even when this machine is paused. Reset only after
   the handshake is consumed/acknowledged. *)
bPeerSignalLatched := bPeerSignalLatched OR bPeerSignal;

IF NOT bAutoMode THEN
    iStep := -1;
    bSequenceRunning := FALSE;
    bSequencePaused := FALSE;
ELSIF iStep = -1 THEN
    iStep := 0;
ELSIF bAbortCmd OR bFaultActive THEN
    iStep := 0;
    bSequenceRunning := FALSE;
    bSequencePaused := FALSE;
ELSIF bPauseCmd AND bSequenceRunning THEN
    bSequenceRunning := FALSE;
    bSequencePaused := TRUE;
ELSIF bStartResumeCmd AND bProcessEnableOK THEN
    bSequenceRunning := TRUE;
    bSequencePaused := FALSE;
END_IF;

IF bSequenceRunning THEN
    CASE iStep OF
        0:  (* Reset/preparation range: 0..99. *)
            IF bResetReady THEN iStep := 100; END_IF;
        100:
            IF bValveExtended THEN iStep := 110; END_IF;
        110:
            IF bProcessDone THEN iStep := 120; END_IF;
        120:
            IF bAxisInPosition THEN
                iStep := 0;
                bSequenceRunning := FALSE;
            END_IF;
        ELSE
            iStep := 0;
            bSequenceRunning := FALSE;
    END_CASE;
END_IF;

(* Valve requests are step-owned and remain during pause. *)
bValveExtendRequest := (iStep = 100 OR iStep = 110 OR iStep = 120)
                    AND (bSequenceRunning OR bSequencePaused);

(* Motion does not remain energized/requested during pause. *)
bMotorRunRequest := (iStep = 110) AND bSequenceRunning;
bAxisMoveRequest := (iStep = 120) AND bSequenceRunning;

bAxisMoveCmd := bAxisMoveRequest
             AND bSequenceRunning
             AND bProcessEnableOK
             AND NOT bFaultActive;

bMotorRunCmd := bMotorRunRequest AND bSequenceRunning AND bProcessEnableOK AND NOT bFaultActive;
bValveExtendCmd := bValveExtendRequest AND bProcessEnableOK AND NOT bFaultActive;
```

Transition rule:

- When the next step starts an axis, valve action, or pulse, the preceding transition must include `bSequenceRunning`.
- When the next condition is an online interaction signal, continue to capture/latch it without `bSequenceRunning`; the peer may not pause. Do not rely on a one-scan pulse.
- On resume, revalidate axis position, valve feedback, interlocks, and peer handshake state before reissuing motion.

Valve holding means retaining the logical valve command required by the mechanism; it does not bypass final output permissives or the independent safety chain. Define the safe paused state from the real mechanics, stored energy, load, and safety architecture.
