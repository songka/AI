# 图纸与备注理解 Skill 对接说明

步骤代码：`DOCUMENT_UNDERSTANDING`

共通对接：在 `skill.json` 的 `supported_steps` 声明本步骤；请求的 `selected_steps` 包含本步骤时才执行，
并只在 `completed_steps` 与 `step_results.DOCUMENT_UNDERSTANDING` 返回结果。完整封包、错误与追踪字段
遵循 `../external-quotation-skill-protocol-v1.0.yaml`；标准提示词见
`../external-skill-prompt-templates-v1.0.yaml`。

输入：`drawing_package.extracted_texts` 原文与来源、`built_in_context.note_inputs` 来源类型、已有
`note_understanding`。优先级为原生 DWG/DXF/SolidWorks 图纸文字、内置推断。
必须区分标题栏、材料栏、技术要求、局部引线及全局备注；保留原文，冲突不得静默覆盖。

提示词：提取材料、规格、厚度、数量、公差、粗糙度、热处理、表面处理和特殊要求；不计价、不选
设备、不猜测。每条结论返回原文、source_file_id、来源类型、可信度；OCR 冲突必须转人工审核。

返回字段：`step_results.DOCUMENT_UNDERSTANDING` 必须包含 `summary_zh`、`requirements`、`ambiguities`、
`evidence`、`confidence`。缺少材料或要求冲突时 `review.requires_human_review=true`。

验收：同一要求在 DXF 与 OCR 冲突时保留两条证据并选择高可信原生文字；不得按文件名推断备注。
