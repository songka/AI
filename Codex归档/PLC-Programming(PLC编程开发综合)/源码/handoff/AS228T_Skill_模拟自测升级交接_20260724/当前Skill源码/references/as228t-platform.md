# AS228T-A platform facts

Use this file only for the company-standard Delta AS228T-A. Treat a bare AS228T mention as AS228T-A. Use ISPSoft 3.19 or later and ST by default without confirmation.

## Confirmed AS228T-A context

- Engineering software: ISPSoft 3.19 or later.
- Execution model: cyclic program execution with configurable tasks and direct/refreshed I/O behavior.
- Company implementation language: ST. Other IEC languages may exist in the product but are outside this Skill's generation scope.
- AS200 program capacity: 64K steps.
- Onboard I/O shown in the official AS228T-A instruction sheet:
  - inputs: `X0.0` through `X0.15` (16 points)
  - outputs: `Y0.0` through `Y0.11` (12 points)
- `AS228T-A` uses transistor-T sinking (NPN) outputs. This Skill does not support another AS228 suffix/model.
- Official AS228T-A output rating shown in the hardware manual: 5–30 VDC, 0.5 A per output, 2 A per common. Apply derating, load type, inrush, protection, and wiring requirements from the current manual.

## Device capacities documented for AS228T-A / AS200

| Device | Documented range/capacity |
| --- | --- |
| Input relay | X, 1024 points |
| Output relay | Y, 1024 points |
| Internal relay | `M0–M8191` |
| Timer | `T0–T511` |
| Counter | `C0–C511` |
| 32-bit high-speed counter | `HC0–HC255` |
| Data register | `D0–D29999` |
| Data register | `W0–W29999` |
| Step relay | `S0–S2047` |
| Index register | `E0–E9` |
| Special auxiliary relay | `SM0–SM2047` |
| Special data register | `SR0–SR2047` |

These capacities do not establish retention, access rights, time bases, special-register meanings, or which addresses are already reserved by the project. Confirm those separately.

Read `devices-retention.md` for the verified default retain ranges and `diagnostics.md` for the small verified SR error subset.

## Addressing rule

Do not reuse DVP octal examples such as “X7 then X10”. AS228T documentation uses dotted onboard addresses and explicitly includes `X0.8`, `X0.9`, `X0.10`, etc. Read expansion I/O addresses from ISPSoft HWCONFIG instead of calculating them from a generic rule.

## Project facts to collect

Before project-ready code, obtain the smallest relevant set:

- task name/type and POU execution order
- actual HWCONFIG and expansion modules
- I/O list with electrical meaning and NO/NC polarity
- output load/interface circuit
- retained/non-retained variable requirements
- HMI/SCADA/drive communication map
- positioning axes, limits, homing method, and drive safety chain

Do not ask the user to confirm PLC model, normal ISPSoft baseline, firmware, or language. Record the fixed defaults as AS228T-A, ISPSoft 3.19+, firmware not required, and ST. Surface firmware only when an official firmware gate directly blocks a specifically requested feature.

Use `hardware-io.md`, `ispsoft-workflow.md`, `communications.md`, or `positioning.md` for topic-specific facts rather than expanding this overview.

## Do not infer

- DVP special M/D meanings or ranges
- DVP timer bases and timer instructions
- WPLSoft import or project behavior
- pulse-output channel assignments or maximum frequency without the exact manual section
- high-speed input filtering or counter mode without HWCONFIG confirmation
- retention behavior from an address alone
- safety integrity from standard PLC code
