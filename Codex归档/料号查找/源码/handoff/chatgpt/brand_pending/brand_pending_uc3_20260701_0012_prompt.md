请使用 external-part-brand-id 处理附件：
brand_pending_uc3_20260701_0012.csv

只做品牌识别，不要查官网图片。
输出文件名必须是：
brand_result_uc3_20260701_0012.csv

输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

规则：
- 原始 brand_raw 可作为线索，但 confirmed 必须给真实公开 http/https 证据 URL。
- confidence 只能是 confirmed、suspected、unknown。
- evidence_url 必须是 http/https，不允许 source:、搜索词、本地文件名或假 URL。
- 没有公开证据时不要 confirmed；可以 suspected 并说明“原始表有品牌，待官网核验”。
- 型号可能有 0/O、1/I/l、缺少连字符、型号不完整等问题，保留 original_model 和 normalized_model。
- 不要把 Taobao/Tmall 当作 confirmed 的唯一证据。
