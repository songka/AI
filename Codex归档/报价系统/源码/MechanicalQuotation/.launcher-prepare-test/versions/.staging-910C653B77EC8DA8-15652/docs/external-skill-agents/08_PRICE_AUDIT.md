# 价格审核 Skill 对接说明

步骤代码：`PRICE_AUDIT`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.PRICE_AUDIT` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：图纸备注、工艺、工时、所有报价分项、正式价格表和来源追踪。

提示词：检查漏项、重复计费、数量/单位异常、设备等级过高、工时异常、价格过期，以及所有 C 价的
ID 和单价一致性。只能提出问题与建议，不得直接改价或批准价格。

返回字段：`verdict`（PASS/REVIEW/BLOCK）、`issues`、`duplicate_checks`、
`price_source_checks`、`actions`、`confidence`。

验收：铣床足够却使用 CNC、相同加工重复计费、C 价 ID 不存在时必须至少 REVIEW。
