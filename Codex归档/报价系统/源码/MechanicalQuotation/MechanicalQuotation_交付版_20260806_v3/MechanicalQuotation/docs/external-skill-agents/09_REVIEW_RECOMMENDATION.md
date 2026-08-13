# 人工审核建议 Skill 对接说明

步骤代码：`REVIEW_RECOMMENDATION`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.REVIEW_RECOMMENDATION` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：备注冲突、低可信特征、AI 工艺、U/AI 参考价、价格审核问题和现有审核状态。

提示词：按风险排序生成可执行的中文确认清单，写明需确认资料、建议审核角色、阻断条件和通过条件；
不得代替人工批准，也不得把建议写成正式价格。

返回字段：`risk_level`、`review_items`、`blocking_items`、`suggested_reviewers`、`confidence`。

验收：材料冲突、正式价缺失和关键工艺不确定必须列为阻断或高优先审核项。
