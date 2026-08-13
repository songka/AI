<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/common/（通用 PLC 资料），记录跨厂商通用的 PLC 工程规则、检查清单、调试方法或输出格式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Debugging checklists

Use this file for troubleshooting checklists after the shared workflow has identified the likely fault path.

## Role boundary

This file defines fault-isolation checklists.
It does not repeat the shared troubleshooting workflow.

Read first when needed:

- `references/debugging-and-review.md` for workflow and evidence handling
- `references/scan-cycle-and-output-ownership.md` when scan order or multi-writer risk is involved

## Quick fault isolation checklist

Check in this order when possible:

1. Is the observed symptom clearly defined?
2. Which input conditions are expected but missing?
3. Which state or step should be active right now?
4. Are timers or counters reaching their expected condition?
5. Is the output written in more than one place?
6. Is a reset condition clearing a latch unexpectedly?
7. Is an interlock blocking the transition?
8. Is scan order affecting the visible result?
9. Does online monitoring match the mental model?
10. Is the problem logic-side, device-side, or field-side?

## Alarm troubleshooting checklist

- alarm trigger condition
- latch condition
- hold condition
- reset condition
- reset permissive condition
- whether another block re-latches immediately
- whether alarm state and HMI state are consistent

## Sequence troubleshooting checklist

- current step
- step entry condition
- step exit condition
- timeout condition
- reset path
- manual or auto mode interaction
- whether outputs are step-owned or globally overwritten

## Output overwrite checklist

- list every location that writes the output
- identify intended owner
- check later logic blocks in scan order
- check force, manual mode, and reset sections
- check startup initialization logic
