---
name: mq-material-classification
description: Normalize material grades while preserving source evidence and uncertainty. Use for the MATERIAL_CLASSIFICATION step in MechanicalQuotation V2.
---

# 材料判断

只执行 `MATERIAL_CLASSIFICATION`。优先采用图纸明确牌号，输出原文、规范牌号、材料大类、证据和置信度。

不得仅凭零件名称猜测材料；牌号冲突、热处理状态缺失或无法映射时标记人工确认。结果写入 `step_results.MATERIAL_CLASSIFICATION`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.material-classification`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
