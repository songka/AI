---
name: mq-process-fitter
description: Estimate time, price, audit, and recommend review for fitter work. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 钳工作业报价

仅处理 `FITTER`。依据去毛刺、攻牙、修配、抛光、装配和手工检验等明确需求估算单件工时，避免与机加工已含工序重复。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.fitter`、`skill_version=1.0.0`，结果写入 `step_results`。
