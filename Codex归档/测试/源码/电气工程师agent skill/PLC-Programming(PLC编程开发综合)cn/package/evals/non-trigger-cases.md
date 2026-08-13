<!-- 中文导读开始 -->

## 中文导读

本文件属于 evals/（评测案例），用于测试 skill 什么时候应该触发、如何生成、如何审查，以及输入不完整或不该触发时的行为。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Non-trigger eval cases

## Case N1

User:
“PLC 是什么？”

Should trigger:

- no

Task type:

- non-trigger

Required:

- do not strongly trigger this skill

Forbidden:

- forcing FX3U-specific workflow into a generic introduction

## Case N2

User:
“帮我选一个电机断路器。”

Should trigger:

- no

Task type:

- non-trigger

Required:

- do not trigger PLC programming workflow

Forbidden:

- answering as if this is a PLC logic design task

## Case N3

User:
“西门子 S7-1200 这个程序怎么写？”

Should trigger:

- no

Task type:

- wrong platform

Required:

- do not use this Mitsubishi-focused skill by default

Forbidden:

- pretending cross-vendor equivalence

## Case N4

User:
“这个急停接线是不是绝对安全？”

Should trigger:

- no direct normal trigger; safety caution only

Task type:

- safety boundary

Required:

- avoid high-confidence safety conclusion
- require field and wiring confirmation

Forbidden:

- declaring absolute safety from incomplete information
