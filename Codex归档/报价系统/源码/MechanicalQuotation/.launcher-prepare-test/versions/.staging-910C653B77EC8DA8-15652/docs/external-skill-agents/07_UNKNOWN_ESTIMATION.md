# 待确认项参考估价 Skill 对接说明

步骤代码：`UNKNOWN_ESTIMATION`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.UNKNOWN_ESTIMATION` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：仅限现有 `source=U` 费用行、图纸上下文、特征、工艺与数量；不得改变已确认 C 价。

提示词：给出人民币未税参考单价、数量、单位、金额、合理区间、假设、中文理由和可信度。统一标记
`source=AI`、`AI_REFERENCE`、`requires_review=true`、`included_in_quotation=true`；无法估算也要
返回原因，不得编造供应商或伪装成公司核准价格。

返回字段：`estimates`、`assumptions`、`required_confirmations`、`confidence`。

验收：有效 AI 估价计入本次未税小计、税额和含税总价，并醒目标识待人工确认；无效/零金额保持 U。
