# 機構2D自動報價系統 — 定價管理層設計

日期：2026-08-01
版本：V1.0

---

## 一、核心原則

1. **所有價格必須有來源** — 禁止硬編碼
2. **歷史價格不可覆蓋** — 每次變更產生新版本
3. **每筆報價必須記錄價格版本** — rule_version + price_version + effective_date
4. **人員通過 Excel 維護價格** — 不需要程式背景
5. **系統讀取 Excel → YAML 規則** — 程序內部使用結構化規則

---

## 二、價格管理架構

```
人員維護 (Excel)
    │
    ├── material-prices.xlsx    ← 材料價格
    ├── process-prices.xlsx     ← 加工價格
    ├── surface-prices.xlsx     ← 表面處理價格
    ├── labor-rates.xlsx        ← 人工費率
    └── process-times.xlsx      ← 工時規則
    │
    ▼
Version Manager (版本管理)
    │ 每次變更 → 新版本號
    │ 舊版本 → 歸檔保存
    ▼
Rules YAML (程序讀取)
    │
    ├── quotation-rules.yaml    ← 組裝後的完整規則
    └── material-density.yaml   ← 物理屬性（不變）
    │
    ▼
Rule Engine (Phase 4)
    │
    ▼
Quote (記錄使用的版本)
```

---

## 三、Material Price Model

### 3.1 Excel 格式 (material-prices.xlsx)

| material_id | material_name | density | unit_price | unit | loss_rate | effective_date | status | note |
|---|---|---|---|---|---|---|---|---|
| MAT001 | A6061-T6 | 2.70 | 38.00 | kg | 0.05 | 2025-01-01 | ACTIVE | |
| MAT002 | S50C | 7.85 | 9.00 | kg | 0.05 | 2025-01-01 | ACTIVE | |
| MAT003 | SUS304 | 7.93 | 28.00 | kg | 0.05 | 2025-01-01 | ACTIVE | |
| MAT004 | SKD11 | 7.85 | 55.00 | kg | 0.05 | 2025-01-01 | ACTIVE | |
| MAT005 | SPCC | 7.85 | 0 | kg | 0.05 | — | PENDING | 待採購確認 |

### 3.2 版本追蹤

```yaml
# 每次匯入時自動生成版本記錄
material_price_versions:
  - version: "1.0"
    imported_at: "2025-01-01"
    source_file: "material-prices.xlsx"
    changes: "初始匯入 5 種材料"
  - version: "1.1"
    imported_at: "2025-06-15"
    source_file: "material-prices.xlsx"
    changes: "A6061-T6: 36→38; 新增 SPCC(PENDING)"
```

### 3.3 數據模型

```python
# domain/pricing.py

class MaterialPrice(BaseModel):
    """Material price record with version tracking."""

    material_id: str = Field(..., description="MAT001")
    material_name: str = Field(..., description="A6061-T6")
    density: float = Field(..., gt=0)
    unit_price: float = Field(..., ge=0)
    unit: str = "kg"
    loss_rate: float = Field(default=0.05, ge=0, le=1)
    effective_date: str | None = None    # ISO date
    status: str = "ACTIVE"              # ACTIVE | PENDING | DEPRECATED
    note: str | None = None

    # Version tracking
    price_version: str = "1.0"
    updated_at: str | None = None
```

---

## 四、Process Price Model

### 4.1 Excel 格式 (process-prices.xlsx)

| process_id | process_name | equipment | rate | unit | conditions | effective_date | status |
|---|---|---|---|---|---|---|---|
| PROC001 | CNC | 三軸加工中心 | 80 | hour | 普通精度 | 2025-01-01 | ACTIVE |
| PROC002 | CNC精密 | 五軸加工中心 | 250 | hour | 公差<0.02mm | 2025-01-01 | ACTIVE |
| PROC003 | 車床 | 普通車床 | 40 | hour | — | 2025-01-01 | ACTIVE |
| PROC004 | 磨床 | 平面磨床 | 55 | hour | — | 2025-01-01 | ACTIVE |
| PROC005 | 鉗工 | — | 88 | hour | — | 2025-01-01 | ACTIVE |
| PROC006 | 線割快絲 | 快走絲 | 30 | hour | — | 2025-01-01 | ACTIVE |
| PROC007 | 線割慢絲 | 慢走絲 | 100 | hour | — | 2025-01-01 | ACTIVE |
| PROC008 | 放電 | — | 30 | hour | — | 2025-01-01 | ACTIVE |

### 4.2 數據模型

```python
class ProcessPrice(BaseModel):
    """Process/machining price record."""

    process_id: str = Field(...)
    process_name: str = Field(...)
    equipment: str | None = None
    rate: float = Field(..., gt=0, description="CNY/hour")
    unit: str = "hour"
    conditions: str | None = None
    effective_date: str | None = None
    status: str = "ACTIVE"

    price_version: str = "1.0"
    updated_at: str | None = None
```

---

## 五、Surface Treatment Price Model

### 5.1 Excel 格式 (surface-prices.xlsx)

支持多種計價模式。不同模式使用不同欄位：

