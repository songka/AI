---
name: mq-process-surface
description: Estimate time, price, audit, and recommend review for surface treatment. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 表面处理报价

仅处理 `SURFACE`。依据明确的发黑、镀锌、阳极、喷涂、热处理等要求以及面积、重量或件数计价单位估算，检查单位匹配和最低收费。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.surface`、`skill_version=1.0.0`，结果写入 `step_results`。
