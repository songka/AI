<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/common/（通用 PLC 资料），记录跨厂商通用的 PLC 工程规则、检查清单、调试方法或输出格式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Safety boundaries

Use this file when the task touches wiring, interlocks, machine safety, forced outputs, or any control decision that could be hazardous if assumptions are wrong.

## Conservative limits

Do not present high-confidence safety conclusions when any of these are unconfirmed:

- wiring details
- normally-open or normally-closed semantics in the field
- actuator behavior
- fail-safe requirements
- emergency-stop or guard-circuit architecture
- electrical protection and hardware boundaries

## Required response behavior

- State what is known.
- State what is assumed.
- State what must be confirmed on site or from project documents.
- Prefer giving verification steps, design cautions, and review points over giving a dangerous final conclusion.

## Typical caution areas

- emergency stop logic
- safety door logic
- motion enable logic
- forced outputs
- bypass logic
- reset behavior after fault or power cycle
- interlocks that protect people or equipment
