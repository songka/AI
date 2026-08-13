# 材料判断 Skill 对接说明

步骤代码：`MATERIAL_CLASSIFICATION`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.MATERIAL_CLASSIFICATION` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：材料栏、标题栏、技术要求原文、几何尺寸和内置材料候选。只依据用户文档和明确特征判断。

提示词：输出标准材料代码、中文名称、材料形态、厚度/规格、证据、假设和可信度。牌号冲突或仅写
“不锈钢/铝”时保留待确认；禁止使用 UC、图号、零件号、文件名或历史价格反推材料。

返回字段：`material_code`、`material_name_zh`、`specification`、`assumptions`、`evidence`、
`confidence`。

验收：`3mm SUS304` 可确认；仅写“不锈钢”不得擅自变成 304。
