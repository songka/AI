# 料号资料流水线运行清单

## 1. 索引原始 TSV

命令：

```powershell
python scripts\index_fnd_gfm.py
```

输入：

- `fnd_gfm.tsv`

输出：

- `data/indexed_parts.jsonl`
- `data/target_parts.jsonl`
- `data/target_parts.tsv`
- `reports/index_report.md`

## 2. 导出品牌识别批次

命令：

```powershell
python scripts\export_brand_batch.py --prefix UC3 --limit 50 --batch-id uc3_0001
```

输出：

- `handoff/chatgpt/brand_pending/brand_pending_uc3_0001.csv`

交给 ChatGPT 网页智能体：

- 使用 `external-part-brand-id`
- 输出 `brand_result_uc3_0001.csv`

## 3. 导入品牌识别结果

命令：

```powershell
python scripts\import_brand_result.py handoff\chatgpt\brand_result\brand_result_uc3_0001.csv
```

输出：

- `data/brand_candidates.jsonl`
- `reports/brand_import_brand_result_uc3_0001.md`

## 4. 导出官网图片查找批次

命令：

```powershell
python scripts\export_asset_batch.py --limit 20 --batch-id uc3_0001
```

输出：

- `handoff/chatgpt/asset_pending/asset_pending_uc3_0001.csv`

交给 ChatGPT 网页智能体：

- 使用 `external-part-official-image-finder`
- 输出 `asset_result_uc3_0001.csv`

## 5. 导入官网图片结果

命令：

```powershell
python scripts\import_asset_result.py handoff\chatgpt\asset_result\asset_result_uc3_0001.csv
```

输出：

- `data/image_manifest.jsonl`
- `reports/asset_import_asset_result_uc3_0001.md`

## 当前状态

已完成：

- 索引 `fnd_gfm.tsv`
- 导出 `brand_pending_uc3_0001.csv`

等待：

- ChatGPT 网页智能体返回 `brand_result_uc3_0001.csv`
