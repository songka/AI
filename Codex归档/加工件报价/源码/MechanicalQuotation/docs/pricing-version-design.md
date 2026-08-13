# 機構2D自動報價系統 — 價格版本管理設計

日期：2026-08-01
版本：V1.0

---

## 一、設計目標

1. 所有價格規則必須支持時間版本
2. 歷史價格不可覆蓋，每次變更產生新版本
3. 報價時根據 `quote_date` 自動選擇當時有效價格
4. 支持價格趨勢分析（材料/加工/零件歷史曲線）

---

## 二、PriceVersion Model

### 2.1 版本核心模型

```python
# domain/pricing.py

class PriceVersion(BaseModel):
    """A version snapshot of a price set.

    Each import of an Excel price file creates a new PriceVersion.
    """

    version_id: str = Field(
        ..., description="Unique version ID, e.g. 'MAT-2025-01-01-v1'"
    )
    name: str = Field(
        ..., description="Human-readable name, e.g. '2025年Q1材料價格'"
    )
    price_type: str = Field(
        ..., description="material | process | surface | labor | time"
    )

    effective_date: str = Field(
        ..., description="ISO date when this version takes effect, e.g. '2025-01-01'"
    )
    expires_date: str | None = Field(
        default=None, description="ISO date when superseded (None = still active)"
    )

    created_by: str = Field(default="SYSTEM", description="Who created this version")
    created_time: str = Field(..., description="ISO datetime of creation")

    source_file: str | None = Field(default=None, description="Excel file imported from")
    row_count: int = Field(default=0, description="Number of price items")
    changes_summary: str = Field(default="", description="Human-readable change log")

    is_active: bool = Field(default=True)
```

### 2.2 版本 ID 命名規則

```
{PRICE_TYPE}-{EFFECTIVE_DATE}-v{VERSION_NUMBER}

例:
  MAT-2025-01-01-v1     ← 材料價格第1版，2025-01-01生效
  MAT-2025-06-15-v2     ← 材料價格第2版，2025-06-15生效
  PROC-2025-01-01-v1    ← 加工價格第1版
  SURF-2025-01-01-v1    ← 表面處理第1版
  LAB-2025-01-01-v1     ← 人工費率第1版
```

### 2.3 所有價格型別加版本關聯

```python
class MaterialPrice(BaseModel):
    material_id: str
    material_name: str
    density: float
    unit_price: float
    unit: str = "kg"
    loss_rate: float = 0.05
    effective_date: str | None = None
    status: str = "ACTIVE"

    # -- Version FK --
    version_id: str = Field(..., description="FK to PriceVersion.version_id")
    # 例: "MAT-2025-01-01-v1"

class ProcessPrice(BaseModel):
    process_id: str
    process_name: str
    equipment: str | None = None
    rate: float                     # CNY/hour
    unit: str = "hour"
    conditions: str | None = None
    effective_date: str | None = None
    status: str = "ACTIVE"
    version_id: str                 # FK

class SurfacePrice(BaseModel):
    surface_id: str
    surface_name: str
    pricing_mode: str               # by_weight | by_area | by_piece | by_length
    unit_price: float
    unit: str = "kg"
    min_charge: float | None = None
    applicable_materials: str = ""
    effective_date: str | None = None
    status: str = "ACTIVE"
    version_id: str                 # FK

class LaborPrice(BaseModel):
    labor_id: str
    labor_type: str
    rate: float                     # CNY/hour
    unit: str = "hour"
    applicable: str | None = None
    effective_date: str | None = None
    status: str = "ACTIVE"
    version_id: str                 # FK

class ProcessTimeRule(BaseModel):
    rule_id: str
    feature_condition: str
    process_name: str
    base_time_min: float
    time_unit: str
    formula: str | None = None
    effective_date: str | None = None
    status: str = "ACTIVE"
    version_id: str                 # FK
```

---

## 三、報價時的自動版本選擇

### 3.1 Quote 增加 quote_date

