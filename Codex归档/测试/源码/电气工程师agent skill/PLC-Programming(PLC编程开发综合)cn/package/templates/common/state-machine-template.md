<!-- 中文导读开始 -->

## 中文导读

本文件属于 templates/（输出模板），用于约束 AI 的交付格式，让代码、报告、检查清单或调试步骤稳定可复用。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# State machine template

## Purpose

Use for step-based machine or process control in FX3U ST projects.

## Suitable for

- sequential machine behavior
- explicit step transitions
- readable startup / run / stop / fault handling

## Suggested structure

- current state
- next-state conditions
- state entry actions if needed
- state-owned outputs
- fault / interlock override
- reset path

## ST skeleton

```st
CASE iState OF

    0: (* Idle *)
        bMotorRun := FALSE;
        IF bAutoMode AND bStartCmd AND NOT bFaultActive THEN
            iState := 10;
        END_IF;

    10: (* Pre-start checks *)
        IF bInterlockOK THEN
            iState := 20;
        ELSIF bFaultActive THEN
            iState := 900;
        END_IF;

    20: (* Run *)
        bMotorRun := TRUE;
        IF bStopCmd THEN
            iState := 0;
        ELSIF bFaultActive THEN
            iState := 900;
        END_IF;

    900: (* Fault *)
        bMotorRun := FALSE;
        IF bFaultResetCmd AND NOT bFaultActive THEN
            iState := 0;
        END_IF;

END_CASE;
```

## Notes

- Keep outputs owned by the active state where possible
- Keep fault transitions explicit
- Keep reset conditions separate from normal transitions
