<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/vendors/（厂商资料），记录具体 PLC 厂商的软件环境、术语、型号线索、指令规则或官方文档入口。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# GX Works2 Structured Project guidance

Use this file when the task concerns project organization, modular structure, or engineering layout in GX Works2 Structured Project.

## Intent

Prefer outputs that fit structured engineering rather than monolithic one-shot logic.

## Default organization mindset

- Separate sequence control, device conditioning, alarm handling, interlocks, and mode handling where practical.
- Prefer explicit module responsibilities.
- Keep main execution flow readable.
- Avoid scattering repeated logic in many places when a reusable pattern can be proposed.

## Review points

When reviewing or refactoring:

- Check whether responsibilities are separated cleanly.
- Check whether outputs are written in one clear place or risk being overwritten.
- Check whether states, transitions, and reset paths are understandable.
- Check whether alarm logic and interlock logic are explicit.
- Check whether device allocation reflects the role of the logic.

## Output preference

When generating solutions, prefer this order:

1. Program structure proposal
2. Variable or device allocation proposal
3. ST block or pseudocode
4. Explanation of scan behavior and module interaction
5. Debug and test checklist