```python
class Quote(BaseModel):
    ...
    # -- Version tracking --
    quote_date: str | None = None            # 報價日期 "2025-03-15"

    rule_version: str | None = None          # quotation-rules.yaml version
    material_price_version: str | None = None  # "MAT-2025-01-01-v1"
    process_price_version: str | None = None
    surface_price_version: str | None = None
    labor_price_version: str | None = None
    time_rule_version: str | None = None
```

### 3.2 版本選擇邏輯

```python
# rules/version_resolver.py (Phase 4)

def resolve_active_version(
    price_type: str,       # "material" | "process" | "surface" | "labor" | "time"
    quote_date: str,       # "2025-03-15"
    versions: list[PriceVersion],
) -> PriceVersion | None:
    """Find the version effective on quote_date.

    Rule: effective_date <= quote_date AND (expires_date IS NULL OR expires_date > quote_date)
    If multiple match, pick the one with the latest effective_date.
    """
    candidates = [
        v for v in versions
        if v.price_type == price_type
        and v.effective_date <= quote_date
        and (v.expires_date is None or v.expires_date > quote_date)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda v: v.effective_date)


def resolve_prices_for_quote(
    quote_date: str,
    all_versions: list[PriceVersion],
    all_material_prices: list[MaterialPrice],
    all_process_prices: list[ProcessPrice],
    all_surface_prices: list[SurfacePrice],
    all_labor_prices: list[LaborPrice],
) -> QuotePriceSet:
    """Resolve all active prices for a specific quote date."""
    mat_version = resolve_active_version("material", quote_date, all_versions)
    proc_version = resolve_active_version("process", quote_date, all_versions)
    surf_version = resolve_active_version("surface", quote_date, all_versions)
    labor_version = resolve_active_version("labor", quote_date, all_versions)

    return QuotePriceSet(
        material_prices=[p for p in all_material_prices
                         if p.version_id == mat_version.version_id] if mat_version else [],
        process_prices=[p for p in all_process_prices
                        if p.version_id == proc_version.version_id] if proc_version else [],
        surface_prices=[p for p in all_surface_prices
                        if p.version_id == surf_version.version_id] if surf_version else [],
        labor_prices=[p for p in all_labor_prices
                        if p.version_id == labor_version.version_id] if labor_version else [],
    )
```

### 3.3 版本選擇示例

```
價格版本時間線:
  MAT-2024-06-01-v1  ← 2024-06-01生效
  MAT-2025-01-01-v1  ← 2025-01-01生效 (A6061: 36→38元/kg)
  MAT-2025-06-15-v1  ← 2025-06-15生效 (新增 SPCC)

報價日期: 2025-03-15
  → resolve: MAT-2025-01-01-v1 (effective=2025-01-01 <= 2025-03-15)

報價日期: 2025-07-01
  → resolve: MAT-2025-06-15-v1 (effective=2025-06-15 <= 2025-07-01)

報價日期: 2024-08-01
  → resolve: MAT-2024-06-01-v1 (effective=2024-06-01 <= 2024-08-01)
```

---

## 四、價格分析功能設計

### 4.1 材料價格曲線

```python
# analysis/price_trends.py (Phase 4+)

@dataclass
class PricePoint:
    """Single data point on a price trend."""
    date: str           # ISO date
    material: str       # Material name
    unit_price: float   # CNY/unit
    version_id: str     # Which version


def get_material_price_history(
    material_name: str,
    all_versions: list[PriceVersion],
    all_prices: list[MaterialPrice],
) -> list[PricePoint]:
    """Extract price history for a specific material across all versions.

    Returns ordered list from oldest to newest.
    """
    ...

# 輸出示例:
# A6061-T6 價格歷史:
#   2024-06-01: 36.00 CNY/kg (MAT-2024-06-01-v1)
#   2025-01-01: 38.00 CNY/kg (MAT-2025-01-01-v1)  ↑5.6%
```

### 4.2 加工價格曲線

