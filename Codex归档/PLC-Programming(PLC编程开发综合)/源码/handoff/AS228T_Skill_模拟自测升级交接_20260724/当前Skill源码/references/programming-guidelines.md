# AS228T programming and review guidelines

## Structure

- Separate input mapping, equipment modules, sequence/state logic, alarms, communications, and output mapping.
- Give each physical output one logical owner. Combine requests and permissives before the final output assignment.
- Use symbolic names for control logic; keep physical addresses in mapping/configuration areas.
- Make startup, stop, fault, reset, pause, resume, abort, and power-cycle behavior explicit.
- Keep HMI commands separate from status and feedback.
- For a whole machine, follow `Prog0_Main`, `Prog1_AutoSequence`, `Prog2_Alarm`, `Prog3_ModuleAndOutput`, and `Prog4_HMIManual`; execute final output mapping after all automatic and manual request producers.
- Use one dedicated valve FB per valve. Sequence/manual logic writes requests only; the valve FB owns direction exclusion, pause holding, and optional bounded retry.

## Step and output convention

- Use `iStep = -1` outside automatic mode; set it to `0` on entry to automatic mode.
- Reserve steps `0..99` for reset, initialization, homing checks, and preparation. Start production at `100` and normally increment by `10`.
- Prefer assignments and explicit state transitions; minimize `SET/RST` use.
- Put action-request calculations at the end and derive them from step, mode, permissives, and interlocks.
- If the next step starts an actuator or pulse, gate the preceding transition with local sequence-running state.
- Capture/hold upper/lower-station interaction signals without local running gating so a peer that did not pause cannot be missed.

## Pause convention

- Preserve the current logical step during controlled pause.
- Drop axis/motion output requests during pause.
- Retain the required valve logical state during pause, subject to final permissives and the verified mechanical safe-state requirement.
- Revalidate position, valve feedback, interlocks, and handshake state before resuming physical actions.
- Do not write ordinary valve alarms inside action logic. Only a configured bounded retry may produce `RetryExhausted`; central alarm logic owns Active/Latched alarms.

## ISPSoft and syntax

- Produce ISPSoft 3.19+ ST only. Do not ask the user to choose LD/CFC/SFC or another implementation language.
- Declare variables and FB interfaces explicitly when enough project context is available.
- Mark code as a skeleton if exact ISPSoft syntax, library FB version, device attribute, or project declaration is unverified.
- Compile in the user's ISPSoft version before treating generated code as usable.

## Function-block interface order

- Include `bAutoMode` and `bSequenceRunning` first in every FB input interface.
- Order inputs: program state → servo state → sensor state → settings.
- Order outputs: flow number → status → alarm → servo drive → cylinder action → online interaction.
- Declare local variables last.
- Keep the same order in `局部变量.csv` and ST declarations.

## Scan and ownership review

For unexpected behavior, inspect in this order:

1. task/POU execution order
2. input refresh and mapping
3. enable/permissive conditions
4. state/step transition
5. timer/counter call and reset path
6. every writer of the affected M/D/X/Y or symbolic variable
7. final output mapping
8. field wiring and feedback

## Alarm and reset

- Separate trigger, latch, hold, reset request, and reset permissive.
- Expect immediate re-latch when the trigger remains true.
- Do not allow a reset command to override an active hazardous condition.
- Distinguish process interlocks from personnel-safety functions.

## Change control

- Preserve an exported project backup and record ISPSoft/firmware versions.
- Compare offline and PLC projects before download.
- Review HWCONFIG and retained values separately from program logic.
- Test changed modules offline, then commission one controlled function at a time.
- Define rollback conditions before an online change.
