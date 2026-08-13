<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/common/（通用 PLC 资料），记录跨厂商通用的 PLC 工程规则、检查清单、调试方法或输出格式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Program templates

Use this file as the template-selection entry for generation tasks.

## Role boundary

This file selects reusable logic structures.
It does not duplicate detailed task routing, review workflow, or debugging checklists.

Read with:

- `references/task-router.md` for task classification
- `references/output-format.md` for output shape
- `references/debugging-checklists.md` when a generated template should end with troubleshooting guidance

## Template selection

Choose the nearest reusable pattern:

- start or stop control
- mode selection
- sequence control
- state machine
- alarm latch and reset
- interlock block
- debounce or filter timing
- fault reset and recovery

## Output rule

Do not jump straight into a full monolithic program.

Prefer:

1. template purpose
2. assumptions
3. module boundary
4. variable or device suggestion
5. ST skeleton
6. scan notes
7. debug checklist

## Recommended template files

If available, use:

- `templates/state-machine-template.md`
- `templates/alarm-latch-reset-template.md`
- `templates/alarm-interlock-module-template.md`
- `templates/start-stop-interlock-template.md`
- `templates/sequence-step-template.md`
- `templates/timer-counter-diagnostic-template.md`
- `templates/output-ownership-review-template.md`

If a matching template does not exist, produce a compact reusable skeleton instead of a large one-off program.
