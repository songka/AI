<!-- 中文导读开始 -->

## 中文导读

本文件属于 examples/（通用示例），用于展示典型输入、期望输出和正确/错误触发方式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Output overwrite debug example

## User prompt

“在线监控看起来启动条件已经满足，但输出就是一闪就没了，帮我判断是不是被后面的逻辑覆盖了。”

## Expected skill behavior

- identify this as a scan-cycle / ownership problem candidate
- ask for or infer the likely writer list
- prioritize output ownership analysis
- provide a concrete monitoring checklist

## Why this example matters

This is one of the most practical debugging situations in PLC work.
