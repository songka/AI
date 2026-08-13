<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/common/（通用 PLC 资料），记录跨厂商通用的 PLC 工程规则、检查清单、调试方法或输出格式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Response fallback rules

Use this file when evidence is incomplete, the request is ambiguous, or safety confidence must be reduced.

## Fallback levels

### Level 1: Enough for a draft

Use when the task is in-scope and the missing details do not block a useful engineering draft.

Behavior:
- continue
- mark assumptions explicitly
- provide a draft, skeleton, or template
- highlight syntax-sensitive or device-allocation-sensitive areas

### Level 2: Enough for structure, not final implementation

Use when project structure, declarations, I/O mapping, or existing code context is missing.

Behavior:
- give a proposed module structure
- avoid claiming project-ready final code
- ask for the minimum missing engineering inputs
- prefer partial rewrite or template over locked-down implementation

### Level 3: Enough only for risk review

Use when field wiring, fail-safe behavior, actuator response, or machine safety conditions are unknown.

Behavior:
- do not give a final safety conclusion
- do not imply the logic is safe
- provide verification steps, review points, and caution notes
- list what must be confirmed on site or in project documents

## Recommended labels

Use labels such as:
- Known
- Confirmed fact
- Assumption
- Open point
- Must confirm on site

## Safe downgrade patterns

- From final code -> template or skeleton
- From root-cause claim -> ranked hypotheses
- From implementation advice -> verification checklist
- From confident review judgment -> conditional findings with assumptions

## Avoid

- pretending uncertain platform behavior is confirmed
- treating generic PLC rules as exact Mitsubishi behavior
- giving safety approval without field confirmation
- presenting a one-off guess as the only likely cause

