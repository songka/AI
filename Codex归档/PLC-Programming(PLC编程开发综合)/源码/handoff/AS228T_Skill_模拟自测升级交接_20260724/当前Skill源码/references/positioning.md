# AS228T positioning and high-speed I/O

## Capability boundary

Delta's AS Series product page advertises family-level capability of up to 6 pulse-control axes at 200 kHz and up to 8 CANopen motion axes. Do not convert that marketing summary into an AS228T channel assignment. Confirm the exact AS228T-A high-speed output table, allowed Y points, pulse format, simultaneous-axis limits, firmware, and wiring chapter.

## Instruction lookup

Before generating a positioning call, open the exact PM-2024 instruction entry and confirm:

- AS100/200 support marker and firmware requirement
- pulse versus continuous execution behavior
- operand data types and 16/32-bit range
- output channel and pulse format
- busy/done/error flags and duplicate-output errors
- acceleration/deceleration, direction, limits, homing, and abort semantics
- whether the instruction is supported by the simulator

Do not import DVP examples or flags merely because instruction names look similar.

## Engineering inputs

Collect drive model/mode, pulse interface type, pulses per revolution, electronic gear, mechanics per revolution, user units, travel sign, home sensor, positive/negative limits, speed/acceleration, stop behavior, and feedback method.

## Commissioning order

1. verify independent stop/STO/limit chain
2. inhibit or unload mechanics where practical
3. verify output electrical compatibility and common wiring
4. verify direction at very low speed
5. verify one commanded unit against measured travel
6. test limits, abort, fault, timeout, restart, and power cycle
7. increase speed/acceleration only after recorded checks pass

Simulation does not prove pulse timing, electrical compatibility, travel direction, stopping distance, or mechanical safety.

