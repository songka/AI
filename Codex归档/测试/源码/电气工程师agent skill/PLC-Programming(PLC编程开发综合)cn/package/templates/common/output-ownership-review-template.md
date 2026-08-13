<!-- 中文导读开始 -->

## 中文导读

本文件属于 templates/（输出模板），用于约束 AI 的交付格式，让代码、报告、检查清单或调试步骤稳定可复用。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Output ownership review template

## Purpose

Use when reviewing ST or GX Works2 project logic for conflicting writes, hidden ownership, and scan-cycle side effects.

## Review target

Identify one critical target first:

- output bit
- run command
- alarm state
- step/state variable

## Review structure

### 1. Target
- Which variable/output/state is under review?

### 2. Intended owner
- Which block or module should own it?

### 3. Known writers
- Where is it set?
- Where is it cleared?
- Where is it reset or initialized?

### 4. Priority model
- Which condition should win if conflicts exist?

### 5. Observed risk
- overwrite risk
- delayed clear
- immediate reset
- hidden mode dependency

### 6. Recommended cleanup
- centralize ownership
- separate mode logic
- separate reset logic
- move inhibit logic nearer to final decision point

## Reviewer output recommendation

For each ownership issue, report:
1. conflicting writers
2. execution risk
3. likely symptom online
4. recommended restructuring
