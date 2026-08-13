# ISPSoft 3.19+ workflow for AS228T-A

## Project structure

Use AS228T-A, ISPSoft 3.19 or later, and ST without asking. Before writing code:

1. inspect HWCONFIG/module table and CPU parameters
2. inspect task type, trigger/period, and POU execution order
3. inspect global/local symbols and physical address bindings
4. inspect cross references and the Used Device Report
5. compile before connecting to a PLC

ISP-2020 ch.5 covers task/POU management and POU order; ch.6 covers symbol variables; ch.13 covers ST, including AS-series limitations; ch.17 covers online/debug functions.

## Task facts

AS Series documentation states a maximum of 283 tasks for the family: 32 cyclic, 32 I/O interrupt, 4 timer interrupt, 2 communication interrupt, 1 external 24 V low-voltage interrupt, and 212 user-defined tasks. Confirm AS228T firmware/project support and do not create tasks merely because capacity exists.

## HWCONFIG

Use HWCONFIG for:

- CPU/module configuration and version matching
- I/O and module-register allocation
- retained-area and CPU behavior settings
- COM/Ethernet/Socket parameters
- module parameters and diagnostics

Menu names can vary across 3.19+ revisions. Describe the setting goal and ask for a screenshot only when an exact click path matters; do not make the ISPSoft baseline a normal confirmation question.

## Review tools

- Program compare: ISPSoft can compare the open project with an `.isp` file or the connected PLC.
- Used Device Report: use `View > Used Device Report` to detect occupied registers/devices.
- Before download: compare, export/backup the project, record firmware/ISPSoft version, and back up required device values.

## Simulation boundary

Delta states that simulator behavior is not identical to the physical PLC. Timing depends on the PC, and multiple hardware/motion/communication instructions are unsupported. Use simulation for logic flow only; test real timing, I/O, communication, high-speed counting, positioning, and safety behavior on controlled hardware.
