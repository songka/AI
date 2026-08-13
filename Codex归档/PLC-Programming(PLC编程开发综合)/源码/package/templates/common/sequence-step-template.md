# AS228T sequence step template

## Purpose

Use for simple ordered process steps when a full state-machine explanation is not necessary.

## Fixed step convention

- `iStep = -1`: not in automatic mode; automatic actions are disabled.
- Entering automatic mode initializes `iStep := 0`.
- Steps `0..99`: reset, initialization, homing checks, and preparation only.
- Normal production starts at `100`.
- Increment ordinary steps by `10` (`100, 110, 120...`) so later steps can be inserted.
- Prefer assignments and explicit state transitions. Avoid `SET/RST` except for a reviewed event latch that genuinely must survive its source condition.

## ST skeleton

```st
IF NOT bAutoMode THEN
    iStep := -1;
ELSIF iStep = -1 THEN
    iStep := 0;
END_IF;

CASE iStep OF
    0:  (* Automatic reset/preparation range: 0..99 *)
        IF bResetReady THEN iStep := 100; END_IF;
    100:
        (* The next step starts a real action, so pause must block entry. *)
        IF bSequenceRunning AND bStep100Done THEN iStep := 110; END_IF;
    110:
        IF bActionFeedback THEN iStep := 120; END_IF;
    120:
        (* Online handshake reception is observed even while locally paused. *)
        IF bPeerSignalLatched THEN iStep := 130; END_IF;
    ELSE
        iStep := 0;
END_CASE;

(* Put action requests after transition logic and derive them from conditions + step. *)
bValveExtendRequest := bAutoMode AND (iStep = 110) AND bValvePermissive;
bAxisMoveRequest := bAutoMode AND bSequenceRunning AND (iStep = 130) AND bAxisPermissive;
```

## Notes

- Give `iStep` one owner and keep timeout/fault transitions visible.
- If the next step emits a physical action or one-shot pulse, require `bSequenceRunning` in the preceding transition.
- If waiting for a peer/upper/lower-station signal, do not gate signal capture with local running. Use a held level, request/acknowledge, sequence echo, or a latched receive event so a peer that did not pause cannot be missed.
- Put outputs at the end. Generate them from current step, mode, permissives, and interlocks rather than setting/resetting them throughout the flow.
