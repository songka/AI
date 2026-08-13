# Template map

Use this file to choose the nearest reusable template before writing a large custom answer.

## Common template selection

- Project confirmation files and generation gates
  - `templates/common/project-confirmation-template.md`
  - workflow: `references/project-confirmation-workflow.md`

- Function-block interface and variable declaration order
  - `templates/common/function-block-interface-template.md`

- Whole-machine program organization and scan/data flow
  - `templates/common/program-framework-template.md`

- Standard equipment module (Auto/Manual/Fault handling)
  - `templates/common/equipment-module-template.md`

- Pneumatic valve drive, pause holding, and bounded retry
  - `templates/common/valve-drive-template.md`

- Start / stop motor or actuator control
  - `templates/common/start-stop-interlock-template.md`

- Sequence flow with explicit steps
  - `templates/common/sequence-step-template.md`

- Advanced sequence flow (Pause / Resume / Abort handling)
  - `templates/common/pause-resume-sequence-template.md`

- State-based machine control
  - `templates/common/state-machine-template.md`

- Alarm latch, hold, and reset behavior
  - `templates/common/alarm-latch-reset-template.md`

- Alarm/interlock module design
  - `templates/common/alarm-interlock-module-template.md`

- Timer / counter diagnosis
  - `templates/common/timer-counter-diagnostic-template.md`

- Output ownership review
  - `templates/common/output-ownership-review-template.md`

- I/O table, address map, robot/CANopen/EIP/alarm/HMI interface
  - `templates/common/io-table-standard-template.md`

- Upper/lower-station docking and transfer handshake
  - `templates/common/station-handshake-template.md`

## Selection rules

- Before selecting a code template for new generation, complete the staged project confirmation workflow. Do not generate final ST or import-ready CSV files before G7 authorization.
- Apply the function-block interface template to every generated FB without asking the user to reconfirm its fixed order.
- Prefer state-machine and step templates for expandable sequential processes.
- Prefer alarm/reset templates when fault memory and recovery are the focus.
- Prefer output-ownership review before rewriting a large code block.
- Use the program-framework template before generating a whole machine or multi-station project.
- Use the dedicated valve template for every valve; sequence actions issue requests and do not embed ordinary valve alarms.
- Use the station-handshake template whenever upstream/downstream machines exchange allow, request, complete, release, or pick signals.
- Apply the fixed step convention: `-1` non-auto, `0..99` reset/preparation, production from `100`, ordinary increments of `10`, and outputs calculated last.
- Treat every template as an ISPSoft draft: compile it, bind it to the actual AS228T declarations, and apply `references/safety-boundaries.md` before field use.