```python
def get_process_price_history(
    process_name: str,
    all_versions: list[PriceVersion],
    all_prices: list[ProcessPrice],
) -> list[PricePoint]:
    """CNC, 車床, 磨床 等加工費率歷史."""
    ...

# 輸出示例:
# CNC加工費率歷史:
#   2024-06-01: 75.00 CNY/h
#   2025-01-01: 80.00 CNY/h  ↑6.7%
```

### 4.3 零件歷史報價曲線

```python
def get_part_quote_history(
    part_no: str,
    quotes: list[Quote],
) -> list[dict]:
    """Get all historical quotes for a specific part number.

    Each quote includes:
    - quote_date
    - total price
    - price versions used
    - source breakdown (C/H/U)
    """
    ...

# 輸出示例:
# UC1000005854 (J003) 報價歷史:
#   2025-01-15: ¥1,425 (來源: BOM)
#   2025-03-20: ¥1,520 (來源: C-60%, H-40%)  ← 規則引擎
```

### 4.4 CLI 命令（Phase 4+）

```bash
# 查看材料價格歷史
quotation price-history material A6061-T6

# 查看加工費率歷史
quotation price-history process CNC

# 查看零件報價歷史
quotation quote-history UC1000005854

# 導出價格趨勢報告
quotation price-trends --output trends.xlsx
```

---

## 五、版本歸檔存儲

### 5.1 目錄結構

```
rules/
├── current/                       ← 當前版本（程序讀取）
│   ├── material-prices.xlsx
│   ├── process-prices.xlsx
│   ├── surface-prices.xlsx
│   ├── labor-rates.xlsx
│   └── process-times.xlsx
│
└── archive/                       ← 歷史版本歸檔（不可修改）
    ├── MAT-2024-06-01-v1/
    │   └── material-prices.xlsx
    ├── MAT-2025-01-01-v1/
    │   └── material-prices.xlsx
    ├── PROC-2025-01-01-v1/
    │   └── process-prices.xlsx
    └── ...
```

### 5.2 匯入流程

```python
def import_price_file(
    source_path: str,       # "rules/current/material-prices.xlsx"
    price_type: str,        # "material"
    archive_dir: str,       # "rules/archive/"
    created_by: str = "SYSTEM",
) -> PriceVersion:
    """Import a price Excel file.

    1. Read the new Excel
    2. Generate new version_id
    3. Copy current file to archive/{version_id}/
    4. Create PriceVersion record
    5. Update all prices with new version_id
    6. Mark old version as expired (set expires_date)
    """
    ...
```

---

## 六、數據模型總覽

```
PriceVersion (版本快照)
  ├── version_id, name, effective_date, created_by
  │
  ├─→ MaterialPrice[]    (version_id FK)
  ├─→ ProcessPrice[]     (version_id FK)
  ├─→ SurfacePrice[]     (version_id FK)
  ├─→ LaborPrice[]       (version_id FK)
  └─→ ProcessTimeRule[]  (version_id FK)

Quote (報價單)
  ├── quote_date
  ├── material_price_version  → PriceVersion.version_id
  ├── process_price_version   → PriceVersion.version_id
  ├── surface_price_version   → PriceVersion.version_id
  ├── labor_price_version     → PriceVersion.version_id
  └── time_rule_version       → PriceVersion.version_id

PricePoint (分析用)
  ├── date, material/process
  ├── unit_price
  └── version_id → PriceVersion.version_id
```

---

## 七、禁止事項

| 禁止 | 正確做法 |
|---|---|
| 修改 archive/ 中的文件 | archive/ 為唯讀歸檔 |
| 報價不記錄版本 | 每個 Quote 必須記錄所有 price version |
| 直接覆蓋 current/ 文件 | 使用 import 命令自動歸檔 |
| hardcode 版本選擇日期 | 從 Quote.quote_date 自動選擇 |
| AI 修改價格版本 | 版本變更需人工確認 |

---

*本文件為 Phase 2 設計補充。版本管理實現在 Phase 4 完成。*
