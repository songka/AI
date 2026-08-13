---
name: mq-process-planning
description: Plan evidence-based multi-process manufacturing routes across supported machining and fabrication processes. Use for the PROCESS_PLANNING step in MechanicalQuotation V2.
---

# 工艺路线规划

只执行 `PROCESS_PLANNING`。根据类别和特征选择必要工艺，可使用 CNC、车床、铣床、磨床、钳工、放电、快丝、慢丝、激光切割、折弯、焊接和表面处理。

- 不得默认所有零件都是 CNC 或铣床。
- 多工艺零件输出有顺序的 `processes`，每项包含 `code`、`process_name`、`reason`、`confidence`。
- 只规划工艺，不生成正式单价。结果写入 `step_results.PROCESS_PLANNING`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.process-planning`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
