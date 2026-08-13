<!-- 中文导读开始 -->

## 中文导读

本文件属于 examples/（通用示例），用于展示典型输入、期望输出和正确/错误触发方式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Motor start-stop example

## User prompt

“帮我写一个 FX3U 在 GX Works2 Structured Project 里的 ST 电机启停逻辑，带自动模式、停止命令、故障联锁和复位思路。”

## Expected skill behavior

- confirm known conditions and assumptions
- propose structure before code
- separate run request, permissive, fault inhibit, and reset logic
- prefer a reusable pattern rather than one-off code

## Why this example matters

This is a common first-step generation task and should strongly trigger the skill.
