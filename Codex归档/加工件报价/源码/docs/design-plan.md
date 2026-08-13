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

## 二、修訂後的系統數據流

基於真實資料分析，系統流程應為：

```
DWG (二進制)                          PDF (視覺參考)
    │                                     │
    ▼                                     │
[ODA File Converter]                      │
    │                                     │
    ▼                                     │
DXF (文本交換格式)                        │
    │                                     │
    ▼                                     │
[CAD Parser: ezdxf]                       │
    │                                     │
    ▼                                     │
Drawing Model ────────────────────────────┘
    │  (幾何實體、尺寸、文字)
    ▼
[Feature Extractor]
    │  (外形、孔、材料文字、表面處理文字)
    ▼
Feature Model
    │
    ├──────────────────────────────────────┐
    ▼                                      ▼
[BOM 歷史報價庫]                    [Rule Engine]
    │  (真實成交價)                    │  (公司規則)
    │  source = H                      │  source = C
    │                                      │
    ├──────────────────────────────────────┤
    │              Quote Model             │
    │  (來源標記: C/H/E/AI/M/U)           │
    │                                      │
    ├── 未命中 ────────────────────────────┤
    ▼                                      │
[AI 輔助分析]                              │
    │  (文字理解、工藝推薦)                │
    │  source = AI/M                       │
    │                                      │
    └──────────────────────────────────────┘
                       │
                       ▼
               [Excel 輸出]
                 5 Sheets:
                 1. 報價匯總
                 2. 成本明細
                 3. 未知項
                 4. 規則匹配記錄
                 5. 日誌
```

### 核心決策：BOM 歷史報價庫優先級

```
規則引擎 (C) → BOM歷史價 (H) → 行業參考 (E) → AI建議 (AI/M) → 未知 (U)
```

BOM 的 20 件已匹配零件**同時服務兩個角色**：
1. **Phase 2**：作為 H 來源（歷史報價庫）
2. **Phase 4**：作為回歸測試基準（驗證規則引擎計算結果 vs 真實價格）

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

## 七、Phase 開發順序（修訂版）

```
Phase 0 ✅  初始化與風險處理
           ├── 項目框架（已完成）
           ├── 風險管理方案（risk-management.md）
           └── DWG 轉換方案設計（待用戶安裝 ODA）

Phase 1 🔜  資料模型建立
           ├── domain/drawing.py
           ├── domain/bom.py          ← 新增
           ├── domain/feature.py
           ├── domain/material.py     ← 含 MaterialProperties
           ├── domain/quote.py        ← 含 PriceSource
           ├── domain/rule.py         ← 含 SurfacePricingMode
           ├── domain/issue.py
           └── 每模塊對應的單元測試

Phase 2 🔜  歷史報價資料庫
           ├── BOM Excel 讀取器
           ├── 20 件回歸測試基準
           ├── BOM ↔ DWG 交叉參照
           └── regression/ 測試目錄

Phase 3 🔜  CAD 解析
           ├── DWG→DXF 轉換器（ODA）
           ├── DXF Parser（ezdxf）
           └── 用 20 件 DWG 驗證解析結果

Phase 4 🔜  報價規則引擎
           ├── 規則加載（含 material-density.yaml）
           ├── 規則匹配
           ├── 多模式價格計算
           ├── 來源標記 (C/H/U)
           └── 與 20 件真實價格對比驗證

Phase 5 🔜  AI 輔助分析
           ├── 材料名稱標準化
           ├── 表面處理文字識別
           ├── 工藝推薦
           └── 未知項補充建議
```

### Phase 1 交付標準

```bash
pytest tests/unit/domain/ -v        # 所有 Domain 模型測試通過
python -c "from quotation.domain import Drawing, Feature, Quote, Rule, Issue, BomEntry, MaterialProperties"
python -c "from quotation.domain.bom import BomEntry; print(BomEntry.schema())"
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

## 九、數據缺口行動計劃

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
