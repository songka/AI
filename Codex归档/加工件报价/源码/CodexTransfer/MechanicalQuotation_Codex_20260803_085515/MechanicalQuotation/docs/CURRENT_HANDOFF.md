# CURRENT HANDOFF — 2026-08-01 (夜間更新)

## 狀態摘要

| 項目 | 狀態 |
|------|------|
| Git | master branch, clean working tree |
| Commits | `b504c43` (UI fix) + `51546f6` (batch) + `32bdf83` (API) + `74c4e49` (secrets) |
| 測試數 | **654** (50 files, +46 from baseline 608) |
| Tasks完成 | ✅ Task 0 + 0.1 + A + Phase 5.0 + 5.1 |
| 下一個任務 | W002 材料費 / W001 價格匹配 |
| DeepSeek | CONFIGURED — runtime/secrets/deepseek_api_key.txt |
| API | http://127.0.0.1:8000/docs |
| UI | .venv/Scripts/python -m quotation.ui.demo_app |
| 可攜式目錄 | dist/MechanicalQuotation/ |
| 資料庫 | runtime/data/quotation_history.db (SQLite) |

---

## ✅ Task 0: Published Company Pricebook Integration

### 正式調用鏈

```
PricingResolver.__init__()
  └─ PublishedPricebookLoader(data/current-version-pointer.json)
       ├─ validate: status=PUBLISHED, SHA256, version match, effective date
       └─ build indexes: 32 materials, 8 processes, 4 surfaces

PricingResolver.lookup(category, name)
  ├─ 1. PublishedPricebookLoader.lookup_*()
  │     └─ filters eligible_for_resolution=True (excludes Pending S)
  │     └─ returns PriceLookupResult(resolution_source=PUBLISHED_COMPANY_PRICEBOOK)
  └─ 2. Legacy YAML (DRAFT detected → LEGACY_YAML_DRAFT + fallback_warning)
```

### 修改文件 (Task 0 + 0.1)

| 檔案 | 操作 |
|------|------|
| `data/current-version-pointer.json` | NEW |
| `src/quotation/infrastructure/rules/published_pricebook_loader.py` | NEW |
| `src/quotation/infrastructure/rules/pricing_resolver.py` | REWRITTEN |
| `src/quotation/infrastructure/rules/calculators/__init__.py` | MODIFIED |
| `src/quotation/domain/quote.py` | MODIFIED (+12 trace fields) |
| `tests/unit/rules/test_pricebook_integration.py` | NEW (20 tests) |
| `tests/unit/rules/test_rule_engine.py` | REFACTORED (isolated from production pointer) |
| `tests/unit/rules/conftest.py` | NEW (test isolation) |
| `tests/unit/rules/test_rules.yaml` | NEW (test-specific prices) |
| `docs/CURRENT_HANDOFF.md` | UPDATED |

---

## J003 完整 Trace

```
=== material: S50C 材料費 ===
  amount=969.31 CNY | unit_price=10.0 CNY/kg
  source=C
  quote_price_source=C
  resolution_source=PUBLISHED_COMPANY_PRICEBOOK
  price_version_id=R01-COMPANY-PRICE-V1.0
  company_price_id=CP-ea9866e3316b
  origin_price_source=S
  origin_price_record_id=PR-B3D59928F064FF
  origin_supplier_id=None ⚠️
  price_basis=EXCLUDING_TAX

=== process: CNC 加工費 ===
  resolution_source=PUBLISHED_COMPANY_PRICEBOOK
  company_price_id=CP-38bf74b25194

=== process: TAP 加工費 (FALLBACK) ===
  resolution_source=LEGACY_YAML_DRAFT
  fallback_approval_status=DRAFT_REQUIRES_CORRECTION
  fallback_warning=True

=== surface: 表面鍍鉻 ===
  resolution_source=PUBLISHED_COMPANY_PRICEBOOK
  company_price_id=CP-75e0fa7fafca
```

---

## origin_supplier_id 結果

**S50C origin_supplier_id = `None`** ⚠️

**阻塞原因:** 這是 Published Snapshot 的**資料品質問題**，非程式碼問題。

Snapshot `company-pricebook-r01-v1.0-snapshot.json` 中的 S50C 記錄：
```json
{
  "company_price_id": "CP-ea9866e3316b",
  "origin_type": "SUPPLIER_PRICE_RECORD",
  "origin_supplier_id": null,
  "origin_price_record_id": "PR-B3D59928F064FF",
  "unit_price": 10.0
}
```

