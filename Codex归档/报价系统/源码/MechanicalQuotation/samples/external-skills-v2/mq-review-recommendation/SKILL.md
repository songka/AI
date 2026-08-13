---
name: mq-review-recommendation
description: Turn quotation evidence gaps and audit findings into a concise actionable manual review checklist. Use for the REVIEW_RECOMMENDATION step in MechanicalQuotation V2.
---

# 人工审核建议

只执行 `REVIEW_RECOMMENDATION`，综合前序 Skill 结果、AI 参考项、警告和价格审核结论。

输出 `requires_review`、`warnings` 和按优先级排序的 `review_items`；每项说明字段、原因、证据与建议动作。不要修改报价或自行批准。结果写入 `step_results.REVIEW_RECOMMENDATION`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.review-recommendation`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
