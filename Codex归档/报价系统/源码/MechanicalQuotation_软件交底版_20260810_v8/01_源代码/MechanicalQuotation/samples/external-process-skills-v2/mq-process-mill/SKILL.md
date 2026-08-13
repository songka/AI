---
name: mq-process-mill
description: Estimate time, price, audit, and recommend review for milling. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 铣床加工报价

仅处理 `MILL`。结合面、槽、孔、型腔、装夹次数、公差和粗糙度估算单件工时，不与 CNC 自动重复计费。正式计价只引用价格表；按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.mill`、`skill_version=1.0.0`，结果写入 `step_results`。
