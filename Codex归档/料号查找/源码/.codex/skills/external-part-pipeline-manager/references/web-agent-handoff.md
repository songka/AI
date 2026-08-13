# Web Agent Handoff

Use these instructions when preparing files for ChatGPT Web.

## Brand Batch Prompt

```text
请使用 external-part-brand-id 处理附件：

{brand_pending_file}

只做品牌识别，不要查官网图片。

输出文件名必须是：{brand_result_file}
输出 CSV，不要输出 Markdown 表格。
CSV 字段必须严格为：
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note

正式批次规则：
- 原始 brand_raw 可作为重要线索，但如果要写 confirmed，必须给真实证据 URL。
- 如果只有原始表品牌、还没有联网证据，应写 suspected，并在 note 说明“原始表有品牌，待官网核验”。
- 型号可能有 0/O、1/I/l、缺少连接符、型号不全等问题，必须保留 original_model 和 normalized_model。
- 不允许留空 evidence_url。
- 不允许无证据确认品牌。
```

## Asset Batch Prompt

```text
请使用 external-part-official-image-finder 处理附件：

{asset_pending_file}

只做官网产品页和图片 URL 查找，不要重新做品牌识别。

输出文件名必须是：{asset_result_file}
输出 CSV，不要输出 Markdown 表格。
CSV 字段必须严格为：
part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note

规则：
- 优先中文官网、中国官网、台湾官网、香港官网、中文 PDF。
- 中文资料不足时再查中文工业品平台和国际分销商。
- 淘宝/天猫只作为人工补图参考，不作为自动抓图来源。
- 每个料号尽量输出 3-6 张多角度图片，每张图片一行。
- image_url 优先使用可直接下载的 .jpg/.jpeg/.png/.webp。
- 产品页 URL 放 official_url，不要重复当作 image_url。
```
