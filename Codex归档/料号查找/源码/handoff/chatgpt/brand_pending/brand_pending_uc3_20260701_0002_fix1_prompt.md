请使用 external-part-brand-id 处理附件：
C:/Users/lfaf-test/Documents/料号查找/handoff/chatgpt/brand_pending/brand_pending_uc3_20260701_0002_fix1.csv

只做品牌识别，不要查官网图片。
输出文件名必须是：
C:/Users/lfaf-test/Documents/料号查找/handoff/chatgpt/brand_result/brand_result_uc3_20260701_0002_fix1.csv

输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

正式批次规则：
- 原始 brand_raw 可作为线索，但如果要写 confirmed，必须给真实公开网页证据 URL。
- evidence_url 必须是 http:// 或 https:// 真实网页，不允许 source:、搜索词、本地文件名或假 URL。
- 如果只有原始表品牌但没有联网证据，应写 suspected，并在 note 说明“原始表有品牌，待官网核验”。
- 如果找不到有用品牌，写 unknown；不要强行猜品牌。
- 型号可能有 0/O、1/I/l、缺少连接符、型号不全等问题，必须保留 original_model 和 normalized_model。
- UC3000050015/0016/0017/0019/0021 等 brand_raw 为“無/无”的行尤其不要编造品牌。
