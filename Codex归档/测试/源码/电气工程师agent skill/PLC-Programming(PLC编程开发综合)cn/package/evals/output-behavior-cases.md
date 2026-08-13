<!-- 中文导读开始 -->

## 中文导读

本文件属于 evals/（评测案例），用于测试 skill 什么时候应该触发、如何生成、如何审查，以及输入不完整或不该触发时的行为。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Output behavior eval cases

## Case O1: Code generation shape

Should trigger:

- generation output format

Task type:

- output behavior

Required:

- requirement understanding
- assumptions
- structured design before code
- ST skeleton or code
- test checklist

Forbidden:

- immediate monolithic code dump with no structure

## Case O2: Code explanation shape

Should trigger:

- explanation output format

Task type:

- output behavior

Required:

- what the code does
- confirmed facts vs assumptions
- scan-cycle interpretation

Forbidden:

- mixing assumptions into facts without labels

## Case O3: Review or refactor shape

Should trigger:

- review output format

Task type:

- output behavior

Required:

- issue list
- impact explanation
- refactoring direction
- validation checklist

Forbidden:

- cosmetic comments only

## Case O4: Debugging shape

Should trigger:

- debugging output format

Task type:

- output behavior

Required:

- symptom restatement
- hypotheses separated from facts
- practical debug plan
- safe verification points

Forbidden:

- unsupported single-cause certainty
