# AS228T equipment module template

Use for a motor, heater, conveyor, or similar equipment module in ISPSoft. Keep physical I/O outside the block. Route valves through `valve-drive-template.md`; do not mix valve drive, retry, and alarm-latch logic into an action step.

> `ProcessEnableOK` is only a standard-PLC process permissive/status input. It does not replace an independent emergency-stop, guard, STO, or other safety circuit.

## Pseudo-ST interface

```st
FUNCTION_BLOCK FB_Equipment
VAR_INPUT
    CmdAutoStart    : BOOL;
    CmdStop         : BOOL;
    CmdManualJog    : BOOL;
    ModeAuto        : BOOL;
    ProcessEnableOK : BOOL;
    ProtectionOK    : BOOL;
    RunFeedback     : BOOL;
    ResetCmd        : BOOL;
END_VAR
VAR_OUTPUT
    RunRequest      : BOOL;
    Ready           : BOOL;
    FaultActive     : BOOL;
END_VAR
VAR
    RunState        : BOOL;
END_VAR

(* Set-dominant process fault. *)
IF NOT ProtectionOK THEN
    FaultActive := TRUE;
ELSIF ResetCmd AND ProtectionOK THEN
    FaultActive := FALSE;
END_IF;

Ready := ProcessEnableOK AND ProtectionOK AND NOT FaultActive;

IF NOT Ready OR CmdStop THEN
    RunState := FALSE;
ELSIF ModeAuto AND CmdAutoStart THEN
    RunState := TRUE;
ELSIF NOT ModeAuto THEN
    (* Manual jog must be hold-to-run and use the same permissives. *)
    RunState := CmdManualJog;
END_IF;

(* Logical request only. Apply final output gating in one output-mapping POU. *)
RunRequest := RunState AND Ready;
```

## Review checklist

- Confirm the exact ISPSoft declarations and feedback-timeout implementation.
- Require stop/fault/permissive loss to dominate start and manual commands.
- Keep manual jog hold-to-run and prevent simultaneous conflicting commands.
- Add a run-feedback timeout when the equipment requires it.
- Map the physical output once, after independent hardware/safety-chain status is confirmed.
- Test startup, mode transfer, fault, reset, feedback loss, and power cycle.
- For a valve, let the dedicated valve FB own extend/retract mutual exclusion and pause holding. The action step only issues a request.
- Do not write a valve alarm inside the normal action. A central alarm module evaluates feedback timeout. Only a configured multi-retry sequence may raise `RetryExhausted` after the last failed attempt.
