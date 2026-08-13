<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/common/（通用 PLC 资料），记录跨厂商通用的 PLC 工程规则、检查清单、调试方法或输出格式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Debugging and review workflow

Use this file as the shared workflow entry for troubleshooting, code review, refactoring, or behavior analysis.

## Role boundary

This file defines:

- task framing
- observable-first workflow
- evidence handling
- refactoring direction

This file does not duplicate detailed checklists.

Use these companions instead:

- `references/debugging-checklists.md` for fault-isolation checklists
- `references/code-review-checklists.md` for review findings and report shape
- `references/gxworks2-project-review-patterns.md` for GX Works2 project-level maintainability patterns

## Shared operating rules

Start from observable behavior or visible structure before proposing code changes.

Always separate:

1. observed facts
2. inferred hypotheses
3. recommended checks
4. proposed corrections

Prefer the smallest useful diagnosis path before a rewrite.

## Debugging workflow

Start from observable behavior and narrow down:

1. Restate the abnormal behavior in operational terms.
2. Identify the involved inputs, conditions, states, timers, counters, and outputs.
3. Classify the likely fault path:
   - missing input condition
   - wrong state transition
   - timer or counter not reaching condition
   - latch or reset conflict
   - output overwrite in another section
   - wrong scan-cycle assumption
4. Separate observed evidence from hypotheses.
5. Build a practical check order before suggesting corrections.

Then read:

- `references/debugging-checklists.md`
- `references/scan-cycle-and-output-ownership.md`
- `references/alarm-and-interlock-patterns.md` when alarms or interlocks are involved

## Review workflow

For review or refactor tasks, assess structure before style:

1. module boundaries
2. state visibility and transition clarity
3. output ownership
4. alarm, interlock, and reset completeness
5. hidden dependencies and duplicate logic
6. maintainability under future changes

Then read:

- `references/code-review-checklists.md`
- `references/gxworks2-project-review-patterns.md`
- `references/scan-cycle-and-output-ownership.md` when writer conflicts are suspected

## Refactoring preference

Refactor toward:

- clearer separation of concerns
- fewer conflicting writes
- explicit state handling
- reusable patterns
- easier online monitoring and maintenance

Prefer structural cleanup over full rewrite unless the user explicitly asks for replacement design.
