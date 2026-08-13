---
name: external-part-step-04-05-brand-research-merge
description: 外购件流水线第 4-5 步技能。用于读取 brand_pending 批次，调用 external-part-brand-id 完成品牌识别、证据 URL 收集、confirmed/suspected/unknown 分类，并校验合并 brand_result 到品牌候选和状态文件。
---

# 第 4-5 步：品牌识别与合并

执行前必须已有 `03_品牌待查/brand_pending_*.csv`。

## 第 4 步：批量品牌识别

输入：

- `03_品牌待查/brand_pending_0001.csv`

动作：

- 必须使用 `external-part-brand-id`。
- 对品牌、型号、别名、缩写、录入错误和缺损型号做容错识别。
- 必要时使用 Web search 补充证据。
- 每条结论都必须有证据来源。

输出 CSV 必须使用以下表头和顺序：

```text
part_no,name_or_type,original_model,normalized_model,brand,confidence,evidence_url,evidence_type,model_issue,note
```

允许的 `confidence`：

- `confirmed`
- `suspected`
- `unknown`

输出：

- `04_品牌识别/brand_result_0001.csv`

## 第 5 步：品牌结果合并

输入：

- `04_品牌识别/brand_result_0001.csv`

动作：

- 校验 CSV 表头、枚举值、证据 URL。
- `confirmed` 必须有真实公开证据 URL，不能只有本地文件。
- 合并品牌候选结果。
- 保留证据来源、候选品牌、置信度、型号问题和备注。
- 更新品牌处理状态。

输出：

- `05_品牌合并/brand_candidates.jsonl`
- `05_品牌合并/brand_state.json`

## 证据规则

- 没有证据不能写 `confirmed`。
- 来源冲突时降级为 `suspected` 或 `unknown`。
- 淘宝、天猫、1688 不能作为品牌官方确认的唯一依据。

完成后，如果还有品牌待查记录，继续下一批；否则进入 `external-part-step-06-08-asset-research-merge`。

## 断点续跑

恢复流程时：

- 如果某个 `03_品牌待查/brand_pending_*.csv` 已有对应的 `04_品牌识别/brand_result_*.csv` 且校验通过，不要重复识别。
- 如果待查文件存在但结果缺失，继续处理该批次。
- 如果结果存在但未合并，执行第 5 步合并。
- 每次合并后更新 `05_品牌合并/brand_candidates.jsonl`、`05_品牌合并/brand_state.json`、`项目更新文档.md` 和 `项目进度.md`。