| surface_id | surface_name | pricing_mode | unit_price | unit | min_charge | applicable_materials | effective_date | status |
|---|---|---|---|---|---|---|---|---|
| SURF001 | 熱處理 | by_weight | 11.00 | kg | 50 | S50C,SKD11,SKD61 | 2025-01-01 | ACTIVE |
| SURF002 | 陽極氧化 | by_area | 0.15 | dm2 | 30 | A6061-T6 | 2025-01-01 | ACTIVE |
| SURF003 | 噴塗(RAL9003) | by_area | 0.35 | dm2 | 50 | SPCC,普通鋼 | 2025-01-01 | ACTIVE |
| SURF004 | 發黑 | by_weight | 2.50 | kg | 20 | S50C,SPCC | 2025-01-01 | ACTIVE |
| SURF005 | 鍍鉻 | by_area | 0.50 | dm2 | 100 | S50C,SKD11 | 2025-01-01 | ACTIVE |
| SURF006 | 小件陽極 | by_piece | 5.00 | piece | 20 | A6061-T6 | 2025-01-01 | ACTIVE |

### 5.2 計價模式說明

| 模式 | 公式 | 適用 |
|---|---|---|
| by_weight | 單價 × 重量(kg) | 熱處理、發黑 |
| by_area | 單價 × 表面積(dm²) | 陽極、噴塗、鍍鉻 |
| by_piece | 單價 × 數量 | 小零件批次處理 |
| by_length | 單價 × 長度(m) | 線材處理 |

每種表面處理可以有多條記錄，涵蓋不同的 applicable_materials。

### 5.3 數據模型

```python
class SurfacePrice(BaseModel):
    """Surface treatment price record."""

    surface_id: str = Field(...)
    surface_name: str = Field(...)
    pricing_mode: str = Field(..., description="by_weight|by_area|by_piece|by_length")
    unit_price: float = Field(..., gt=0)
    unit: str = "kg"
    min_charge: float | None = None
    applicable_materials: str = ""    # Comma-separated material names
    effective_date: str | None = None
    status: str = "ACTIVE"

    price_version: str = "1.0"
    updated_at: str | None = None
```

---

## 六、Labor Price Model

### 6.1 Excel 格式 (labor-rates.xlsx)

人工費率用於非加工工序（裝配、調試、設計等）：

| labor_id | labor_type | rate | unit | applicable | effective_date | status |
|---|---|---|---|---|---|---|
| LAB001 | 機構設計 | 150 | hour | 非標設計 | 2025-01-01 | ACTIVE |
| LAB002 | 電控設計 | 150 | hour | — | 2025-01-01 | ACTIVE |
| LAB003 | 裝配調試 | 120 | hour | — | 2025-01-01 | ACTIVE |
| LAB004 | 現場安裝 | 200 | hour | 出差 | 2025-01-01 | ACTIVE |
| LAB005 | 鉗工 | 88 | hour | — | 2025-01-01 | ACTIVE |

### 6.2 數據模型

```python
class LaborPrice(BaseModel):
    """Labor rate record."""

    labor_id: str = Field(...)
    labor_type: str = Field(...)
    rate: float = Field(..., gt=0, description="CNY/hour")
    unit: str = "hour"
    applicable: str | None = None
    effective_date: str | None = None
    status: str = "ACTIVE"

    price_version: str = "1.0"
    updated_at: str | None = None
```

---

## 七、Process Time Rule Model

### 7.1 設計目標

工時規則與價格分離。工時由特徵決定，不是由價格決定。

### 7.2 工時估算規則 (process-times.xlsx)

| rule_id | feature_condition | process | base_time_min | time_unit | formula | note |
|---|---|---|---|---|---|---|
| TIME001 | hole_count>0 | CNC鑽孔 | 2 | per_hole | base × hole_count | 每個孔2分鐘 |
| TIME002 | volume<100000 | CNC粗加工 | 30 | fixed | base | 小零件固定30分鐘 |
| TIME003 | volume>=100000 | CNC粗加工 | 30 | per_100cm3 | base × (volume/100000) | 每100cm³加30分鐘 |
| TIME004 | surface=熱處理 | 熱處理 | 0 | — | — | 按重量計價 |
| TIME005 | always | 鉗工去毛刺 | 15 | fixed | base | 固定15分鐘 |

### 7.3 數據模型

```python
class ProcessTimeRule(BaseModel):
    """Estimated machining time based on feature conditions."""

    rule_id: str = Field(...)
    feature_condition: str = Field(..., description="When this rule applies")
    process_name: str = Field(...)
    base_time_min: float = Field(..., ge=0)
    time_unit: str = "fixed"      # fixed | per_hole | per_100cm3 | per_kg
    formula: str | None = None    # "base × hole_count"
    note: str | None = None

    version: str = "1.0"
    updated_at: str | None = None
```

---

## 八、Price Version Management

### 8.1 版本策略

```
價格變更時：
  1. 人員修改 Excel
  2. 執行匯入命令: quotation import-prices --source material-prices.xlsx
  3. 系統自動生成新版本號
  4. 舊版本歸檔保存（不可覆蓋）
  5. 新版本成為 ACTIVE
```

