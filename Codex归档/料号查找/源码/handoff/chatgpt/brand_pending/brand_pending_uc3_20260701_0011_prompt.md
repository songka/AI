请使用 external-part-brand-id 处理附件：
handoff/chatgpt/brand_pending/brand_pending_uc3_20260701_0011.csv

只做品牌识别，不要查官网图片。
输出文件名必须是：
handoff/chatgpt/brand_result/brand_result_uc3_20260701_0011.csv

输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

规则：
- confidence 只能是 confirmed、suspected、unknown。
- evidence_url 必须是真实可访问的 http/https 公开网页。
- confirmed 必须有真实网页证据支持品牌和型号/系列。
- 原始 brand_raw 只能作为线索，不能代替证据 URL。
- 不要使用 source:、搜索词、本地文件名或伪 URL。
- 找不到证据时保持 unknown 或不输出该行，等待后续最小 repair batch。
