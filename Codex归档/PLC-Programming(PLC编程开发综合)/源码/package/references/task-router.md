# AS228T task router

Read the narrowest useful set.

## Generate logic

Read:

- `as228t-platform.md`
- `programming-guidelines.md`
- `ispsoft-workflow.md`
- the nearest file in `../templates/common/`

Add `safety-boundaries.md` when outputs, motion, wiring, interlocks, or commissioning are involved.

## Explain existing logic

Establish the task/POU scan order, variable declarations, device map, and all writers. Explain visible behavior first, then assumptions and likely weak points.

## Review or refactor

Check output ownership, reset/re-latch paths, state transitions, task interactions, retained state, startup behavior, and project/HWCONFIG consistency. Propose a structure before rewriting.

## Debug

Read `diagnostics.md`. Collect symptom, reproduction condition, current state/step, relevant inputs/outputs, timer/counter states, task context, online values, error log, and whether another POU writes the same device.

## Communications

Read `communications.md` and, for interface maps, `io-addressing-standard.md`. Confirm physical port, protocol role, node/IP settings, register/tag map, byte/word order, timeout/retry behavior, write permissions, and network exposure. Do not invent SM/SR meanings.

## I/O table, robot, alarm, or HMI map

Read `io-addressing-standard.md` and use `templates/common/io-table-standard-template.md`. Enforce one producer per address, separate commands from status, prohibit HMI direct writes to Y, and include stale-data and failure behavior.

## Positioning or motion

Read `positioning.md` and `safety-boundaries.md`. Require the axis type, pulse/communication method, drive model, homing method, limits, units/scaling, stop categories, and verified hardware safety chain. Start with disabled/unloaded offline validation.

## Hardware, devices, or retention

Read `hardware-io.md` for electrical/port/I/O questions and `devices-retention.md` for M/S/T/C/HC/D/W/SM/SR questions. Prefer the actual HWCONFIG project over generic allocation assumptions.

## Incomplete input

Continue with a clearly labeled template when omissions are non-critical. Stop at a risk review when wiring polarity, actuator response, output circuitry, or safety-chain behavior is unknown.
