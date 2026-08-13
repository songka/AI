# 機構2D自動報價系統 — 設計計劃 (Design Plan)

日期：2026-08-01
版本：V1.1（基於真實資料重新設計）

---

## 一、設計原則（不變）

來源：Claude Code 開發憲章 §1-5

1. **分層架構**：Domain → Application → Infrastructure → Rules
2. **數據驅動**：所有價格來自規則文件，禁止硬編碼
3. **可追溯**：每個價格標註來源（C/H/E/AI/M/U）
4. **可測試**：每模塊有獨立測試
5. **AI 受限**：AI 僅輔助文字理解和工藝推薦，不直接定價

---

## 二、修訂後的系統架構（雙流程設計）

### 2.1 核心決策：BOM 不是報價輸入

BOM 的定位為「歷史報價知識庫建立來源」，不是正式報價的必要輸入。

客戶通常只提供 PDF/DWG 圖紙，不會提供 BOM。

### 2.2 流程 A：知識庫建立（離線）

```
BOM Excel + DWG 圖紙
        │
        ▼
   BomReader (Phase 2.1)
        │
        ▼
   Description Parser + DWG/BOM Match (Phase 2.2-2.3)
        │
        ▼
   HistoricalFeature 合併
        │  (material, dimensions, surface, historical_price, source_bom, source_dwg)
        ▼
   quotation_history.db (SQLite)
```

### 2.3 流程 B：實際報價（線上）

```
客戶 PDF/DWG
        │
        ▼
   [ODA File Converter]  ← DWG→DXF
        │
        ▼
   [CAD Parser: ezdxf]   ← Phase 3
        │
        ▼
   [Feature Extractor]   ← Phase 3
        │
        ▼
   Feature Model
        │
        ├──────────────────────────────┐
        ▼                              ▼
   Similarity Search              Rule Engine
   (quotation_history.db)         (quotation-rules.yaml)
        │  source = H                  │  source = C
        │                              │  (material/process/surface/labor prices)
        └──────────┬───────────────────┘
                   ▼
              Quote Model
                   │  (每筆記錄: rule_version + price_versions + effective_date)
                   ▼
              Excel 輸出
                   │
                   ▼
              未命中 → AI 輔助 (Phase 5)
```

---

## 三、技術選型

| 項目 | 選擇 | 理由 |
|---|---|---|
| 語言 | Python 3.11+ | 運行環境 3.14.6 |
| 構建系統 | setuptools + pyproject.toml | PEP 621 |
| 測試框架 | pytest + pytest-cov | 憲章要求 |
| CAD 讀取 | ezdxf | DXF 解析 |
| DWG→DXF 轉換 | ODA File Converter | 外部命令行工具 |
| Excel 讀寫 | openpyxl + xlsxwriter | BOM 讀取 + 報價輸出 |
| YAML 規則 | PyYAML | 規則文件格式 |
| CLI 框架 | click | 命令行入口 |
| 數據驗證 | pydantic v2 | Domain 模型驗證 |
| 日誌 | logging (stdlib) | 無外部依賴 |

---

## 四、目錄結構（修訂版）

```
MechanicalQuotation/
├── src/quotation/
│   ├── domain/                    # Phase 1: 數據模型
│   │   ├── drawing.py             # Drawing 實體
│   │   ├── feature.py             # Feature 實體
│   │   ├── material.py            # Material + MaterialProperties
│   │   ├── quote.py               # Quote + QuoteItem
│   │   ├── rule.py                # RuleSet + 多模式 SurfaceRule
│   │   ├── issue.py               # Issue + UnknownItem
│   │   └── bom.py                 # [新增] BOM 數據模型
│   │
│   ├── application/               # 應用層
│   │   ├── analyze_service.py
│   │   ├── quote_service.py
│   │   └── batch_service.py
│   │
│   ├── infrastructure/
│   │   ├── dxf/
│   │   │   ├── converter.py       # [新增] DWG→DXF 轉換器
│   │   │   ├── parser.py          # DXF 解析
│   │   │   └── scanner.py         # 文件掃描
│   │   ├── excel/
│   │   │   ├── bom_reader.py      # [新增] BOM Excel 讀取
│   │   │   └── writer.py          # 報價 Excel 輸出
│   │   ├── database/
│   │   │   └── repository.py      # 歷史報價庫
│   │   └── ai/
│   │       └── assistant.py       # AI 輔助
│   │
│   ├── rules/                     # 規則引擎
│   │   ├── loader.py              # YAML/Excel 規則加載
│   │   ├── matcher.py             # 規則匹配
│   │   ├── calculator.py          # 價格計算（多模式）
│   │   └── validator.py           # 規則驗證
│   │
│   ├── cli/main.py
│   └── utils/
│       ├── config.py
│       ├── logging.py
│       └── serialization.py
│
├── rules/
│   ├── quotation-rules.yaml       # 主規則（材料+加工+表面處理）
│   └── material-density.yaml      # [新增] 材料物理屬性
│
├── tests/
│   ├── unit/domain/               # Phase 1
│   ├── unit/rules/                # Phase 4
│   ├── unit/infrastructure/       # Phase 3
│   ├── integration/               # Phase 2-4
│   └── regression/                # Phase 2: 20件 BOM 回歸測試
│
└── samples/
    ├── drawings/                   # 29 DWG + 25 PDF + BOM Excel
    ├── bom_extracted.json          # [已生成] BOM 提取數據
    ├── bom_parsed.json             # [已生成] BOM 結構化數據
    └── cross_reference.json        # [已生成] DWG↔BOM 交叉參照
```

