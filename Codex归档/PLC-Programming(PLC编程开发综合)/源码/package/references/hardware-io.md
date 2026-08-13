# AS228T-A hardware and I/O

## Confirmed CPU facts

- Supply: 24 VDC; HOM-2022/2024 lists an operating range of 20.4–28.8 VDC.
- Onboard digital inputs: 16 points, `X0.0` through `X0.15`, 24 VDC input; the instruction sheet shows sinking or sourcing input wiring.
- Onboard digital outputs: 12 points, `Y0.0` through `Y0.11`.
- `AS228T-A`: transistor-T sinking (NPN) outputs, 5–30 VDC, 0.5 A per output, 2 A per common.
- Built-in interfaces: Ethernet 10/100 M, two RS-485 ports, USB, Micro SD, and CAN/CANopen interface as shown for AS200.
- The AS Series CPU supports expansion through HWCONFIG; obtain actual X/Y/D allocation from the project rather than calculating it.

Sources: HOM-2024 sec.2.2 and 4.6.8; AS228-IS; HOM-2022 sec.2.2.1/2.2.2.

## Addressing and mapping

- Use dotted onboard addresses; `X0.8` and `X0.9` are valid AS228T addresses.
- Keep physical X/Y references in mapping POUs. Use symbols in equipment and sequence logic.
- Use ISPSoft HWCONFIG/module table for expansion addresses.
- When module changes must not shift assigned areas, review the official “Manual + Flags” I/O-allocation option and the complete project consequences before enabling it.

## Wiring checklist

Before giving field instructions, confirm:

- input sink/source topology and S/S wiring
- output common grouping, load current, inrush, leakage, and polarity
- external fuse/protection and inductive-load suppression
- 24 V supply capacity, grounding, shielding, and separation from noisy power wiring
- safe state on CPU STOP, power loss, cable break, and output-device failure

Do not infer wiring from logical TRUE/FALSE names. Use the current manual diagram and the real schematic.
