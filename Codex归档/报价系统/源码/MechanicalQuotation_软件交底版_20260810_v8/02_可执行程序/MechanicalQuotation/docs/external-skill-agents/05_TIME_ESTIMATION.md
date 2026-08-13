# 工时估算 Skill 对接说明

步骤代码：`TIME_ESTIMATION`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.TIME_ESTIMATION` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：工艺路线、设备、材料、数量、尺寸、特征、公差和已有工时。不得使用未确认工艺估算正式工时。

提示词：分别估算准备、装夹、加工、换刀/换序、检验和必要辅助工时；说明公式、数量、单位、批量
摊销及假设。对可替代设备分别给出工时，供系统结合已发布工价计算最低总成本。不得编造或修改
正式小时费率；信息不足时 `review_required=true`。

返回字段：`time_items`、`assumptions`、`calculation_evidence`、`review_required`、`confidence`。

验收：所有小时数非负且有依据；同一工序不得重复计算准备时间。
