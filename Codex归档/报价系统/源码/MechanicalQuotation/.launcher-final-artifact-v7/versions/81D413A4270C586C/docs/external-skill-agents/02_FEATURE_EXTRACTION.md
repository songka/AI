# 特征提取与零件分类 Skill 对接说明

步骤代码：`FEATURE_EXTRACTION`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；仅在请求选中时执行，并只在
`completed_steps` 与 `step_results.FEATURE_EXTRACTION` 返回结果。完整封包遵循
`../external-quotation-skill-protocol-v1.0.yaml`，标准提示词见 `../external-skill-prompt-templates-v1.0.yaml`。

输入：图纸原文、`built_in_context.manufacturing_features`、尺寸和已识别备注。先判断零件属于
加工件、钣金件、焊接件或型材组装件，再核对孔、螺纹、槽、轮廓、折弯、焊缝、装配、
表面区域及毛坯尺寸；不得用图号或文件名补特征或类别。

提示词：把结果分为“内置已确认、Skill 新增、来源冲突、无法确认”，每项返回类型、数量、尺寸、
来源证据和可信度；不计价、不决定正式工艺。

返回字段：`part_category`、`features`、`conflicts`、`missing_features`、`evidence`、`confidence`。

验收：圆形图框不得误算加工孔；备注中的“4-M8”应识别数量与螺纹，但不能自行推断孔深。
