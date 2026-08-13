---
name: mq-unknown-estimation
description: Estimate unresolved quotation items as clearly labeled AI references that require review. Use for the UNKNOWN_ESTIMATION step in MechanicalQuotation V2.
---

# 待确认项 AI 估价

只执行 `UNKNOWN_ESTIMATION`，只处理没有正式价格的待确认费用行。

每个估价必须标记 `source=AI`、`price_status=AI_REFERENCE`、`requires_review=true`，并给出假设、范围、置信度和原因。不得覆盖已发布公司价格。结果写入 `step_results.UNKNOWN_ESTIMATION`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.unknown-estimation`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
