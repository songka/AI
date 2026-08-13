请使用 external-part-official-image-finder 处理附件：
C:/Users/lfaf-test/Documents/料号查找/handoff/chatgpt/asset_pending/asset_pending_uc3_20260701_0004.csv

只做官网产品页和图片 URL 查找，不要重新做品牌识别。
输出文件名必须是：
C:/Users/lfaf-test/Documents/料号查找/handoff/chatgpt/asset_result/asset_result_uc3_20260701_0004.csv

输出 CSV，不要输出 Markdown 表格。CSV 字段必须严格为：
part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note

规则：
- 优先中文官网、中国官网、台湾官网、香港官网、中文 PDF。
- 中文资料不足时再查中文工业品平台和国际分销商。
- 淘宝/天猫只作人工补图参考，不作自动抓图来源，也不能作为 confirmed 的唯一来源。
- 每个料号尽量输出 3-6 张多角度图片，每张图片一行。
- image_url 优先使用可直接下载的 .jpg/.jpeg/.png/.webp。
- 产品页 URL 放 official_url，不要重复当作 image_url。
