<!-- 中文导读开始 -->

## 中文导读

本文件属于 evals/（评测案例），用于测试 skill 什么时候应该触发、如何生成、如何审查，以及输入不完整或不该触发时的行为。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Generation eval cases

## Case G1: Motor start-stop with interlock

User:
“帮我写一个 FX3U 的 ST 电机启停逻辑，要求放在 GX Works2 Structured Project 里，带自动模式、停止命令和故障联锁。”

Should trigger:

- yes

Task type:

- generation

Required:

- propose structure before code
- separate request, permissive, inhibit, and output
- stay within FX3U + GX Works2 + ST context
- end with test or debug checklist

Forbidden:

- giant monolithic code dump without structure
- generic non-platform answer

## Case G2: Sequence state machine

User:
“根据这套工艺步骤设计 FX3U 的 ST 状态机，后续方便在线调试和扩展。”

Should trigger:

- yes

Task type:

- generation

Required:

- recommend state or step structure
- show transitions and fault path
- prefer maintainable structure over flat condition chain

Forbidden:

- hiding fault branch
- producing only abstract theory with no structural proposal

## Case G3: Incomplete requirements

User:
“帮我写 PLC 程序控制一个循环动作。”

Should trigger:

- clarify first or continue with explicit assumptions

Task type:

- ambiguous generation

Required:

- ask for missing engineering details or declare assumptions
- avoid claiming final project-ready code
- prefer template or skeleton if details stay incomplete

Forbidden:

- pretending device allocation and structure are already known
- presenting final locked-down code with no assumptions
