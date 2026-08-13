<!-- 中文导读开始 -->

## 中文导读

本文件属于 templates/（输出模板），用于约束 AI 的交付格式，让代码、报告、检查清单或调试步骤稳定可复用。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Alarm latch and reset template

## Purpose

Use for alarm set, hold, display, and reset logic that must remain readable and easy to debug.

## Suitable for

- process alarms
- timeout alarms
- permissive-loss alarms
- resettable fault states

## Suggested structure

- alarm trigger condition
- latch behavior
- hold behavior
- reset permissive condition
- reset command handling
- re-latch prevention check

## ST skeleton

```st
IF bAlarmTrigger THEN
    bAlarmActive := TRUE;
END_IF;

IF bAlarmResetCmd AND bResetPermissive AND NOT bAlarmTrigger THEN
    bAlarmActive := FALSE;
END_IF;
```

## Notes

- Keep set and reset conditions explicit
- Prevent immediate re-latch after reset when possible
- Separate alarm source from HMI acknowledge if they are different concerns
