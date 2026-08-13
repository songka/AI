# AS228T project confirmation and source delivery workflow

Apply this workflow to every new program, whole-machine program, station module, or substantial rewrite. Do not generate complete ST source or import-ready variable CSV files before final generation authorization.

## Confirmation gates

Work one gate at a time. After the user explicitly confirms a gate, create or update its confirmed artifact before moving on.

| Gate | Confirm with user | Required confirmed artifact |
| --- | --- | --- |
| G0 | project name, scope, existing-project/new-project; prefill fixed platform defaults without asking | `00_确认索引.md` |
| G1 | functional requirements, modes, cycle, startup/stop/reset/pause/abort/power-cycle behavior | `01_需求确认.md` |
| G2 | physical DI/DO, devices, axes, robots, HMI, communication, addresses, direction, fail state | `02_IO与地址确认.csv` |
| G3 | POU/task structure, scan order, module ownership, final output owner | `03_程序结构确认.md` |
| G4 | station/process flow, step numbers, transitions, timeout, retry, pause/resume, abnormal branches | `04_流程确认.md` |
| G5 | alarms, interlocks, reset permissives, upper/lower-station handshakes, communication timeout/recovery | `05_报警联锁接口确认.md` |
| G6 | variable names/types, retain policy, CSV import format, file encoding, ST file split, test cases | `06_变量与交付确认.md` |
| G7 | all open items closed and explicit approval to generate the program | `07_程序生成授权.md` |

Do not skip a gate because the request sounds complete. Pre-fill known information, mark assumptions and open items, and ask only for the current gate's unresolved decisions.

G0 always records these fixed company defaults and does not ask the user to confirm them:

- PLC: `AS228T-A`
- ISPSoft: `3.19+`
- firmware: `不作为确认项`
- implementation language: `ST`

## Confirmation artifact rules

Each confirmed artifact must contain:

- project and document version
- status: `草案`, `待确认`, `已确认`, or `已作废`
- confirmed scope and exact decisions
- assumptions and project/site confirmations
- unresolved items; an artifact with unresolved blocking items cannot be `已确认`
- source files/drawings/manuals used
- confirmation date and the user's confirmation wording
- effect on downstream artifacts

Never write `已确认` based on silence or inference. When an upstream decision changes, mark affected downstream artifacts `已作废`, increment the revision, list the change, and reconfirm before source generation.

## Program-generation boundary

Before G7, output only confirmation artifacts, address proposals, structure diagrams, step tables, handshake tables, alarm tables, and test plans. Do not output complete executable ST, final FB bodies, or import-ready variable CSV files. A small illustrative fragment is allowed only when the user requests it for a design decision; label it `示意/非最终程序`.

After G7, generate exactly these source deliverables:

```text
确认文件/
  00_确认索引.md
  01_需求确认.md
  02_IO与地址确认.csv
  03_程序结构确认.md
  04_流程确认.md
  05_报警联锁接口确认.md
  06_变量与交付确认.md
  07_程序生成授权.md
源程序/
  全局变量.csv
  局部变量.csv
  ST/
    PRG0_Main.st
    PRG1_AutoSequence.st
    PRG2_Alarm.st
    PRG4_HMIManual.st
    PRG3_ModuleAndOutput.st
```

Split/add ST files by confirmed POU structure. Keep final output mapping last in actual task execution even if numeric POU names differ.

## CSV format and ordering

Ask for one variable CSV exported by the user's current ISPSoft version during G6. Preserve its exact header, separator, encoding, quoting, scope labels, address syntax, and Boolean spelling.

If no export sample is available, generate UTF-8 review CSV files with the following headers and clearly mark them `需按当前ISPSoft导入格式复核`:

- Global: `Order,Category,Name,DataType,Address,InitialValue,Retain,Producer,Consumer,Comment`
- Local: `POU,Order,Section,Name,DataType,InitialValue,Comment`

Sort variables deterministically:

1. inputs: physical/communication input images and `VAR_INPUT`
2. outputs: output requests/final output images and `VAR_OUTPUT`
3. shared status, command, parameter, and interface variables
4. local variables last; group by POU, then `VAR_INPUT`, `VAR_OUTPUT`, and `VAR`

Avoid `VAR_IN_OUT` unless explicitly confirmed. Within each group, sort by confirmed module/process order, then physical/D address numerically, then symbolic name. Keep multiword variables together and list the low/start address first.

For every FB, apply `templates/common/function-block-interface-template.md`: inputs are program state, servo state, sensor state, then settings; outputs are flow number, status, alarm, servo drive, cylinder action, then online interaction; locals are last.

## ST delivery rules

- Put a header in every ST file with project version and the confirmed-artifact revisions used.
- Declare or reference inputs first, outputs second, and local variables last.
- Keep one owner for every step, output request, physical output, alarm latch, and communication transmit word.
- Use symbolic variables from the CSV files; do not introduce undeclared variables in ST.
- Run a cross-file check: every ST symbol is declared, every generated variable has an owner/use or an explicit reserved reason, and data types/addresses match the confirmed I/O file.
- Deliver compile/import status honestly. Do not claim ISPSoft import or compilation unless performed in the user's actual version.
