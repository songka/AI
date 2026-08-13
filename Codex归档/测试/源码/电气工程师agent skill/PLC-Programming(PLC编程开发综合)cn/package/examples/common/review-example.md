<!-- 中文导读开始 -->

## 中文导读

本文件属于 examples/（通用示例），用于展示典型输入、期望输出和正确/错误触发方式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Review example

## Input style

User provides a block of ST code from a GX Works2 Structured Project and asks for maintainability review.

## Expected behavior

The skill should:
- assess structure first
- identify output ownership conflicts
- point out hidden state dependencies
- recommend refactoring direction
- avoid rewriting everything unless necessary

## Preferred output shape

1. overall assessment
2. key findings
3. impact
4. suggested restructuring
5. partial rewrite if useful
6. validation checklist
