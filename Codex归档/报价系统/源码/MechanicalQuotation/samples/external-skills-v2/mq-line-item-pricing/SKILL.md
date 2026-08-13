---
name: mq-line-item-pricing
description: Build auditable material, process, surface, and other quotation line items from approved price records. Use for the LINE_ITEM_PRICING step in MechanicalQuotation V2.
---

# 分项计价

只执行 `LINE_ITEM_PRICING`。按材料、加工、表面处理及其他费用逐项计算。

- 正式单价只能引用请求 `published_pricebook.records` 中已发布记录，并保留 `company_price_id`。
- 禁止使用图号、UC 料号或文件名匹配价格。
- 每行输出数量、单位、单价、未税金额、来源和证据；不得重复计费。
- 找不到正式价格时保留待确认项，不伪装为公司价格。结果写入 `step_results.LINE_ITEM_PRICING`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.line-item-pricing`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
