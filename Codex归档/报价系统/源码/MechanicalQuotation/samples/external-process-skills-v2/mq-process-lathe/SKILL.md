---
name: mq-process-lathe
description: Estimate time, price, audit, and recommend review for lathe turning. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 车床加工报价

仅处理 `LATHE`。结合回转体、直径长度、台阶、槽、螺纹、精度和批量估算单件车削工时；正式计价只引用价格表。按请求选择执行工时、计价、审核或人工建议。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.lathe`、`skill_version=1.0.0`，结果写入 `step_results`。
