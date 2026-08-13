<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/common/（通用 PLC 资料），记录跨厂商通用的 PLC 工程规则、检查清单、调试方法或输出格式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Input completeness rules

Use this file when the request does not provide enough engineering detail.

## Goal

Continue helpfully without pretending certainty.

## Three levels of incompleteness

### Level 1: Missing details but usable for a draft

Examples:
- exact variable naming convention missing
- exact device allocation missing
- some sequence details missing
- exact ST declaration block missing

Behavior:
- continue
- state assumptions
- provide a draft, skeleton, or template
- mark syntax-sensitive areas clearly

### Level 2: Missing project structure details

Examples:
- unclear whether this is Structured Project
- unclear how modules are split
- no I/O list
- no existing code provided for a review request

Behavior:
- continue with a proposed structure
- avoid claiming this is final project-ready code
- ask for the minimum missing engineering inputs if needed
- prefer modular templates over full locked-down implementation

### Level 3: Missing safety-critical field facts

Examples:
- unknown wiring polarity
- unknown fail-safe design
- unknown actuator behavior
- unknown emergency stop architecture
- unknown output force / bypass consequences

Behavior:
- do not give a final safety conclusion
- do not imply the logic is safe
- provide verification steps, review points, and caution notes
- explicitly list what must be confirmed on site

## Recommended wording pattern

Use labels such as:

- Known
- Assumed
- Open point
- Must confirm on site

## For debugging tasks

If abnormal behavior is reported but evidence is weak, first collect:

1. symptom
2. trigger condition
3. related inputs
4. related outputs
5. current state / step
6. timers / counters involved
7. whether other sections write the same output
8. whether online monitoring confirms the hypothesis
