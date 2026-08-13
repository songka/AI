# Delta AS228T official source index

Use official Delta sources first. Confirm revision, CPU family applicability, firmware, and ISPSoft version. Direct PDF access may require accepting Delta's current download terms.

## Core manuals

### HOM-2024 — AS Series Hardware and Operation Manual, 2024-10-25

Use for CPU/electrical specifications, AS228T-A terminals and wiring, ports, modules, LEDs, HWCONFIG-related hardware behavior, and troubleshooting.

`https://filecenter.deltaww.com/Products/download/06/060301/Manual/DELTA_IA-PLC_AS_HOM_EN_20241025.pdf`

### HOM-2022 — AS Series Hardware and Operation Manual, 2022-05-30 (archived comparison revision)

Use only when a detail is absent from the indexed 2024 text or when supporting older firmware/projects; prefer HOM-2024 for current work.

`https://filecenter.deltaww.com/Products/download/06/060301/Manual/DELTA_IA-PLC_AS_HOM_EN_20220530.pdf`

### PM-2024 — AS Series Programming Manual, 2024-09-20

Use for device/retention tables, SM/SR, basic/applied instructions, data types, high-speed I/O, communication instructions, and instruction-specific firmware/applicability notes.

`https://filecenter.deltaww.com/Products/download/06/060301/Manual/DELTA_IA-PLC_AS_PM_EN_20240920.pdf`

### ISP-2020 — ISPSoft User Manual, 2020-03-12

Use for HWCONFIG, tasks/POUs, symbols, FB/DUT, LD/FBD/ST/SFC editors, online/debug tools, project import/export, and compare workflow. Cross-check menu names with the installed ISPSoft version.

`https://filecenter.deltaww.com/Products/download/06/060301/Manual/DELTA_IA-PLC_ISPSoft_UM_EN_20200312.pdf`

### OM-2020 — AS Series Operation Manual, 2020-07-07

Use as an older split-volume reference for CPU functions, tasks, HWCONFIG, data exchange, Ethernet, and troubleshooting. Prefer HOM-2024/PM-2024 where newer content overlaps.

`https://filecenter.deltaww.com/Products/download/06/060301/Manual/DELTA_IA-PLC_AS_OM_EN_20200707.pdf`

### MOD-2024 — AS Series Module Manual, 2024-04-30

Use only when the actual project contains the relevant AS expansion module. Confirm module suffix and hardware version.

`https://filecenter.deltaww.com/Products/download/06/060301/Manual/DELTA_IA-PLC_AS_MdM_EN_20240430.pdf`

### AS228-IS — AS228R-A / AS228T-A / AS228P-A Instruction Sheet

Use for model identification, onboard terminal layout, basic wiring, and installation cautions.

`https://filecenter.deltaww.com/Products/download/06/060301/Manual/DELTA_IA-PLC_AS228-T-P-R-B_I_TSE_20171218..pdf`

## Communication application notes and FAQs

### SOCKET-2019 — AH/AS Series Socket Communication Instructions

`https://filecenter.deltaww.com/Products/download/06/060301/Application%20Note/DELTA_IA-PLC_SOCKET_AN_EN_20190507.pdf`

- AS Socket setup/status FAQ: `https://www.deltaww.com/en-US/service-support/faq/2209`
- Modbus TCP single-connection merge, firmware-gated: `https://www.deltaww.com/zh-TW/service-support/faq/2467`

## ISPSoft operational FAQs

- Compare project with file or PLC: `https://www.deltaww.com/zh-TW/service-support/faq/2085`
- Used Device Report: `https://www.deltaww.com/en-US/service-support/faq/2093`
- Simulator limitations: `https://www.deltaww.com/zh-TW/service-support/faq/635`
- Relocate AS module register area: `https://www.deltaww.com/en-US/service-support/faq/2363`

## Product and download entry points

- AS Series product page: `https://landing.deltaww.com/en-US/products/PLC-Programmable-Logic-Controllers/3495`
- Delta Download Center: `https://downloadcenter.deltaww.com`

## Evidence order

1. installed AS228T-A nameplate, firmware, wiring, and actual ISPSoft project/HWCONFIG
2. latest applicable official hardware/programming manual
3. ISPSoft help/manual matching the installed version
4. exact module/drive/application manual
5. official Delta FAQ/application note with its version conditions
6. generic engineering guidance
7. community material only as a labeled lead

Do not use DVP manuals or examples to establish AS228T behavior. Do not redistribute complete Delta manuals; link to the official source and keep only concise internal engineering notes.
