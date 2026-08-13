<!-- 中文导读开始 -->

## 中文导读

本文件属于 templates/（输出模板），用于约束 AI 的交付格式，让代码、报告、检查清单或调试步骤稳定可复用。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Template map

Use this file to choose the nearest reusable template before writing a large custom answer.

## Common template selection

- Standard equipment module (Auto/Manual/Fault handling)
  - `templates/common/equipment-module-template.md`

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

## Selection rules

- Prefer state-machine and step templates for expandable sequential processes.
- Prefer alarm/reset templates when fault memory and recovery are the focus.
- Prefer output-ownership review before rewriting a large code block.
- If vendor-specific syntax matters, combine the common template with the vendor module instead of inventing cross-vendor syntax.
