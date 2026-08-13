# AS228T valve drive template

Use one dedicated valve FB per valve. Sequence and manual logic issue requests; the valve FB owns extend/retract mutual exclusion, pause holding, feedback qualification, and optional retry control. The output-mapping POU remains the only physical Y writer.

## Interface

- Inputs: extend/retract requests, manual/auto mode, pause, permissive, extended/retracted feedback, retry enable/count, reset.
- Outputs: extend/retract logical output requests, busy, extended, retracted, retry active, retry exhausted, diagnostic code.

## Rules

- Reject simultaneous extend and retract requests; never energize both directions.
- During pause, retain the last valid step-defined valve state. Still apply permissive, fault, and final-output gating.
- Do not latch or write a valve alarm in the normal action or valve FB.
- Let the central alarm module evaluate ordinary motion/feedback timeout.
- If the process explicitly requires repeated attempts, perform a bounded retry sequence. Raise only `RetryExhausted` after the configured final attempt; the central alarm module converts that event into Active/Latched alarm states.
- Clear the retry counter only on a new command cycle or reviewed reset, not every scan.
- Record timeout per attempt, retry count, rest interval, opposite-direction behavior, and final safe state.

## Output pattern

```st
(* Requests are calculated last from state + conditions. *)
bExtendOutReq := bExtendState
              AND bProcessEnableOK
              AND NOT bRetractState;
bRetractOutReq := bRetractState
               AND bProcessEnableOK
               AND NOT bExtendState;
```

Do not assign physical `Y` inside this FB.
