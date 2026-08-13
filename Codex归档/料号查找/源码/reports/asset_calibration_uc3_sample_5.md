# UC3 官网图片查找校准报告

输入文件：

`\\tsclient\D\Codex项目\料号检测系统\查询\asset_pending_uc3_sample_5.csv`

输出文件：

`\\tsclient\D\Codex项目\料号检测系统\查询\asset_result_uc3_sample_5.csv`

## 结论

本轮未完全通过第二阶段校准。

字段格式合格，但测试集切批、覆盖范围、多角度图片数量、直接图片链接质量不合格。

## 已通过

- 输出字段顺序正确：
  `part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note`
- 必填字段没有空值。
- 枚举值合法：
  - `angle`: front/catalog/connector/unknown
  - `image_source`: official/catalog/authorized_distributor
  - `product_url_confidence`: confirmed/suspected
  - `image_confidence`: confirmed/suspected
- 没有把淘宝/天猫误标为官方证据。
- 结果主要使用 official/catalog/authorized_distributor，来源质量总体可控。

## 未通过

- 输入文件名是 `asset_pending_uc3_sample_5.csv`，但实际包含 20 条记录。
- 输出只覆盖 5 个料号、10 行，未说明只处理前 5 条，导致输入/输出命名和覆盖范围不一致。
- 未覆盖输入中的 15 个料号。
- 每个料号只输出 2 行，未达到“每个料号优先 3-6 张图片”的要求。
- 角度覆盖不足，只有 `front/catalog/connector/unknown`，没有 `side/back/label`。
- 10 条输出中只有 1 条 `image_url` 是直接图片链接；其余多为产品页或 PDF 页面，不利于 Codex 自动下载图片。
- 多条记录的 `image_url` 与 `official_url` 相同，说明没有真正提取图片 URL。

## 调整建议

### 对输入切批

如果只测试 5 条，`asset_pending_uc3_sample_5.csv` 必须只包含 5 条记录。

如果输入包含 20 条，文件名应改为：

`asset_pending_uc3_sample_20.csv`

并要求智能体输出：

`asset_result_uc3_sample_20.csv`

### 对图片 Skill

补充规则：

- `image_url` 优先必须是直接图片链接，例如 `.jpg/.jpeg/.png/.webp`。
- 产品页 URL 只能放在 `official_url`。
- PDF URL 只有在作为目录证据时才能放在 `image_url`，并且必须设置 `angle=catalog`、`image_source=catalog`。
- 如果没有直接图片链接，应继续从中文官网、中文代理商、中文工业品平台、淘宝/天猫寻找多角度图片。
- 每个料号目标输出 3-6 张图片；如果少于 3 张，必须在 `note` 写明原因。
- 不能用同一个产品页 URL 充当多张图片。

## 下一轮测试标准

- 输入 5 条，输出只处理这 5 条。
- 每个料号至少 3 行，除非确实找不到并在 note 说明。
- 至少覆盖 `front` + `catalog` + `label/connector/side/back` 中的 3 类。
- 直接图片链接数量应明显增加。
- 淘宝/天猫可作为补充图片来源，但不能单独支撑 `product_url_confidence=confirmed`。
