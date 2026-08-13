<!-- 中文导读开始 -->

## 中文导读

本文件属于 references/common/（通用 PLC 资料），记录跨厂商通用的 PLC 工程规则、检查清单、调试方法或输出格式。

> 说明：为方便课堂解读，本文件保留原英文/原技术内容，并在前面加入中文说明；文件名、路径、代码块和引用关系不变，可继续直接导入使用。

<!-- 中文导读结束 -->

# Output format rules

Choose the format based on task type.

## 1. Code generation format

Use for new logic design or program drafting.

1. Requirement understanding
2. Known conditions
3. Assumptions
4. Program structure proposal
5. Variable / device allocation suggestion
6. ST code or pseudocode
7. Logic explanation
8. Risks and cautions
9. Debug / test checklist

## 2. Code explanation format

Use when explaining existing ST or device-based logic.

1. What the code is doing
2. Confirmed facts
3. Assumptions
4. Execution / scan-cycle interpretation
5. Potential weak points
6. Suggested validation points

## 3. Review / refactor format

Use for code quality improvement.

1. Overall assessment
2. Main issues
3. Why each issue matters
4. Suggested refactoring direction
5. Revised structure or sample rewrite
6. Validation checklist

## 4. Debug / troubleshoot format

Use for abnormal behavior analysis.

1. Symptom
2. Known facts
3. Assumptions
4. Most likely failure paths
5. Step-by-step debug plan
6. Safe verification steps
7. Likely corrections

## Formatting rules

- Prefer sections over long paragraphs
- Prefer explicit labels for uncertainty
- Prefer modular proposals before large code dumps
- Prefer checklist endings for engineering tasks