---

## 五、核心數據模型設計（修訂版）

### 5.1 Drawing（圖紙實體）

```python
# domain/drawing.py
class Drawing:
    id: str
    file_path: str
    file_name: str
    source_format: str              # "DXF" | "DWG"
    entities: list[EntityInfo]
    raw_texts: list[str]
    parse_status: str               # "success" | "partial" | "failed"
    parse_errors: list[str]
```

### 5.2 BOM（歷史報價條目）— 新增

```python
# domain/bom.py
class BomEntry:
    """A single row from the BOM Excel."""
    item: str                       # "UC1000005854"
    description: str                # "原物料;加工件;S50C;J003;928*796*15;熱處理"
    level: int                      # BOM 層級 (0=成品, 1=組件, 2=零件)
    item_type: str                  # "Finished good" | "Subassembly" | "Purchased"
    uom: str                        # "ST" | "PCS" | "SET"
    quantity: float
    unit_cost: float                # 真實成交價（¥）
    extended_cost: float

class BomSheet:
    """Parsed BOM with cross-reference data."""
    source_file: str
    total_rows: int
    entries: list[BomEntry]
    # 結構化提取
    parts: list[ParsedPart]         # 從 description 解析出的結構化數據

class ParsedPart:
    """Structured data extracted from BOM description."""
    bom_item: str
    material: str | None            # "S50C", "A6061-T6", "SPCC", etc.
    part_code: str | None           # "J003", "R001", etc.
    dimensions: str | None          # "928*796*15"
    surface_treatment: str | None   # "熱處理", "表面噴砂陽極氧化銀色"
    unit_cost: float
```

### 5.3 Feature（零件特徵）

```python
# domain/feature.py
class Feature:
    drawing_id: str
    bom_ref: str | None             # 對應 BOM Item（如有）

    # 外形
    bounding_box: BoundingBox
    overall_length: float
    overall_width: float
    overall_height: float

    # 體積與重量（從尺寸+密度計算）
    volume_mm3: float | None
    weight_kg: float | None

    # 孔
    holes: list[Hole]
    hole_count: int

    # 材料（從圖紙文字或 BOM 獲取）
    material_text: str | None
    material_normalized: str | None

    # 表面處理
    surface_text: str | None
    surface_normalized: str | None

    # 加工
    tolerances: list[str]
    tech_requirements: list[str]
    all_texts: list[TextEntity]

    # 來源標記
    feature_source: str             # "CAD" | "BOM" | "BOTH" | "MANUAL"
```

### 5.4 Material（材料 — 含物理屬性）

```python
# domain/material.py
class MaterialProperties:
    """Physical properties from material-density.yaml."""
    name: str
    density: float                  # g/cm³ (required)
    category: str
    grade: str
    source_file: str

class MaterialRule:
    """Pricing rule from quotation-rules.yaml."""
    material_id: str
    material_name: str
    aliases: list[str]
    unit_price: float
    unit: str
    loss_rate: float
    status: str                     # "ACTIVE" | "PENDING" | "DEPRECATED"
    note: str | None
    # 關聯物理屬性
    properties: MaterialProperties | None
```

### 5.5 Rule（報價規則 — 擴展版）

