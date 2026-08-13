# AS228T state-machine template

Use for step-based control in ISPSoft. Separate state-owned requests from the single final output assignment.

```st
(* Safe default every scan prevents retained output commands between states. *)
bMotorRunRequest := FALSE;

IF bFaultActive OR NOT bProcessEnableOK THEN
    iState := 900;
END_IF;

CASE iState OF
    0: (* Idle *)
        IF bAutoMode AND bStartCmd AND NOT bFaultActive AND bProcessEnableOK THEN
            iState := 10;
        END_IF;

    10: (* Pre-start checks *)
        IF bStopCmd THEN
            iState := 0;
        ELSIF bInterlockOK THEN
            iState := 20;
        END_IF;

    20: (* Run *)
        bMotorRunRequest := TRUE;
        IF bStopCmd THEN
            iState := 0;
        END_IF;

    900: (* Fault *)
        IF bFaultResetCmd AND NOT bFaultActive AND bProcessEnableOK THEN
            iState := 0;
        END_IF;

ELSE
    iState := 900;
END_CASE;

(* Final logical gate; map the physical Y output in one output POU only. *)
bMotorRunCmd := bMotorRunRequest
             AND bProcessEnableOK
             AND bInterlockOK
             AND NOT bFaultActive
             AND NOT bStopCmd;
```

`bProcessEnableOK` and `bInterlockOK` do not replace independent personnel-safety hardware. Confirm ISPSoft syntax and the state type in the real project.

