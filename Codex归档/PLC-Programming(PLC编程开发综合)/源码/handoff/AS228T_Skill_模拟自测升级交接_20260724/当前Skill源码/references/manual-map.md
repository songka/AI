# Manual-derived topic map

Use the narrowest reference below. Source identifiers resolve in `official-doc-index.md`.

| Question | Read | Primary official evidence |
| --- | --- | --- |
| CPU, power, ports, onboard X/Y, output type | `hardware-io.md` | HOM-2024, AS228-IS |
| Device capacity, retain range, SM/SR | `devices-retention.md` | PM-2024 ch.2 |
| Instruction existence or operands | current PM-2024 instruction entry | PM-2024 ch.3 onward |
| ISPSoft project, POU, task, symbol, ST | `ispsoft-workflow.md` | ISP-2020 ch.3/5/6/13/17 |
| HWCONFIG and expansion allocation | `hardware-io.md`, `ispsoft-workflow.md` | HOM-2024, OM-2020 ch.8 |
| RS-485, Ethernet, Socket, Modbus, CANopen | `communications.md` | OM-2020, SOCKET-2019, Delta FAQ |
| Pulse or CANopen positioning | `positioning.md` | HOM-2024, PM-2024, product page |
| I/O table, D-bit map, robot, alarm, HMI manual interface | `io-addressing-standard.md` | PM-2024 ch.2, ISPSoft manual, CiA/ODVA |
| LED, SR error log, watchdog, duplicate output | `diagnostics.md` | HOM-2024, PM-2024 sec.2.2.14/2.2.15 |
| Forcing, bypass, online change, field test | `safety-boundaries.md` | safety policy plus exact hardware manual |

## Evidence discipline

- Treat AS-family marketing limits as family-level until the AS228T-A output/channel table confirms them.
- Treat every SM/SR, instruction, retain range, menu path, and communication limit as revision/firmware-sensitive.
- Use manual title, revision date, chapter/section, CPU model, firmware, and ISPSoft version in high-risk answers.
- Do not bundle or reproduce complete manuals. Store concise engineering notes and link to official sources for lawful internal consultation.
- If the current official download requires accepting Delta terms, direct the user to the Download Center; do not bypass access controls or TLS validation.
