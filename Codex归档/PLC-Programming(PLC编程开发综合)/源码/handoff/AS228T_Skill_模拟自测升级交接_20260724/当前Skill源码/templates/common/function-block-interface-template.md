# AS228T-A function-block interface template

Apply this interface order to every generated FB unless a confirmed external library interface forces another order. Do not ask the user to reconfirm the default order.

## Required program-state inputs

Every FB includes these inputs first:

```st
VAR_INPUT
    bAutoMode        : BOOL;  (* 程序状态：自动状态 *)
    bSequenceRunning : BOOL;  (* 程序状态：状态运行中 *)
```

## Input order

Continue `VAR_INPUT` in this order:

1. program state: mode, running, pause, reset, permissions
2. servo/axis state: ready, servo on, homed, busy, in-position, alarm, actual position
3. sensor state: cylinder limits, presence, position, inspection and other field sensing
4. settings: enable, timeout, retry count, speed, position, recipe/process settings

Within a category, sort by confirmed process/device order, then axis/device number, then symbolic name. Keep related positive/negative or extend/retract signals adjacent.

## Output order

Declare `VAR_OUTPUT` in this exact category order:

1. flow number: `iStep`/`iFlowNo`
2. status: ready, running, busy, done, paused, reset complete
3. alarm: alarm active, alarm code, timeout/retry-exhausted diagnostics
4. servo drive: enable, reset, home, jog, move, stop and target requests
5. cylinder action: extend/retract or valve state requests
6. online interaction: upstream/downstream allow, request, complete, release and acknowledgement

The FB produces logical requests only. Physical Y, pulse output, CANopen controlword, and network transmit images remain owned by their confirmed mapping/interface module.

## Local variables last

After `VAR_INPUT` and `VAR_OUTPUT`, declare `VAR` locals last. Group locals as step helpers, edge memories, timers/counters, retry state, calculations, then reserved diagnostics. Avoid `VAR_IN_OUT` unless the interface was explicitly confirmed.

## Skeleton

```st
FUNCTION_BLOCK FB_Station
VAR_INPUT
    (* 1. Program state *)
    bAutoMode        : BOOL;
    bSequenceRunning : BOOL;

    (* 2. Servo state *)

    (* 3. Sensor state *)

    (* 4. Settings *)
END_VAR
VAR_OUTPUT
    (* 1. Flow number *)
    iStep : INT;

    (* 2. Status *)

    (* 3. Alarm *)

    (* 4. Servo drive requests *)

    (* 5. Cylinder action requests *)

    (* 6. Online interaction *)
END_VAR
VAR
    (* Local variables last *)
END_VAR
```

Reflect the same category order in `局部变量.csv` and in the ST declaration block.
