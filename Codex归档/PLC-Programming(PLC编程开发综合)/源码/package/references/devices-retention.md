# AS228T devices, retention, and special registers

## Capacity map

| Device | AS228T/AS200 capacity |
| --- | --- |
| X / Y | 1024 points each |
| M | `M0–M8191` |
| T | `T0–T511` |
| C | `C0–C511` |
| HC | `HC0–HC255` |
| D | `D0–D29999` |
| W | `W0–W29999` |
| S | `S0–S2047` |
| E | `E0–E9` |
| SM | `SM0–SM2047` |
| SR | `SR0–SR2047` |

Source: HOM-2024/OM-2020 AS228T-A functional specification table.

## Retention

PM-2024 sec.2.1.4 documents configurable retained areas. Defaults shown for AS100/200 include:

- M retained area: `M6000–M8191`
- C retained area: `C448–C511`
- HC retained area: `HC128–HC255`
- D retained area: `D20000–D23999`
- X, Y, T, and E0–E9: non-retained
- FR: retained

Treat these as manual defaults, not proof of the current project. HWCONFIG can change supported retained ranges, firmware can affect behavior, and a download/initialization command can clear values.

## STOP/RUN and clearing

- The documented default for STOP→RUN is to clear non-retained areas.
- The documented default for RUN→STOP is to clear Y state.
- Special flags can clear retained or non-retained areas; verify the exact PM-2024 entry before use.
- Back up critical device values before downloads, initialization, retain-range changes, or battery/memory work.

## SM/SR rule

Never infer a special-register meaning from its number. Check the exact PM-2024 table for:

- AS100/200 applicability
- read-only versus read/write
- default and refresh timing
- retained attribute
- firmware requirement
- paired SM/SR behavior

Use `diagnostics.md` only for the small verified error-register subset listed there.