### 8.2 版本記錄模型

```python
class PriceVersionLog(BaseModel):
    """Immutable record of price changes."""

    version_id: str = Field(..., description="e.g. 'MAT-v1.2'")
    price_type: str = Field(..., description="material | process | surface | labor | time")
    version_number: str = "1.0"
    source_file: str                # Excel file that was imported
    imported_at: str                # ISO datetime
    imported_by: str = "SYSTEM"
    changes_summary: str            # Human-readable change description
    row_count: int = 0              # Number of price rows in this version
    previous_version: str | None = None
    is_active: bool = True
```

### 8.3 Quote 中的版本記錄

```python
# Quote 模型增加字段
class Quote(BaseModel):
    ...
    # Version tracking (added)
    rule_version: str | None = None        # quotation-rules.yaml version
    material_price_version: str | None = None
    process_price_version: str | None = None
    surface_price_version: str | None = None
    labor_price_version: str | None = None
    time_rule_version: str | None = None
```

### 8.4 版本追蹤鏈

```
報價單 (Quote)
  ├── rule_version: "1.1"
  ├── material_price_version: "MAT-v1.0"
  ├── process_price_version: "PROC-v1.0"
  ├── surface_price_version: "SURF-v1.0"
  └── effective_date: "2025-01-01"
        │
        ▼
  可追溯：這筆報價使用了哪個版本的價格
```

---

## 九、人員維護方式

### 9.1 Excel 維護（Phase 4，優先）

人員直接編輯 Excel 文件：

```
rules/
├── material-density.yaml       ← 物理屬性（極少變更，YAML即可）
├── material-prices.xlsx        ← 材料價格（人員Excel維護）
├── process-prices.xlsx         ← 加工價格
├── surface-prices.xlsx         ← 表面處理價格
├── labor-rates.xlsx            ← 人工費率
├── process-times.xlsx          ← 工時規則
└── price-versions/             ← 歷史版本歸檔（自動生成）
    ├── material-prices-v1.0.xlsx
    ├── material-prices-v1.1.xlsx
    └── ...
```

### 9.2 匯入命令（Phase 4）

```bash
# 匯入材料價格
quotation import-prices material --source rules/material-prices.xlsx

# 匯入所有價格
quotation import-prices all --source rules/

# 查看當前版本
quotation price-versions

# 回滾到指定版本
quotation price-versions --rollback MAT-v1.0
```

### 9.3 GUI 維護（Phase 5+，後續）

後續可開發簡單的設定界面：

- 表格顯示當前價格
- 雙擊編輯
- 儲存時自動版本管理
- 顯示變更歷史

---

## 十、與現有模塊的整合

```
Phase 1 Domain Models:
  domain/rule.py     ← MaterialRule, ProcessRule, SurfaceRule (保持)
  domain/pricing.py  ← [新增] MaterialPrice, ProcessPrice, SurfacePrice,
                              LaborPrice, ProcessTimeRule, PriceVersionLog

Phase 2 Knowledge Base:
  不變 — BOM 提供真實價格作為 H 來源

Phase 4 Rule Engine:
  rules/loader.py    ← 讀取 Excel → 生成 quotation-rules.yaml
  rules/validator.py ← 驗證價格有效性（no negative, no PENDING without note）
```

---

## 十一、禁止事項

| 禁止 | 原因 |
|---|---|
| 代碼中硬編碼 `price = 150` | 必須來自 Excel/YAML |
| 覆蓋歷史價格版本 | 舊版本歸檔保存 |
| 報價不記錄版本 | 無法追溯價格來源 |
| AI 直接修改價格 | AI 只能建議，人工確認後匯入 |
| Excel 欄位格式不一致 | 使用固定模板，驗證格式 |

---

## 十二、AI 價格來源整合 (Phase 7)

### 12.1 AI 不可修改正式規則

AI 產生的價格**永遠不能**直接寫入 `material-prices.xlsx` 或 `quotation-rules.yaml`。

流程：

```
AI → QuoteSuggestion(AI-EST/AI-WEB)
    → 人工確認 → M
    → 可選: 管理員手動加入 material-prices.xlsx → 發布 → C
```

### 12.2 價格來源在 Quote 中的記錄

每個 QuoteItem 標記來源：

```python
QuoteItem(
    category="surface",
    name="陽極氧化",
    amount=300.0,
    source=PriceSource.AI_EST,      # AI 估算
    rule_id=None,                    # 無正式規則
    ai_suggestion_id="sug-001",      # 關聯的 AI Suggestion
    evidence="AI估算: 基於5個相似A6061陽極氧化件",
    confidence=QuoteConfidence.LOW,
)
```

人工確認後：

```python
QuoteItem(
    source=PriceSource.M,            # 人工已確認
    rule_id=None,
    evidence="AI估算: ¥300, 人工確認: ¥350 (實際外發報價)",
)
```

詳見 `docs/ai-design.md`。


*本文件為 Phase 2 設計。AI 整合在 Phase 7 實施。*