程式碼正確地：
1. 從 snapshot 讀取 `origin_supplier_id` → `null`
2. 將 `origin_type=SUPPLIER_PRICE_RECORD` 映射為 `origin_price_source=S`
3. 原樣保留 `origin_supplier_id=None` 到 `QuoteItem`

**要顯示為 Tongrui，需在 admin review 階段將 supplier_id 寫入 snapshot。** 這不在本次程式修改範圍內。

---

## Legacy Draft Fallback 警告機制

當 PricingResolver 回退到 Legacy YAML 且 YAML 狀態為 DRAFT 時：

- `resolution_source` = `LEGACY_YAML_DRAFT`（非 `LEGACY_YAML`）
- `fallback_approval_status` = YAML 中的 `status` 欄位值
- `fallback_warning` = `True`
- `fallback_reason` = 完整說明含版本號

當前生產 YAML (`rules/quotation-rules.yaml`) status = `DRAFT_REQUIRES_CORRECTION`，
因此所有 fallback 項目（如 TAP）都會被標記為 `LEGACY_YAML_DRAFT`。

---

## 測試結果

**590 passed, 2 skipped** ✓

| 類別 | 數量 |
|------|------|
| Pricebook integration tests | 20 (14 + 6 hardening) |
| Rule engine tests (isolated) | 21 |
| Cost completion tests | 7 |
| Other existing tests | 549 |
| **Total** | **597** |

---

## ✅ Task A: Quote Builder cost_completion dead code fix

### 問題
`quote_builder.py` L33-37 中的 `cost_completion` 計算位於 `return Quote(...)` 之後，永遠不執行。

### 修復
1. `Quote` 模型新增 `cost_completion: float` 欄位（`quote.py`）
2. `QuoteBuilder` 新增 `_calculate_cost_completion()` 私有純函數
3. 在 `return Quote(...)` **之前**計算並傳入 `cost_completion=...`
4. 移除 `return` 後的不可達程式碼
5. CLI 從 `quote.cost_completion` 讀取（原從 `source_summary` 讀取）

### cost_completion 計算規則
- `source=U` → 未完成
- `amount=None` → 未完成
- `amount=0` 且 `source≠U` → 合法已知價格（已完成）
- 空清單 → 0%
- 結果限制在 0.0–100.0

### J003 示例
| 指標 | 值 |
|------|-----|
| item 總數 | 4 |
| known | 4 |
| unknown | 0 |
| cost_completion | **100.0%** |
| status | COMPLETE |

### W001 示例
| 指標 | 值 |
|------|-----|
| item 總數 | 7 |
| known | 6 |
| unknown | 1 |
| cost_completion | **85.7%** |
| status | INCOMPLETE |

### 修改檔案
| 檔案 | 操作 |
|------|------|
| `src/quotation/domain/quote.py` | +cost_completion field |
| `src/quotation/infrastructure/rules/quote_builder.py` | +_calculate_cost_completion, fix dead code |
| `src/quotation/cli/main.py` | 改讀 quote.cost_completion |
| `tests/unit/rules/test_quote_builder.py` | +7 tests |

---

## 下一個原子任務

**W002 材料費 → SPCC 2mm 邏輯**

---

## 尚未處理

- W002 材料費 → SPCC 2mm 邏輯
- W001 AL_PROFILE 40x40 → frame profile 規格匹配
- J029 CNC 40 元 → `_CNC_BASE_HOURS` 對 0 holes
- J001 BBOX_ESTIMATE → REVIEW_REQUIRED 狀態
- RAL9003 V1.1 → 待發布 (DRAFT)

---

## Git Status — 已提交 (Checkpoint 2026-08-01)

### Commits
```
4311caf docs: update CURRENT_HANDOFF.md with checkpoint info
e4676df checkpoint: apply remaining Task 0/0.1 working tree modifications (5 files)
efb119e checkpoint: published pricebook integration and hardening  (root, 223 files)
```

### Working Tree: 4 files modified (Task A — pending commit)

### .gitignore 排除類別
| 類別 | 說明 |
|------|------|
| `*.xlsx`, `*.xls` | 二進制 Excel 文件 |
| `samples/drawings/*.DWG` | CAD 原始檔 (~28MB) |
| `samples/drawings/*.pdf` | PDF 圖紙 |
| `src/quotation/demo_*.dxf` | 生成的暫存 DXF |
| `data/price-review-*.json` | 價格審查中間產物 |
| `data/pricing-import-preview*.json` | 導入預覽中間產物 |
| `__pycache__/`, `*.pyc` | Python bytecode |
| `.venv/`, `.pytest_cache/`, `htmlcov/` | 虛擬環境/測試/覆蓋率 |
| `import_test.txt`, `pytest_result.txt` | 暫存測試文件 |
