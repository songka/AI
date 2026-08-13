# 给 ChatGPT Web 智能体的修正说明

请使用 `external-part-brand-id` 只处理附件：
`brand_pending_uc3_20260701_0001_fix2.csv`

这是 `brand_result_uc3_20260701_0001.csv` 的 2 行修正批次。原结果中这两行的 `evidence_url` 写成了 `source:...`，不能通过本地导入校验。

只做品牌识别，不要查官网图片。

输出文件名必须是：
`brand_result_uc3_20260701_0001_fix2.csv`

输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：

```text
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note
```

修正规则：

- `evidence_url` 必须是 `http://` 或 `https://` 开头的公开可核验网页 URL。
- 不允许再使用 `source:...`、本地文件名、搜索词、备注文字作为 `evidence_url`。
- 如果找不到型号页，可以使用品牌官网、品牌产品分类页、公开样本/PDF 或可信工业品平台页面作为 `evidence_url`，但 `confidence` 应保持 `suspected`。
- 如果要写 `confirmed`，必须有能支撑品牌和型号/系列的真实证据 URL。

处理完成后，把 `brand_result_uc3_20260701_0001_fix2.csv` 放回：
`handoff/chatgpt/brand_result/`
