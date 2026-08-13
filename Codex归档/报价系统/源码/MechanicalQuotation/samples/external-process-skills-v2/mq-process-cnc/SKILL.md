---
name: mq-process-cnc
description: Estimate time, price, audit, and recommend review for CNC machining. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# CNC 加工报价

仅处理 `selected_processes` 中的 `CNC` 以及请求选中的步骤。工时按单件拆分准备、装夹、加工、换刀和检验；计价只能引用已发布价格；审核检查工时、重复费用与来源；建议必须可执行。不得把 kg 当件数。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.cnc`、`skill_version=1.0.0`，结果按步骤写入 `step_results`，不得返回未选择步骤。
