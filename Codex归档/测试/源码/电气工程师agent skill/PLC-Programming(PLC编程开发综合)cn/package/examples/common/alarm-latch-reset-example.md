<!-- 中文导读开始 -->

## 中文导读

本文件属于 examples/（通用示例），用于展示典型输入、期望输出和正确/错误触发方式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Alarm latch reset example

## User prompt

“这段 FX3U 的 ST 报警逻辑为什么复位后下一扫又报警？帮我检查锁存条件、复位条件和是否有别的地方重新置位。”

## Expected skill behavior

- restate the symptom clearly
- separate facts from hypotheses
- inspect source condition, reset permissive, and re-latch risk
- mention scan-cycle and output/state ownership if relevant

## Why this example matters

This is a high-value troubleshooting example for real PLC maintenance work.
