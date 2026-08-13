# 機構2D自動報價系統 — 回歸測試設計

日期：2026-08-01
版本：V1.0

---

## 一、定位

Phase 2.4 不測試最終報價誤差（CAD Feature Extractor 和 Rule Engine 尚未完成）。

本階段目標：

> **驗證 Historical Knowledge Data Chain 的正確性**
> DWG + BOM → MatchResult → ParsedPart → HistoricalFeature → 資料庫

作為 Phase 3-4 的回歸測試基準。

---

## 二、Golden Dataset

### 2.1 內容

20 件已匹配零件，每件包含：

| 字段 | 來源 | 說明 |
|---|---|---|
| `dwg_file` | 文件系統 | DWG 文件名 |
| `bom_item` | BOM Excel | BOM 料號 |
| `material` | BOM description | 材料（標準化後） |
| `part_code` | BOM description | 零件代碼 |
| `dimensions_raw` | BOM description | 原始尺寸文字 |
| `dimensions_parsed` | Dimension Parser | 解析後的長/寬/高 |
| `surface_treatment` | BOM description | 表面處理 |
| `historical_price` | BOM Excel | 真實成交價 |
| `price_source` | BOM metadata | "BOM" |
| `source_bom_row` | BOM Excel | 來源行號 |
| `match_level` | Matcher | L1/L2/L3 |
| `project_name` | — | "GCS-雙滑台打磨設備" |

### 2.2 存儲格式

```
tests/regression/
├── __init__.py
├── conftest.py
├── golden_dataset.json          ← 20 件 Golden Data
├── test_golden_material.py      ← 材料驗證
├── test_golden_dimensions.py    ← 尺寸驗證
├── test_golden_price.py         ← 價格驗證
├── test_golden_matching.py      ← 匹配驗證
└── test_golden_source.py        ← Source 追蹤驗證
```

---

## 三、驗證項目

### 3.1 材料驗證 (test_golden_material.py)

| # | 測試 | 說明 |
|---|---|---|
| M1 | material_not_null | 所有加工件 material 不為 None |
| M2 | material_normalizable | material 可被 MaterialNormalizer 標準化 |
| M3 | material_match_golden | material 與 Golden Data 一致 |

### 3.2 尺寸驗證 (test_golden_dimensions.py)

| # | 測試 | 說明 |
|---|---|---|
| D1 | dimensions_raw_not_null | 所有加工件有尺寸文字 |
| D2 | dimensions_parsable | Dimension Parser 狀態非 FAILED |
| D3 | length_positive | 長度 > 0 |

### 3.3 價格驗證 (test_golden_price.py)

| # | 測試 | 說明 |
|---|---|---|
| P1 | price_positive | 所有零件 historical_price > 0 |
| P2 | price_source_is_bom | 所有零件 price_source = "BOM" |
| P3 | price_in_golden_range | 價格在合理範圍（非異常值） |

### 3.4 匹配驗證 (test_golden_matching.py)

| # | 測試 | 說明 |
|---|---|---|
| T1 | all_20_l1_matched | 20 件全部 L1 精確匹配 |
| T2 | dwg_candidate_extracted | 文件名成功提取候選號 |
| T3 | confidence_1_point_0 | L1 匹配信心度 = 1.0 |

### 3.5 Source 追蹤驗證 (test_golden_source.py)

| # | 測試 | 說明 |
|---|---|---|
| S1 | source_bom_not_null | 所有零件 source_bom 非空 |
| S2 | source_bom_row_valid | source_bom_row > 0 |
| S3 | historical_feature_has_source_dwg | HistoricalFeature.source_dwg 已設定 |
| S4 | data_chain_complete | DWG→BOM→Match→HistoricalFeature 鏈完整 |

---

## 四、Phase 3-4 回歸要求

後續 Phase 必須通過此數據集：

```bash
# Phase 3 完成後
pytest tests/regression/ -v  # 必須全部通過

# Phase 4 完成後增加
pytest tests/regression/ -v  # 必須全部通過
pytest --regression --golden  # 完整回歸（含價格對比）
```

---

## 五、禁止事項

| 禁止 | 原因 |
|---|---|
| 修改 Golden Data 以通過測試 | Golden Data 是 ground truth |
| 刪除失敗的測試 | 修復代碼，不是修復測試 |
| 在 Phase 2 測試價格誤差 | Rule Engine 尚未完成 |

---

*本文件為 Phase 2.4 設計。*
