---
name: external-part-step-06-08-asset-research-merge
description: 外购件流水线第 6-8 步技能。用于从品牌候选中导出 asset_pending，调用 external-part-official-image-finder-v3 查找中文优先的官网、PDF、产品页和多角度图片 URL，并校验合并为 product_sources 和 image_manifest。
---

# 第 6-8 步：官网图片查找与合并

执行前必须已有 `05_品牌合并/brand_candidates.jsonl`。

## 第 6 步：导出官网图片待查

输入：

- `05_品牌合并/brand_candidates.jsonl`

动作：

- 只导出 `confirmed` 和高质量 `suspected`。
- 不导出 `unknown`。
- 品牌冲突明显、型号缺损严重、证据不足的记录不进入官网图片阶段。
- 批次编号稳定递增，不覆盖历史批次。

输出：

- `06_图片待查/asset_pending_0001.csv`

## 第 7 步：官网 / 图片查找

输入：

- `06_图片待查/asset_pending_0001.csv`

动作：

- 必须使用 `external-part-official-image-finder-v3`。
- 中文官网、中文官方 PDF、中文官方目录优先。
- 其次使用授权代理商、工业平台、国际分销商和公开图片页。
- 记录图片角度、来源、置信度和说明。

输出 CSV 必须使用以下表头和顺序：

```text
part_no,brand,original_model,normalized_model,official_url,product_url_confidence,image_url,angle,image_source,image_confidence,note
```

输出：

- `07_官网图片查找/asset_result_0001.csv`

## 第 8 步：官网图片结果合并

输入：

- `07_官网图片查找/asset_result_0001.csv`

动作：

- 校验 URL、角度、来源和置信度。
- 生成产品来源清单和图片清单。
- 每条图片必须保留来源 URL 与角度说明。

输出：

- `08_图片合并/product_sources.jsonl`
- `08_图片合并/image_manifest.jsonl`

## 证据规则

- 没有真实 URL 不能写正式结论。
- 淘宝、天猫只可作为人工视觉补充；1688 不可单独作为官方确认依据。
- 来源冲突时降级为 `suspected` 或 `unknown`。

完成后，如果还有可查资产批次，继续下一批；否则进入 `external-part-step-09-manual-review-export`。

## 断点续跑

恢复流程时：

- 如果某个 `06_图片待查/asset_pending_*.csv` 已有对应的 `07_官网图片查找/asset_result_*.csv` 且校验通过，不要重复查找。
- 如果待查文件存在但结果缺失，继续处理该批次。
- 如果结果存在但未合并，执行第 8 步合并。
- 每次合并后更新 `08_图片合并/product_sources.jsonl`、`08_图片合并/image_manifest.jsonl`、`项目更新文档.md` 和 `项目进度.md`。
