---
name: mq-part-classification
description: Classify mechanical parts into the four supported quotation categories with evidence and confidence. Use for the PART_CLASSIFICATION step in MechanicalQuotation V2.
---

# 零件类别分类

只执行 `PART_CLASSIFICATION`。依据几何、材料、图纸备注和制造特征，从 `MACHINING`、`SHEET_METAL`、`WELDMENT`、`FRAME_ASSEMBLY` 四类中选择。

在 `step_results.PART_CLASSIFICATION` 返回 `part_category`、`category_name_zh`、`confidence`、`evidence` 和 `alternatives`。置信度低时仍给出最佳候选，但设置 `review.requires_review=true`。不要执行后续工艺或计价。

返回协议 JSON，复制请求 `request_id`；固定 `skill_id=sample.part-classification`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
