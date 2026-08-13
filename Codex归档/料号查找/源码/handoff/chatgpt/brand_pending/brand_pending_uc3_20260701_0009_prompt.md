请使用 external-part-brand-id 处理附件：
brand_pending_uc3_20260701_0009.csv

只做品牌识别，不要查官网图片。
输出文件名必须是：
brand_result_uc3_20260701_0009.csv

输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

正式批次规则：
- confidence 只能是 confirmed、suspected、unknown。
- evidence_url 必须是真实可访问的 http:// 或 https:// 网页 URL。
- confirmed 必须有真实网页证据支持品牌和型号/系列，不允许只根据原始表格品牌确认。
- 原始 brand_raw 可作为重要线索；如果只有原始表品牌、没有联网证据，应写 suspected，并在 note 说明“原始表有品牌，待官网核验”。
- 型号可能有 0/O、1/I/l、缺少连接符、型号不全等问题，必须保留 original_model 和 normalized_model。
- 不允许使用 source:、本地文件名、搜索词、空 URL 或假 URL 作为 evidence_url。
