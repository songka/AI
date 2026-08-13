---
name: mq-document-understanding
description: Understand mechanical drawing notes and extract structured requirements, risks, quantities, and evidence. Use for the DOCUMENT_UNDERSTANDING step in MechanicalQuotation V2.
---

# 图纸与备注理解

只执行请求 `selected_steps` 中的 `DOCUMENT_UNDERSTANDING`。

- 从 `drawing_package.extracted_texts` 和 `built_in_context.note_inputs` 提取摘要、要求、风险和置信度。
- 严格区分“1件”、材料重量 kg、尺寸 mm 和工时 hour；不得把 1kg 当成 1 件。
- 保留来源文件与原文证据。资料不足时输出待确认项，不臆造。
- 将结果放入 `step_results.DOCUMENT_UNDERSTANDING`。

返回 JSON：复制请求的 `request_id`，使用 `protocol_version=1.0`、`skill_id=sample.document-understanding`、`skill_version=1.0.0`，并提供 `status`、`completed_steps`、`step_results`、`warnings_zh`、`review` 和 `trace`。不得返回 Markdown。
