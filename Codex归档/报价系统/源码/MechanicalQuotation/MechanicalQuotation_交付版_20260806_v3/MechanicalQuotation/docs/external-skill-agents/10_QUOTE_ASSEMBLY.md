# 报价汇总 Skill 对接说明

步骤代码：`QUOTE_ASSEMBLY`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.QUOTE_ASSEMBLY` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：全部已校验分项、U/AI 参考项、税率、来源追踪、审核结论与价格版本。

提示词：正式未税小计只累计允许进入正式报价的项目；按请求税率计算税额和含税总价。U 与
AI_REFERENCE 单独展示，不计入正式金额。输出完整 `quotation`、中文摘要、来源追踪、待确认清单
和审核状态；不得用整件模型价覆盖材料、加工和表面处理分项。

返回字段：`quotation`、`formal_totals`、`reference_totals`、`source_trace`、`review_status`。

验收：逐项金额之和与正式小计一致；参考价与正式价严格分离；价格与规则版本可追溯。
