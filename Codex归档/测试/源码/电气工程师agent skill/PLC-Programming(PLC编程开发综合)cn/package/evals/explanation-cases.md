<!-- 中文导读开始 -->

## 中文导读

本文件属于 evals/（评测案例），用于测试 skill 什么时候应该触发、如何生成、如何审查，以及输入不完整或不该触发时的行为。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Explanation eval cases

## Case E1: Explain ST logic

User:
“解释一下这段 FX3U 的 ST 逻辑在做什么。”

Should trigger:

- yes

Task type:

- explanation

Required:

- describe visible behavior first
- separate confirmed facts and assumptions
- mention scan-cycle interpretation if relevant

Forbidden:

- treating assumptions as confirmed facts
- giving platform claims unsupported by evidence

## Case E2: Explain timer problem

User:
“这段定时器逻辑看起来没问题，为什么一直不动作？”

Should trigger:

- yes

Task type:

- explanation with troubleshooting direction

Required:

- inspect enable, reset, and completion path
- explain likely control intent before claiming device fault
- keep unsupported platform claims out

Forbidden:

- jumping to exact Mitsubishi rule without support
- saying the timer is broken without logic inspection
