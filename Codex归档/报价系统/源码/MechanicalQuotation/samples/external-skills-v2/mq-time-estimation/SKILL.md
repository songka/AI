---
name: mq-time-estimation
description: Estimate bounded per-piece manufacturing time by concrete process using drawing evidence. Use for the TIME_ESTIMATION step in MechanicalQuotation V2.
---

# 工时估算

只执行 `TIME_ESTIMATION`，并只处理请求 `selected_processes` 指定的具体工艺。

- 工时按图纸的“一件”估算，不按材料重量 kg 当作件数。
- 分解准备、装夹、加工、换刀和检验时间，输出合计与证据。
- 使用 `references/time-factors.json` 的软上限做异常检查；超过上限时降低置信度并要求人工复核，不静默截断。
- 不修改公司核准的小时单价。结果写入 `step_results.TIME_ESTIMATION`。

返回协议 JSON，复制 `request_id`；固定 `skill_id=sample.time-estimation`、`skill_version=1.0.0`、`protocol_version=1.0`，不得返回 Markdown。
