<!-- 中文导读开始 -->

## 中文导读

本文件属于 examples/（通用示例），用于展示典型输入、期望输出和正确/错误触发方式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Sequence state machine example

## User prompt

“根据这个工艺步骤帮我设计一个 FX3U 的 ST 状态机，要求结构适合 GX Works2 Structured Project，后续容易调试。”

## Expected skill behavior

- recommend step/state structure explicitly
- show state ownership and transition conditions
- keep fault and reset branches visible
- avoid giant flat condition chains

## Why this example matters

This is a core generation/refactoring scenario for the current scope.
