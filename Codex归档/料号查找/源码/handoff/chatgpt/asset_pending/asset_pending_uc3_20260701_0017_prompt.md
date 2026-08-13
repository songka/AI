请使用 external-part-official-image-finder 处理附件：
handoff/chatgpt/asset_pending/asset_pending_uc3_20260701_0017.csv

只做官网产品页和图片 URL 查找，不要重新做品牌识别。
输出文件名必须是：
handoff/chatgpt/asset_result/asset_result_uc3_20260701_0017.csv

输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：
part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note

规则：
- 优先使用基恩士中国官网或 KEYENCE 官方页面。
- `UC3040020012 / GL-S40FH` 已有可核验官方产品页：https://www.keyence.com/products/safety/light-curtain/gl-s/models/gl-s40fh/
- image_url 优先使用可直接下载的 .jpg/.jpeg/.png/.webp。
- 不要把产品页面 URL 重复当作 image_url。
- Taobao/Tmall 只能作为人工补图参考，不能作为 confirmed 的唯一来源。
