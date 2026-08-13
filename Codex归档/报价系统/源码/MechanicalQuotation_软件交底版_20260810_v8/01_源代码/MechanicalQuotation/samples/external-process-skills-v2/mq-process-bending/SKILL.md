---
name: mq-process-bending
description: Estimate time, price, audit, and recommend review for sheet metal bending. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 折弯加工报价

仅处理 `BENDING`。依据板厚、材质、折弯次数、长度、角度、公差和换模次数估算单件工时；无折弯特征不得添加。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.bending`、`skill_version=1.0.0`，结果写入 `step_results`。
