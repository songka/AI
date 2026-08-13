<!-- 中文导读开始 -->

## 中文导读

本文件属于 templates/（输出模板），用于约束 AI 的交付格式，让代码、报告、检查清单或调试步骤稳定可复用。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Sequence step template

## Purpose

Use for simple ordered process steps when a full state-machine explanation is not necessary.

## Suggested structure

- current step marker
- step completion condition
- next step transition
- timeout or abnormal branch
- reset branch

## ST skeleton

```st
IF iStep = 10 THEN
    IF bStep10Done THEN
        iStep := 20;
    ELSIF bStep10Timeout THEN
        iStep := 900;
    END_IF;
END_IF;
```

## Notes

- Make transitions explicit
- Avoid hidden writes to the same step variable in multiple places
- Keep timeout and fault transitions visible
