---
name: external-part-step-01-03-prepare-brand-batch
description: 外购件流水线第 1-3 步技能。用于将 tvs/fnd_gfm/系统物料表索引为结构化数据，筛选机械外购件和电控外购件，根据 assets.json 模式过滤目标料号，并导出 brand_pending 批次 CSV。
---

# 第 1-3 步：索引、筛选、导出品牌待查

执行前必须已经完成第 0 步，并且所有文件位于 Google Drive 项目文件夹。

## 第 1 步：原始表索引

输入：

- `tvs`、`fnd_gfm.tsv`、系统物料表或等价物料文件。

动作：

- 读取表头。
- 规范化料号、描述、分类、型号、品牌、库存等字段。
- 保留原始字段，不要过度推断。
- 编码不确定时优先按 UTF-8、GB18030、GBK 顺序尝试，并记录实际编码。

输出：

- `01_原始表索引/indexed_parts.jsonl`

## 第 2 步：筛选目标料号

输入：

- `01_原始表索引/indexed_parts.jsonl`
- 可选 `assets.json`
- `00_项目启动/run_config.json`

动作：

- 仅保留“机械外购件”和“电控外购件”。
- `asset_mode=skip_existing_assets` 时，过滤 `assets.json` 已覆盖料号。
- `asset_mode=update_existing_assets` 时，保留已有料号，用于补充或替换。
- 如果无法稳定判断 `assets.json` 中的料号匹配字段，停止并询问匹配规则。

输出：

- `02_目标料号筛选/target_parts.tsv`

## 第 3 步：导出品牌待查批次

输入：

- `02_目标料号筛选/target_parts.tsv`
- `05_品牌合并/brand_state.json`

动作：

- 只导出尚未完成品牌确认的记录。
- 每批 50-100 条；剩余不足一批时按实际数量导出。
- 批次编号稳定递增，如 `0001`、`0002`，不要覆盖历史批次。

输出：

- `03_品牌待查/brand_pending_0001.csv`

## 输出要求

所有输出必须保存到 Google Drive 项目文件夹。完成后说明下一步应使用 `external-part-step-04-05-brand-research-merge`。

## 断点续跑

如果恢复流程时发现以下文件已存在且结构有效，不要重复生成：

- `01_原始表索引/indexed_parts.jsonl`
- `02_目标料号筛选/target_parts.tsv`
- 已导出的 `03_品牌待查/brand_pending_*.csv`

继续时只导出尚未完成品牌确认的下一批记录，并更新 `00_项目启动/run_config.json`、`项目更新文档.md` 和 `项目进度.md`。
