---
name: mq-process-slow-wire
description: Estimate time, price, audit, and recommend review for slow wire EDM. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 慢丝加工报价

仅处理 `SLOW_WIRE`。依据高精度、低粗糙度、锥度、切割周长、厚度和多次修刀要求估算；无精度证据时提示复核慢丝必要性。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.slow-wire`、`skill_version=1.0.0`，结果写入 `step_results`。
