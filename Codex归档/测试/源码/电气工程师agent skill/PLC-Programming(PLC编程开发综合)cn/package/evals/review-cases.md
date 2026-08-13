<!-- 中文导读开始 -->

## 中文导读

本文件属于 evals/（评测案例），用于测试 skill 什么时候应该触发、如何生成、如何审查，以及输入不完整或不该触发时的行为。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Review eval cases

## Case R1: Output ownership conflict

User:
“帮我审查这段 GX Works2 Structured Project 里的 ST 逻辑，怀疑同一个输出被多个地方写了。”

Should trigger:

- yes

Task type:

- review

Required:

- trigger review workflow
- prioritize ownership analysis
- suggest structural cleanup before cosmetic rewrite
- mention impact on maintainability or debugging

Forbidden:

- large rewrite without ownership diagnosis
- ignoring multi-writer risk

## Case R2: Maintainability review

User:
“这段顺控逻辑后续维护会不会很痛苦？帮我从结构上审查。”

Should trigger:

- yes

Task type:

- review

Required:

- inspect module boundaries, state visibility, and alarm/reset handling
- output findings, impact, and recommended changes
- keep comments technical and structure-oriented

Forbidden:

- cosmetic-only comments
- rewriting everything without explaining why