```python
# domain/rule.py
class SurfacePricingMode(Enum):
    BY_WEIGHT = "by_weight"         # 元/kg
    BY_AREA = "by_area"             # 元/dm²
    BY_PIECE = "by_piece"           # 元/件
    BY_LENGTH = "by_length"         # 元/m

class SurfaceRule:
    surface_id: str
    surface_name: str
    pricing_mode: SurfacePricingMode
    unit_price: float
    unit: str
    min_charge: float | None
    applicable_materials: list[str]
    note: str | None

class ProcessRule:
    process_id: str
    process_name: str
    rate: float                     # 元/h
    unit: str
    conditions: list[str] | None

class RuleSet:
    version: str
    materials: list[MaterialRule]
    processes: list[ProcessRule]
    surfaces: list[SurfaceRule]
```

### 5.6 Quote（報價 — 含來源標記）

```python
# domain/quote.py
class PriceSource(Enum):
    C = "C"       # 公司規則
    H = "H"       # 歷史報價
    E = "E"       # 行業參考
    AI = "AI"     # AI 建議
    M = "M"       # 人工確認
    U = "U"       # 未知

class QuoteItem:
    category: str                   # "material" | "process" | "surface" | "purchased"
    name: str
    quantity: float
    unit: str
    unit_price: float
    amount: float
    source: PriceSource
    rule_id: str | None
    bom_ref: str | None             # 對應 BOM Item
    note: str | None

class Quote:
    id: str
    drawing_id: str
    items: list[QuoteItem]
    total: float
    source_summary: dict[str, float]  # {"C": 500, "H": 200, "U": 100}
```

---

## 六、核心 API 設計

### 6.1 CLI 入口

```bash
# Phase 1-2: 數據操作
quotation import-bom BOM.xlsx --output bom_data.json

# Phase 3: 單文件分析
quotation analyze drawing.dxf --rules rules/ --bom BOM.xlsx

# Phase 4: 批量報價
quotation batch ./drawings/ --rules rules/ --output result.xlsx

# Phase 0: 規則驗證
quotation validate-rules --rules rules/quotation-rules.yaml
```

### 6.2 Python API

```python
# application/bom_service.py (Phase 2)
def import_bom(excel_path: str) -> BomSheet: ...
def cross_reference_bom(bom: BomSheet, dwg_dir: str) -> list[tuple[str, BomEntry]]: ...

# application/analyze_service.py (Phase 3)
def analyze_drawing(file_path: str) -> Drawing: ...

# application/quote_service.py (Phase 4)
def quote_feature(feature: Feature, rules: RuleSet, bom: BomSheet | None) -> Quote: ...

# application/batch_service.py (Phase 4)
def batch_process(directory: str, rules: RuleSet, bom: BomSheet | None, output: str) -> list[Quote]: ...
```

---

## 七、Phase 開發順序（V2.0 — 2026-08-01）

```
Phase 0 ✅  初始化與風險處理
           ├── 項目框架（已完成）
           ├── 風險管理方案（risk-management.md）
           ├── 定價管理設計（pricing-management-design.md）
           └── DWG 轉換方案設計（待用戶安裝 ODA）

Phase 1 ✅  資料模型建立（已完成）
           ├── domain/drawing.py, feature.py, bom.py
           ├── domain/material.py, quote.py, rule.py, issue.py
           ├── domain/pricing.py         ← 待新增 (Phase 4)
           ├── domain/historical.py      ← 待新增 (Phase 2)
           └── 133 單元測試，99% domain 覆蓋率

Phase 2 🔜  歷史報價知識庫建立
           ├── BOM Excel Reader ✅ (Phase 2.1 完成)
           ├── Description Parser + Dimension Parser + Material Normalizer
           ├── DWG ↔ BOM 交叉匹配 (20件已匹配, 9件未匹配)
           ├── HistoricalFeature domain model
           ├── SQLite 資料庫 (quotation_history.db)
           ├── BOM → HistoricalFeature 導入器
           └── 20 件回歸測試基準

Phase 3 🔜  CAD 解析
           ├── DWG→DXF 轉換器（ODA File Converter）
           ├── DXF Parser（ezdxf: LINE/CIRCLE/ARC/POLYLINE/TEXT）
           ├── Feature Extractor（外形/孔/文字/公差）
           └── 用 20 件 DWG 驗證解析結果

Phase 4 🔜  報價規則引擎 + 定價管理
           ├── 價格 Excel 匯入器（material/process/surface/labor/time）
           ├── 價格版本管理（不可覆蓋，自動歸檔）
           ├── 規則加載（quotation-rules.yaml + material-density.yaml）
           ├── 規則匹配（material + surface + process）
           ├── 多模式價格計算（by_weight/area/piece/length）
           ├── 相似度搜索（Feature → HistoricalFeature）
           ├── 來源標記 (C/H/U) + 版本追蹤
           └── 與 20 件真實價格對比驗證（±15% 容忍）

Phase 5 🔜  AI 輔助分析
           ├── 材料名稱標準化（Phase 2 已有基礎）
           ├── 表面處理文字識別
           ├── 未知材料工藝推薦
           ├── 相似案例解釋
           └── 不可直接定價（AI 結果標記為 AI/M）

Phase 6 🔜  Excel 輸出 + GUI
           ├── 5-Sheet 報價 Excel
           ├── Windows GUI (可選)
           └── 價格維護 GUI (可選)

Phase 7+ 🔜  企業多人部署（設計已完成，核心報價驗證後實施）
           ├── 用戶認證 + Session (user-auth-design.md)
           ├── 角色權限 RBAC (permission-design.md)
           ├── 審計日誌 Local+SMB (audit-log-design.md)
           ├── SMB 部署 + Cache 同步 (smb/cache-sync-design.md)
           ├── 變更請求 + 規則發布 (multi-user-design.md)
           └── 飛書通知 + i18n (notification-design.md)
```

