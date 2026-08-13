<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/vendors/（厂商资料），记录具体 PLC 厂商的软件环境、术语、型号线索、指令规则或官方文档入口。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# FX3U focus

Use this file when the task is specifically about Mitsubishi FX3U development.

## Version-1 scope

Stay centered on:

- FX3U PLC development knowledge needed for programming work
- device-level reasoning needed for logic design and troubleshooting
- practical interpretation of timers, counters, internal relays, data registers, and related device usage
- engineering behavior in GX Works2 Structured Project and ST-oriented workflows

## Working approach

For FX3U tasks:

1. Identify what is confirmed:
   - exact PLC family or CPU assumption
   - programming language in use
   - whether the code is for Structured Project
   - whether the question concerns design, explanation, review, or troubleshooting
2. Separate:
   - documented device or instruction behavior
   - project-specific conventions
   - inferred engineering advice
3. Prefer maintainable device and variable organization over ad-hoc addressing.

## Typical task classes

- Explain device usage and likely role in logic
- Convert process steps into modular control logic
- Suggest state-machine or sequence structure
- Review timer or counter usage
- Analyze interlocks, alarm holds, resets, and edge conditions
- Troubleshoot scan-related behavior and overwritten outputs

## Avoid overreach

- Do not generalize from other Mitsubishi families unless clearly marked.
- Do not assume hardware wiring, field polarity, fail-safe strategy, or machine sequence details.
- Do not present hazardous control advice as complete without field confirmation.
