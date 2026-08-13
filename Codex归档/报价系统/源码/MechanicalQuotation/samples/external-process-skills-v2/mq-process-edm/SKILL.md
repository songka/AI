---
name: mq-process-edm
description: Estimate time, price, audit, and recommend review for EDM machining. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 放电加工报价

仅处理 `EDM`。依据深窄型腔、尖角、硬料和电极需求估算电极准备、放电与检验工时；无证据不得添加放电。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.edm`、`skill_version=1.0.0`，结果写入 `step_results`。
