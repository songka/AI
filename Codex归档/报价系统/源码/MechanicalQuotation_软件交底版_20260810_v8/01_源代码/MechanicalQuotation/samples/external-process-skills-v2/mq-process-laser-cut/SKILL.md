---
name: mq-process-laser-cut
description: Estimate time, price, audit, and recommend review for laser cutting. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 激光切割报价

仅处理 `LASER_CUT`。依据板厚、材质、切割长度、穿孔数、轮廓复杂度和排样利用率估算，材料重量与件数分别处理。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.laser-cut`、`skill_version=1.0.0`，结果写入 `step_results`。
