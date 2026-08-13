<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/vendors/（厂商资料），记录具体 PLC 厂商的软件环境、术语、型号线索、指令规则或官方文档入口。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Delta Electronics Official Documentation Index

This file indexes official Delta Electronics documentation for DVP-series PLCs and programming software.

## Primary Documentation Sources

### Delta Download Center
- Main portal: https://downloadcenter.deltaww.com
- Search by product series (DVP, AH, AS)
- Manuals available in multiple languages

### DVP-Series PLC Documentation

#### DVP-PLC Application Manual: Programming
- PDF: https://deltronics.ru/images/manual/DVP-PLC_PM_EN_20170615.pdf
- Covers: DVP ES/EX/SS/SA/SX/SC/EH2/EH3/SV/SV2 series
- Contents:
  - Basic ladder logic programming principles
  - Instruction set reference
  - Memory map and device addressing
  - Special modules and communication

#### DVP-PLC Operation Manual
- Covers hardware specifications, wiring, and installation
- Series-specific (ES2, EX2, SS2, SA2, SX2, etc.)

#### ISPSoft User Manual
- PDF: https://industrialautomation.delta-emea.com/downloads/DELTA_IA-PLC_ISPSoft_UM_EN_20170614%20(1).pdf.pdf
- Modern programming software for AH/AS series and newer DVP models
- Supports:
  - Ladder Diagram (LD)
  - Sequential Function Chart (SFC)
  - Structured Text (ST) - limited support
  - Function Block Diagram (FBD)

#### WPLSoft User Manual
- Legacy programming software for DVP series
- Primarily Ladder Diagram (LD) focused
- Still widely used for DVP-ES, DVP-EX, DVP-SS series

## Controller Families

### DVP Series (Micro/Compact PLCs)
- **DVP-ES/EX/SS/SA/SX**: Entry-level, compact PLCs
- **DVP-EH2/EH3**: Enhanced models with Ethernet
- **DVP-SV/SV2**: Slim, space-saving models
- **DVP-SC**: Motion control integrated

### AH Series (Advanced PLCs)
- High-performance controllers
- Native Ethernet and EtherCAT support
- Programmed with ISPSoft

### AS Series (Motion Control PLCs)
- Integrated motion control
- EtherCAT motion bus
- Programmed with ISPSoft

## Programming Software

### ISPSoft (Modern)
- **Used for**: AH series, AS series, newer DVP models
- **Languages**: LD, SFC, ST (limited), FBD
- **Features**: IEC 61131-3 partial compliance, simulation, online debugging

### WPLSoft (Legacy)
- **Used for**: DVP-ES, DVP-EX, DVP-SS, DVP-SA, DVP-SX series
- **Languages**: Primarily Ladder Diagram (LD)
- **Features**: Simple, lightweight, widely deployed

## Memory Addressing

Delta PLCs use a device-based addressing system:

| Device | Type | Description |
|--------|------|-------------|
| X | Input | External inputs (X0~X377, octal) |
| Y | Output | External outputs (Y0~Y377, octal) |
| M | Auxiliary Relay | Internal bits (M0~M4095) |
| S | Step Relay | For SFC programming (S0~S1023) |
| T | Timer | Timers (T0~T255) |
| C | Counter | 16-bit and 32-bit counters (C0~C255) |
| D | Data Register | 16-bit data storage (D0~D9999) |

**Note:** X and Y use **octal numbering** (0-7), not decimal.

## Evidence Priority

When answering Delta-specific questions, use sources in this order:
1. Official Delta manuals (DVP-PLC Programming Manual, ISPSoft User Manual)
2. Delta Download Center resources
3. IEC 61131-3 standards (for ISPSoft language-level questions)
4. Community resources (lowest priority)

---
Last updated: 2026-04-06
