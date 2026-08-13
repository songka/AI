---
name: mq-quote-assembly
description: Assemble validated quote lines into untaxed subtotal, tax, and total without duplicate charges. Use for the QUOTE_ASSEMBLY step in MechanicalQuotation V2.
---

# 报价汇总

只执行 `QUOTE_ASSEMBLY`。汇总已有正式费用行，计算未税小计、税额和含税总价。

检查重复行、单位和 Decimal 精度；整件模型参考价只作审核参考，不计入正式合计。结果写入 `step_results.QUOTE_ASSEMBLY`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.quote-assembly`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
