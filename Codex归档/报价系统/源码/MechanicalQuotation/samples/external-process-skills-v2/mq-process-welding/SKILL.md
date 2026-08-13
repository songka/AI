---
name: mq-process-welding
description: Estimate time, price, audit, and recommend review for welding. Use for process-routed TIME_ESTIMATION, LINE_ITEM_PRICING, PRICE_AUDIT, or REVIEW_RECOMMENDATION steps.
---

# 焊接加工报价

仅处理 `WELDING`。依据焊缝类型、长度、板厚、焊接方法、装配定位、变形控制和检验要求估算，不凭“组件”名称自动添加焊接。按请求执行第 6、7、10、11 步。

返回协议 JSON，复制 `request_id`，固定 `skill_id=sample.process.welding`、`skill_version=1.0.0`，结果写入 `step_results`。
