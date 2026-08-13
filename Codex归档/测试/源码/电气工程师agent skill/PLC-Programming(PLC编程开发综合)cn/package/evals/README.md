<!-- 中文导读开始 -->

## 中文导读

本文件属于 evals/（评测案例），用于测试 skill 什么时候应该触发、如何生成、如何审查，以及输入不完整或不该触发时的行为。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Eval index

Use this folder as a lightweight regression set for the skill.

## Current eval groups

- `eval-matrix.md`
- `generation-cases.md`
- `explanation-cases.md`
- `review-cases.md`
- `debugging-cases.md`
- `incomplete-input-cases.md`
- `non-trigger-cases.md`
- `routing-cases.md`
- `output-behavior-cases.md`

## Intended usage

When iterating the skill, check whether changes preserve:

1. trigger accuracy
2. output structure quality
3. conservative handling of missing information
4. conservative handling of safety-sensitive questions
5. stable review/debugging behavior

## Minimum regression checklist

Before accepting a major skill edit, verify:

- should-trigger cases still clearly trigger
- non-trigger cases do not over-expand the skill
- incomplete-input cases produce assumptions or clarification, not fake certainty
- debugging cases prioritize fault isolation over guesswork
- review cases prioritize ownership and structure, not cosmetic comments
