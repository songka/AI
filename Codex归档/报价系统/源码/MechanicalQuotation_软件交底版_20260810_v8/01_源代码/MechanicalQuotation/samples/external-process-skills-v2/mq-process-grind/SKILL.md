---
name: mq-process-grind
description: Estimate time, price, audit, and recommend review for grinding. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 磨床加工报价

仅处理 `GRIND`。仅在精度、平面度、圆度、粗糙度或热处理后精加工证据支持时计入磨削，估算准备、找正、磨削和检验工时。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.grind`、`skill_version=1.0.0`，结果写入 `step_results`。
