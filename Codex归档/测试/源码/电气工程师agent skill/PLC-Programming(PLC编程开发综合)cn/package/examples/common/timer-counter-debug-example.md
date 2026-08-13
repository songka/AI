<!-- 中文导读开始 -->

## 中文导读

本文件属于 examples/（通用示例），用于展示典型输入、期望输出和正确/错误触发方式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Timer counter debug example

## User prompt

“这段 GX Works2 里的 ST 逻辑为什么定时器一直不到位，或者计数器一直不到目标值？帮我分析可能是使能条件、复位路径还是写法问题。”

## Expected skill behavior

- inspect enable condition first
- inspect reset path second
- inspect done-dependent transition logic third
- avoid assuming the timer or counter itself is faulty

## Why this example matters

This reinforces correct troubleshooting order for FX3U logic.
