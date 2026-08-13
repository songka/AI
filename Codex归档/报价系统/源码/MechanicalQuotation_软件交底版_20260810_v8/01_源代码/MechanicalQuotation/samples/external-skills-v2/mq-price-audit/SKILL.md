---
name: mq-price-audit
description: Audit quantity, weight, process hours, price sources, duplicate fees, and totals with executable recalculation actions. Use for the PRICE_AUDIT step in MechanicalQuotation V2.
---

# 价格审核

只执行 `PRICE_AUDIT`，可按请求中的具体工艺分别审核。

- 检查件数与 kg 是否混淆、重量计算、工时异常、重复计费、正式价格引用和合计。
- 输出 `verdict`、`issues`、`actions`、`confidence`。
- `actions` 必须明确受影响步骤和重算内容，例如重新执行 `TIME_ESTIMATION`，不能只写“请检查”。
- 有实质风险时设置 `review.requires_review=true`。结果写入 `step_results.PRICE_AUDIT`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.price-audit`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
