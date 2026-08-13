请使用 external-part-brand-id 处理附件：
handoff/chatgpt/brand_pending/brand_pending_uc3_20260701_0014.csv

只做品牌识别，不要查官网图片。
输出文件名必须是：handoff/chatgpt/brand_result/brand_result_uc3_20260701_0014.csv
输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

本批次 50 行当前都是 brand_raw=紐立得，型号多为 PPC/PPL/PPY/PPW 等气管接头。请主动查找“紐立得/纽立得/Newlited”等公开网页、官网、产品目录或可信工业品页面证据。
规则：
- evidence_url 必须是真实 http/https URL，不能用本地文件、source:、搜索词或假 URL。
- confirmed 必须有网页证据能支持品牌和型号/系列。
- 如果只能证明品牌但找不到型号页，写 suspected，并在 note 说明“品牌有公开网页，型号待确认”。
- 如果找不到任何公开证据，写 unknown，但 evidence_url 仍需填可解释不确定性的真实公开网页；找不到就不要编造。
- original_model 保留原始型号，normalized_model 只做明显清洗，不要改变含义。
