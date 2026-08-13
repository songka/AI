请使用 external-part-brand-id 处理附件：

C:/Users/lfaf-test/Documents/料号查找/handoff/chatgpt/brand_pending/brand_pending_uc3_20260701_0010.csv

只做品牌识别，不要查官网图片。

输出文件名必须是：

C:/Users/lfaf-test/Documents/料号查找/handoff/chatgpt/brand_result/brand_result_uc3_20260701_0010.csv

输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：

part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

规则：
- confidence 只能是 confirmed、suspected、unknown。
- evidence_url 必须是真实公开的 http/https URL，不能是 source:、搜索词、本地文件名或假 URL。
- confirmed 必须有网页证据支持品牌和型号/系列。
- 只有品牌官网但没有型号证据时，用 suspected，并在 note 说明 exact model not verified。
- 找不到公开证据时保持 unknown 或不要纳入导入结果，不要编造 URL。
- 保留 original_model；normalized_model 只做必要的型号清洗。
