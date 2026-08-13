# AS228T diagnostics

## Front-panel indicators

HOM-2024 describes:

- RUN ON: running; OFF: stopped; blinking: error detection
- ERROR ON: serious error; OFF: normal; blinking: minor error
- BAT.LOW: battery status; display can be enabled/disabled in HWCONFIG
- COM1/COM2/CAN blinking: communication activity
- I/O LEDs: physical input/output signal indication

Use LEDs as triage evidence, not a root-cause conclusion.

## Verified SR error subset

PM-2024 sec.2.2.14/2.2.15 documents:

- `SR0`: PLC operation/operand error
- `SR1`: address of the operation error (32-bit)
- `SR4`: grammar-check error
- `SR5`: address of the grammar-check error (32-bit)
- `SR8`: step address where the watchdog timer became active
- `SR28–SR31`: high-speed-output duplicate/repeated-output diagnostics
- `SR40`: number of error logs
- `SR41`: error-log pointer
- `SR42` onward: error-log records

Confirm the exact table, data width, refresh condition, and current firmware before writing or clearing any SR/SM.

## Fault-isolation order

1. record RUN/ERROR/BAT.LOW and module LEDs
2. record ISPSoft CPU/module diagnostics and error log before reset
3. read relevant SR values without writing them
4. compare offline project with PLC
5. confirm HWCONFIG/module versions and missing/moved modules
6. inspect task/POU order, watchdog/cycle time, and duplicate writers
7. inspect power, wiring, communication, and field feedback
8. reset only after preserving evidence and removing the cause

Do not clear memory, initialize the CPU, update firmware, or download a project as the first diagnostic step.

