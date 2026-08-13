# UC3 品牌识别校准报告

输入文件：

handoff/chatgpt/brand_pending/brand_pending_uc3_sample_20.csv

智能体返回文件：

handoff/chatgpt/brand_result/brand_result_uc3_sample_20.csv

## 结果概览

- 返回记录数：20
- confirmed：20
- suspected：0
- unknown：0

## 已通过项

- 能够识别标准 “品牌:” 字段，例如 台億、貝士德、士林、威斯康、台達、東力、精研、松下、三菱。
- 能够识别 description 末尾品牌，例如 PLC 擴展记录中的 松下。
- 输出为 CSV，便于 Codex 导入。
- 20 条记录数量正确。

## 未通过项

- 输出列名仍是旧版：part_no,name_or_type,model,brand,confidence,evidence_url,evidence_type,note。
- 缺少 original_model、normalized_model、model_issue 三个关键字段。
- evidence_url 为空，不符合 “每条必须有证据引用” 的导入要求。
- 文件命名没有按要求自动输出，需要人工改名为 brand_result_uc3_sample_20.csv。
- note 中说明 “未联网核验”，但 confidence 直接给 confirmed，语义容易混淆。校准阶段可以接受，但正式阶段必须区分原始品牌确认和官网核验。

## 调整规则

- 校准阶段 evidence_url 统一写 source:fnd_gfm.tsv，不能留空。
- 校准阶段原始品牌可记为 confirmed，但 evidence_type 必须明确为 raw_brand_field 或 description_tail_brand。
- 正式联网阶段，confirmed 必须有官网、PDF、产品页或可信页面证据 URL。
- 输出字段必须改为：

part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

## 结论

本轮智能体已经基本通过“品牌抽取能力”校准，但未通过“固定字段、证据占位、文件命名、型号容错字段”校准。

下一轮继续使用同一 20 条 UC3 样本，要求智能体按 v2 提示词重新输出 brand_result_uc3_sample_20.csv。通过后再进入批量品牌识别。