### Phase 2 修正後交付標準

```bash
pytest tests/unit/domain/ tests/unit/infrastructure/ tests/integration/ -v
# 所有測試通過

python -c "from quotation.infrastructure.excel.bom_reader import BomReader; ..."
# BOM Reader 可用

python -c "from quotation.domain.historical import HistoricalFeature; ..."
# HistoricalFeature 模型可用

sqlite3 quotation_history.db ".schema"  # 資料庫已建立
sqlite3 quotation_history.db "SELECT COUNT(*) FROM historical_parts"  # 20 rows
```

---

## 八、測試策略

### 8.1 測試分層

```
Regression (回歸測試)
  └── 20 件 BOM 已匹配零件：系統報價 vs 真實價格
Integration (集成測試)
  └── 完整報價流程（假 DXF + 真實規則 + 真實 BOM）
Unit (單元測試)
  └── 每模塊獨立測試，不依賴外部文件
```

### 8.2 覆蓋率目標

| 模塊 | 目標 |
|---|---|
| Rule Engine (loader + matcher + calculator) | ≥95% |
| Domain Models (validation + serialization) | ≥95% |
| BOM Reader | ≥90% |
| DXF Parser | ≥90% |
| Calculator | ≥95% |

### 8.3 Phase 2 回歸測試基準（20件）

回歸測試將比較系統計算價格與 BOM 真實價格：

```python
# tests/regression/test_bom_ground_truth.py
@pytest.mark.regression
@pytest.mark.parametrize("bom_item,expected_cost", [
    ("UC1000005854", 1425),   # S50C, J003, 928×796×15, 熱處理
    ("UC1000005855", 712),    # S50C, J005, 1400×250×15, 熱處理
    ("UC1002009711", 209),    # A6061-T6, R001, φ250×15, 陽極
    ("UC1002009712", 61),     # A6061-T6, R002, 60×70×20, 陽極
    # ... 共 20 件
])
def test_quote_matches_bom(bom_item, expected_cost):
    """系統報價應在 BOM 真實價格 ±15% 範圍內"""
    ...
```

---

## 七-B、Pricing Management Layer（定價管理層）

所有價格通過 Excel 維護，禁止硬編碼。詳見 `pricing-management-design.md` 和 `pricing-version-design.md`。

| 價格類型 | Excel 文件 | 版本管理 |
|---|---|---|
| 材料價格 | material-prices.xlsx | PriceVersion (effective_date) |
| 加工價格 | process-prices.xlsx | PriceVersion |
| 表面處理 | surface-prices.xlsx | PriceVersion，支持 4 種計價模式 |
| 人工費率 | labor-rates.xlsx | PriceVersion |
| 工時規則 | process-times.xlsx | PriceVersion |

定價流程：

```
Excel 維護 → import 命令 → 自動歸檔 + 新版本 → Quote 根據 quote_date 自動選擇有效版本
```

---

## 七-C、設計補充（2026-08-01）

