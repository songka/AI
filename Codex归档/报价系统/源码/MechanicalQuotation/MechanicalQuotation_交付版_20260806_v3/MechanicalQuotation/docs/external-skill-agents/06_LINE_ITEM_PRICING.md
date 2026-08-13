# 分项计价 Skill 对接说明

步骤代码：`LINE_ITEM_PRICING`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.LINE_ITEM_PRICING` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：材料用量、工艺与工时、表面处理、数量、`published_pricebook` 和既有费用行。

提示词：按材料、加工、表面处理、外购、装配和其他费用分项。正式 `source=C` 必须引用输入中的
`company_price_id/price_version_id`，单价完全一致，`amount=quantity×unit_price`。无正式价返回 U，
可附 AI_REFERENCE，但不得进入正式合计。不得用整件参考价覆盖分项。

返回字段：`quote_items`、`unknown_items`、`ai_references`、`evidence`、`confidence`。

验收：伪造、过期或单价不一致的公司价格必须被主系统拒绝。
