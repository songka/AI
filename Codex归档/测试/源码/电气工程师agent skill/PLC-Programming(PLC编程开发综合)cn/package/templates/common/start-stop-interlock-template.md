<!-- 中文导读开始 -->

## 中文导读

本文件属于 templates/（输出模板），用于约束 AI 的交付格式，让代码、报告、检查清单或调试步骤稳定可复用。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Start-stop interlock template

## Purpose

Use for standard motor or actuator start/stop control with explicit permissives and interlocks.

## Suggested structure

- mode permissive
- start command
- stop command
- run latch or run state
- interlock block
- fault block

## ST skeleton

```st
IF bStopCmd OR bFaultActive OR NOT bInterlockOK THEN
    bRunCmd := FALSE;
ELSIF bStartCmd AND bModeAuto THEN
    bRunCmd := TRUE;
END_IF;
```

## Notes

- Keep stop, fault, and interlock inhibition ahead of start enable
- Make output ownership clear
- If seal-in behavior is used, make reset paths obvious