| # | 主題 | 詳細文檔 | 關鍵模型 |
|---|---|---|---|
| 1 | Quote Snapshot | quote-lifecycle-design.md §三 | QuoteSnapshot（不可變快照） |
| 2 | Drawing Revision | quote-lifecycle-design.md §四 | DrawingRevision, RevisionHistory |
| 3 | Drawing Validation | quote-lifecycle-design.md §八 | ValidationCheck（完整性檢查） |
| 4 | Feature Similarity | quote-lifecycle-design.md §九 | FeatureSimilarity, SimilarityResult |
| 5 | Quote Confidence | quote-lifecycle-design.md §五 | ConfidenceScorer (C=1.0, H=0.8, U=0.0) |
| 6 | Correction Record | quote-lifecycle-design.md §六 | CorrectionRecord (人工修正追溯) |
| 7 | Cost/Selling Price | quote-lifecycle-design.md §七 | total_cost vs selling_price |
| 8 | Supplier Database | quote-lifecycle-design.md §十 | Supplier, SupplierQuote |
| 9 | 異常處理 | exception-handling-design.md | FATAL/ERROR/WARNING/INFO 四級 |

---

## 八、企業多人部署架構（2026-08-01 新增）

### 8.1 部署環境

| 項目 | 值 |
|---|---|
| SMB 共享路徑 | `\\10.97.0.210\lfaf_Engineer\Mechanical\3-標準文檔\10-自動報價系統\data` |
| Client OS | Windows 10/11 |
| 網路 | 區域網路（LAN），所有 Client 可訪問 SMB |
| 權限模式 | SMB 全員可讀寫 → 軟件內建帳號權限系統 |

### 8.2 新增子系統

| 子系統 | 文檔 | Phase |
|---|---|---|
| 用戶認證 | user-auth-design.md | Phase 4 |
| 角色權限 (RBAC) | permission-design.md | Phase 4 |
| 審計日誌 | audit-log-design.md | Phase 4 |
| 飛書通知 | notification-design.md | Phase 5 |
| SMB 部署 | smb-deployment-design.md | Phase 4 |
| Cache 同步 | cache-sync-design.md | Phase 4 |
| 多人協作 | multi-user-design.md | Phase 4-5 |

### 8.3 關鍵設計決策

| 決策 | 說明 |
|---|---|
| SMB 僅存儲 | 不執行邏輯，Client 端計算 |
| 規則發布流程 | Draft → Review → Published → Archived |
| 報價鎖定版本 | Quote Session 凍結價格版本，不受他人變更影響 |
| 密碼安全 | bcrypt hash + salt，不可明文 |
| 權限非硬編碼 | YAML 配置文件定義 |
| Windows Mutex | 防止同機多開 |
| i18n | zh-CN / zh-TW / en-US |

---

## 九、設計文檔索引

| 文檔 | 說明 |
|---|---|
| `docs/design-plan.md` | 本文 — 總體設計計劃 |
| `docs/architecture.md` | 架構概述（含部署架構） |
| `docs/domain-design.md` | Domain 模型（含 HistoricalFeature） |
| `docs/bom-design.md` | BOM 數據模型 + 知識庫定位 |
| `docs/pricing-management-design.md` | 定價管理層 |
| `docs/pricing-version-design.md` | 價格版本管理 + 趨勢分析 |
| `docs/quote-lifecycle-design.md` | 報價生命週期 |
| `docs/exception-handling-design.md` | 異常處理策略 |
| `docs/multi-user-design.md` | 多人使用架構 |
| `docs/user-auth-design.md` | 用戶認證 |
| `docs/permission-design.md` | 角色權限 |
| `docs/audit-log-design.md` | 審計日誌 |
| `docs/notification-design.md` | 飛書通知 |
| `docs/smb-deployment-design.md` | SMB 部署 |
| `docs/cache-sync-design.md` | Cache 同步 |
| `docs/risk-management.md` | 風險管理 |
| `docs/audit-report.md` | 項目審計報告 |
| `docs/progress.md` | 開發進度 |
| `docs/decisions.md` | ADR 決策記錄 |

| 數據 | 負責 | 期限 |
|---|---|---|
| **安裝 ODA File Converter** | 用戶 | Phase 3 前 |
| **SPCC 材料價格** | 用戶（採購部門） | Phase 4 前 |
| **表面噴塗價格** | 用戶 | Phase 4 前 |
| 材料密度數據 | 系統（材料手冊） | Phase 1 |
| Z 系列 9 件確認 | 用戶 | Phase 2 |
| 報價 Excel 模板 | 用戶 | Phase 4 前 |

---

*本文件隨開發進展持續更新。下一步：用戶確認後開始 Phase 1 數據模型實現。*
