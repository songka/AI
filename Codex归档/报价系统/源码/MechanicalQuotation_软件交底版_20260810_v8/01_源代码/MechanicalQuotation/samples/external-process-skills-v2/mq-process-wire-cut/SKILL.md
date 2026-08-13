---
name: mq-process-wire-cut
description: Estimate time, price, audit, and recommend review for fast wire cutting. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 快丝线切割报价

仅处理 `WIRE_CUT`。依据切割周长、厚度、穿丝孔、精度和切割次数估算单件工时；与慢丝不可重复。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.wire-cut`、`skill_version=1.0.0`，结果写入 `step_results`。
