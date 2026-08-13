# 機構2D自動報價系統 — Domain Model 設計文件

日期：2026-08-01
版本：V1.0
階段：Phase 1.1

---

## 一、設計原則

1. **所有模型使用 Pydantic v2**，確保運行時型別驗證
2. **字段全部有型別註解**，可選字段用 `| None`
3. **價格相關字段**必須標註來源 (`PriceSource` 枚舉)
4. **模型之間通過 ID 關聯**，不直接持有對象引用
5. **序列化友好**：所有模型支持 `.model_dump()` 和 `.model_dump_json()`

---

## 二、通用型別與枚舉

### 2.1 共用枚舉

```python
from enum import Enum

class PriceSource(str, Enum):
    """價格來源 — 憲章 §6 定義"""
    C = "C"       # 公司規則確認價格
    H = "H"       # 歷史報價
    E = "E"       # 行業參考
    AI = "AI"     # AI 建議
    M = "M"       # 人工確認
    U = "U"       # 未知

class DrawingFormat(str, Enum):
    DXF = "DXF"
    DWG = "DWG"
    PDF = "PDF"

class ParseStatus(str, Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAILED = "failed"

class FeatureSource(str, Enum):
    CAD = "CAD"           # 從 CAD 解析
    BOM = "BOM"           # 從 BOM 提取
    BOTH = "BOTH"         # CAD + BOM 交叉驗證
    MANUAL = "MANUAL"     # 人工輸入

class MaterialStatus(str, Enum):
    ACTIVE = "ACTIVE"       # 可用
    PENDING = "PENDING"     # 待確認價格
    DEPRECATED = "DEPRECATED"

class SurfacePricingMode(str, Enum):
    BY_WEIGHT = "by_weight"    # 元/kg
    BY_AREA = "by_area"        # 元/dm²
    BY_PIECE = "by_piece"      # 元/件
    BY_LENGTH = "by_length"    # 元/m

class IssueSeverity(str, Enum):
    WARNING = "warning"
    ERROR = "error"
    UNKNOWN = "unknown"

class IssueStatus(str, Enum):
    OPEN = "open"
    IN_REVIEW = "in_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"

class QuoteConfidence(str, Enum):
    HIGH = "high"           # C 來源，規則精確匹配
    MEDIUM = "medium"       # H 來源，歷史相似
    LOW = "low"             # E 來源，行業推測
    UNCERTAIN = "uncertain" # AI/M 來源，需確認
```

### 2.2 共用值對象

```python
from pydantic import BaseModel, Field

class BoundingBox(BaseModel):
    """3D 邊界框"""
    min_x: float
    min_y: float
    min_z: float = 0.0
    max_x: float
    max_y: float
    max_z: float = 0.0

    @property
    def length(self) -> float: return self.max_x - self.min_x
    @property
    def width(self) -> float:  return self.max_y - self.min_y
    @property
    def height(self) -> float: return self.max_z - self.min_z

class Dimensions(BaseModel):
    """零件外形尺寸（結構化）"""
    length: float           # mm
    width: float            # mm
    height: float           # mm
    raw_text: str | None = None  # BOM 原始文字，如 "928*796*15"

class Hole(BaseModel):
    """孔特徵"""
    diameter: float               # mm
    center_x: float
    center_y: float
    depth: float | None = None    # 盲孔深度，貫穿為 None
    hole_type: str = "through"    # "through" | "blind" | "tapped" | "counterbore"
    thread_spec: str | None = None  # 螺紋規格，如 "M6"

class TextEntity(BaseModel):
    """CAD 文字實體"""
    content: str
    position_x: float
    position_y: float
    height: float
    layer: str | None = None

class CostBreakdown(BaseModel):
    """成本明細項"""
    category: str           # "material" | "process" | "surface" | "purchased" | "other"
    name: str               # 項目名稱
    quantity: float
    unit: str
    unit_price: float
    amount: float           # quantity × unit_price
    source: PriceSource
    rule_id: str | None = None
    evidence: str | None = None  # 計算依據
    confidence: QuoteConfidence = QuoteConfidence.MEDIUM
```

---

## 三、Drawing Model（圖紙實體）

### 3.1 定義

```python
# domain/drawing.py

class Drawing(BaseModel):
    """圖紙實體 — 對應一份 CAD 文件"""

    # -- 標識 --
    id: str = Field(..., description="唯一標識，生成 UUID")
    file_path: str = Field(..., description="來源文件絕對路徑")
    file_name: str = Field(..., description="文件名，含副檔名")

    # -- 來源 --
    source_format: DrawingFormat = Field(..., description="DXF | DWG | PDF")

    # -- 圖紙資訊（從圖框/標題欄提取） --
    drawing_number: str | None = None    # 圖號，如 "UC1000005854"
    part_name: str | None = None         # 零件名稱
    revision: str | None = None          # 版本
    material_text: str | None = None     # 原始材料標註文字
    scale: str | None = None             # 比例，如 "1:1"

    # -- CAD 實體 --
    entity_count: int = 0
    entity_summary: dict[str, int] = Field(default_factory=dict)
    # 例: {"LINE": 245, "CIRCLE": 12, "ARC": 8, "TEXT": 3, "POLYLINE": 4}

    # -- 文字內容 --
    all_texts: list[TextEntity] = Field(default_factory=list)
    raw_text_strings: list[str] = Field(default_factory=list)
    # 所有 TEXT/MTEXT 的純文字列表，用於材料、技術要求識別

    # -- 解析狀態 --
    parse_status: ParseStatus = ParseStatus.SUCCESS
    parse_errors: list[str] = Field(default_factory=list)
    parse_warnings: list[str] = Field(default_factory=list)

    # -- 關聯 --
    feature_id: str | None = None  # 關聯的 Feature

    model_config = {"json_schema_extra": {
        "example": {
            "id": "dwg-001",
            "file_path": "D:/drawings/UC1000005854-J003.DWG",
            "file_name": "UC1000005854-J003.DWG",
            "source_format": "DWG",
            "drawing_number": "UC1000005854",
            "part_name": "J003",
            "material_text": "S50C",
            "entity_count": 269,
            "entity_summary": {"LINE": 245, "CIRCLE": 12, "TEXT": 3, "ARC": 8, "POLYLINE": 1},
            "parse_status": "success"
        }
    }}
```

### 3.2 字段說明

| 字段 | 型別 | 必填 | 說明 | 來源 |
|---|---|---|---|---|
| `id` | str | ✅ | UUID | 系統生成 |
| `file_path` | str | ✅ | 文件路徑 | 文件系統 |
| `file_name` | str | ✅ | 文件名 | 文件系統 |
| `source_format` | DrawingFormat | ✅ | 格式枚舉 | 副檔名判斷 |
| `drawing_number` | str \| None | — | 圖號/料號 | 文件名提取或圖框文字 |
| `part_name` | str \| None | — | 零件名 | 圖框文字或文件名提取 |
| `revision` | str \| None | — | 版本 | 圖框文字 |
| `material_text` | str \| None | — | 材料標註 | TEXT/MTEXT 提取 |
| `entity_count` | int | — | 實體總數 | CAD Parser |
| `entity_summary` | dict | — | 各類實體數量 | CAD Parser |
| `all_texts` | list[TextEntity] | — | 文字實體 | CAD Parser |
| `parse_status` | ParseStatus | — | 解析結果 | CAD Parser |
| `feature_id` | str \| None | — | Feature 關聯 | Feature Extractor |

---

## 四、Feature Model（零件特徵）

### 4.1 定義

```python
# domain/feature.py

class Feature(BaseModel):
    """零件特徵 — 從 Drawing 提取的結構化製造資訊"""

    # -- 標識 --
    id: str = Field(..., description="唯一標識")
    drawing_id: str = Field(..., description="關聯的 Drawing.id")
    bom_ref: str | None = None           # 對應 BOM Item 編號

    # -- 外形尺寸 --
    bounding_box: BoundingBox | None = None
    overall_length: float = 0.0          # mm
    overall_width: float = 0.0           # mm
    overall_height: float = 0.0          # mm
    dimensions_raw: str | None = None    # BOM 原始尺寸文字

    # -- 體積與重量 --
    volume_mm3: float | None = None      # CAD 計算體積
    surface_area_mm2: float | None = None  # 表面積（用於噴塗計價）
    weight_kg: float | None = None       # 重量 = 體積 × 密度

    # -- 孔特徵 --
    holes: list[Hole] = Field(default_factory=list)
    hole_count: int = 0
    # 孔分類統計
    through_holes: int = 0
    blind_holes: int = 0
    tapped_holes: int = 0               # 螺紋孔

    # -- 螺紋 --
    threads: list[str] = Field(default_factory=list)  # 螺紋規格列表 ["M6", "M8"]

    # -- 輪廓 --
    contour_type: str | None = None     # "rectangular" | "circular" | "irregular"
    is_axisymmetric: bool = False       # 是否軸對稱（車削件判斷）

    # -- 材料（最終確認值） --
    material_text: str | None = None         # 原始文字
    material_normalized: str | None = None   # 標準化名稱，如 "A6061-T6"

    # -- 表面處理 --
    surface_text: str | None = None         # 原始文字
    surface_normalized: str | None = None   # 標準化名稱

    # -- 公差 --
    tolerances: list[str] = Field(default_factory=list)
    # 例: ["平面度 0.01", "Ra0.8"]
    has_tight_tolerance: bool = False       # 是否有精密公差 (<0.05mm)
    max_tolerance_grade: str | None = None  # "IT6", "IT7", etc.

    # -- 技術要求 --
    tech_requirements: list[str] = Field(default_factory=list)
    all_texts: list[TextEntity] = Field(default_factory=list)

    # -- 來源標記 --
    feature_source: FeatureSource = FeatureSource.CAD
    # 當 feature 數據來自 BOM（如尺寸）時標記為 BOM 或 BOTH

    model_config = {"json_schema_extra": {
        "example": {
            "id": "feat-001",
            "drawing_id": "dwg-001",
            "bom_ref": "UC1000005854",
            "overall_length": 928.0,
            "overall_width": 796.0,
            "overall_height": 15.0,
            "volume_mm3": 11070720.0,
            "surface_area_mm2": 1529376.0,
            "weight_kg": 86.91,
            "hole_count": 12,
            "through_holes": 8,
            "tapped_holes": 4,
            "threads": ["M6", "M8"],
            "contour_type": "rectangular",
            "material_text": "S50C",
            "material_normalized": "S50C",
            "surface_text": "熱處理",
            "surface_normalized": "熱處理",
            "tolerances": ["平面度 0.05"],
            "feature_source": "BOTH"
        }
    }}
```

### 4.2 重量計算邏輯（模型內實現）

```python
def calculate_weight(self, density_g_cm3: float) -> float | None:
    """從體積和材料密度計算重量 (kg)"""
    if self.volume_mm3 is None:
        return None
    # volume_mm3 ÷ 1000 = cm³, cm³ × density = g, g ÷ 1000 = kg
    return (self.volume_mm3 / 1000.0) * density_g_cm3 / 1000.0
```

### 4.3 字段說明

| 字段 | 型別 | 說明 | 來源 |
|---|---|---|---|
| `id` | str | UUID | 系統 |
| `drawing_id` | str | 關聯 Drawing | 系統 |
| `bom_ref` | str \| None | BOM Item 編號 | BOM 匹配 |
| `bounding_box` | BoundingBox \| None | 3D 邊界框 | CAD |
| `overall_length/width/height` | float | 外形尺寸 mm | CAD/BOM |
| `volume_mm3` | float \| None | 體積 | CAD計算 |
| `surface_area_mm2` | float \| None | 表面積（噴塗計價用） | CAD計算 |
| `weight_kg` | float \| None | 重量 | 體積×密度 |
| `holes` | list[Hole] | 孔列表 | CAD |
| `threads` | list[str] | 螺紋 | CAD/BOM文字 |
| `contour_type` | str \| None | 輪廓類型 | CAD |
| `material_normalized` | str \| None | 標準材料名 | 文字匹配 |
| `surface_normalized` | str \| None | 標準表面處理名 | 文字匹配 |
| `tolerances` | list[str] | 公差要求 | CAD文字 |
| `feature_source` | FeatureSource | 數據來源 | 系統標記 |

---

## 五、BOM Model（歷史報價條目）

### 5.1 定義

```python
# domain/bom.py

class BomEntry(BaseModel):
    """BOM 單行條目 — 對應 Excel 一行"""

    # -- 標識 --
    item: str = Field(..., description="零件號/料號，如 'UC1000005854'")
    description: str = Field(..., description="完整描述文字")

    # -- BOM 結構 --
    level: int = Field(default=0, ge=0, description="BOM 層級 0=成品 1=組件 2+=零件")
    parent_item: str | None = None     # 父項料號（用於樹狀結構）

    # -- 類型 --
    item_type: str = "Purchased"       # "Finished good" | "Subassembly" | "Purchased"
    uom: str = "ST"                    # 單位: ST/PCS/SET/KG/M

    # -- 數量 --
    quantity: float = 1.0

    # -- 價格（真實歷史數據） --
    unit_cost: float = 0.0             # 單價 (CNY)
    extended_cost: float = 0.0         # 總價 = quantity × unit_cost

    # -- 供應商 --
    supplier: str | None = None

    # -- 元數據 --
    bom_source_file: str | None = None # BOM 來源文件名
    notes: str | None = None           # 備註

    model_config = {"json_schema_extra": {
        "example": {
            "item": "UC1000005854",
            "description": "原物料;加工件;S50C;J003;928*796*15;熱處理",
            "level": 2,
            "item_type": "Purchased",
            "uom": "ST",
            "quantity": 1,
            "unit_cost": 1425.0,
            "extended_cost": 1425.0,
            "bom_source_file": "GCS-雙滑台打磨設備-BOM.xlsx"
        }
    }}


class ParsedPart(BaseModel):
    """從 BOM description 解析出的結構化零件數據"""

    bom_item: str = Field(..., description="BOM Item 編號")
    material: str | None = None            # "S50C", "A6061-T6", "SPCC"
    part_code: str | None = None           # "J003", "R001"
    dimensions_raw: str | None = None      # "928*796*15"
    surface_treatment: str | None = None   # "熱處理"
    category: str | None = None            # "加工件" | "採購件" | "鈑金件"
    unit_cost: float = 0.0
    # 關聯
    drawing_ref: str | None = None         # 匹配的 DWG 文件名
    feature_ref: str | None = None         # 匹配的 Feature.id


class BomSheet(BaseModel):
    """完整的 BOM 表"""

    source_file: str = Field(..., description="BOM Excel 文件路徑")
    sheet_name: str = "Sheet1"
    total_rows: int = 0
    project_name: str | None = None        # "GCS-雙滑台打磨設備"

    entries: list[BomEntry] = Field(default_factory=list)
    parsed_parts: list[ParsedPart] = Field(default_factory=list)

    # 統計
    total_cost: float = 0.0
    part_count: int = 0                    # 加工件數量
    purchased_count: int = 0               # 採購件數量

    # 交叉參照統計
    matched_drawings: int = 0              # 已匹配 DWG 的零件數
    unmatched_drawings: int = 0            # 未匹配的 DWG 數
```

### 5.2 BOM description 解析規則

```
"原物料;加工件;S50C;J003;928*796*15;熱處理"
   ↓        ↓      ↓     ↓       ↓        ↓
 category  type  material code dimensions surface

"原物料;採購件;鋁型材;40*40;圖號:W001;1300*1300*995"
   ↓        ↓      ↓      ↓       ↓         ↓
 category  type  material dims   code    extra_dims
```

### 5.3 字段說明

| 字段 | 型別 | 說明 |
|---|---|---|
| `item` | str | 零件號，系統主鍵 |
| `description` | str | 原始描述（分號分隔） |
| `level` | int | BOM 層級 |
| `unit_cost` | float | **真實成交價** — 回歸測試基準 |
| `extended_cost` | float | 總價 |
| `supplier` | str \| None | 供應商 |
| `ParsedPart.material` | str \| None | 解析出的材料 |
| `ParsedPart.part_code` | str \| None | 零件代碼 |
| `ParsedPart.dimensions_raw` | str \| None | 原始尺寸文字 |
| `ParsedPart.surface_treatment` | str \| None | 表面處理 |
| `ParsedPart.drawing_ref` | str \| None | DWG 文件名匹配 |

---

## 六、Rule Model（報價規則）

### 6.1 定義

```python
# domain/rule.py

class MaterialRule(BaseModel):
    """材料報價規則"""
    material_id: str = Field(..., description="唯一規則 ID，如 'MAT001'")
    material_name: str = Field(..., description="標準材料名，如 'A6061-T6'")
    aliases: list[str] = Field(default_factory=list)
    # 別名列表: ["6061", "AL6061", "6061-T6", "鋁6061"]

    # 價格
    unit_price: float = Field(..., gt=0, description="單價")
    unit: str = "kg"
    loss_rate: float = Field(default=0.05, ge=0, le=1, description="損耗率")

    # 狀態
    status: MaterialStatus = MaterialStatus.ACTIVE
    note: str | None = None

    # 版本
    version: str = "1.0"
    updated_at: str | None = None  # ISO datetime


class ProcessRule(BaseModel):
    """加工工序報價規則"""
    process_id: str = Field(..., description="如 'PROC_CNC'")
    process_name: str = Field(..., description="如 'CNC'")
    rate: float = Field(..., gt=0, description="每小時工費 (元/h)")
    unit: str = "hour"
    conditions: list[str] | None = None
    # 適用條件: ["普通三軸", "公差>0.05mm"]

    version: str = "1.0"


class SurfaceRule(BaseModel):
    """表面處理報價規則"""
    surface_id: str = Field(..., description="如 'SURF_ANODIZE'")
    surface_name: str = Field(..., description="如 '陽極氧化'")
    aliases: list[str] = Field(default_factory=list)
    # ["陽極", "anodize", "陽極處理"]

    pricing_mode: SurfacePricingMode = SurfacePricingMode.BY_WEIGHT
    unit_price: float = Field(..., gt=0)
    unit: str = "kg"
    min_charge: float | None = None       # 最低消費
    applicable_materials: list[str] = Field(default_factory=list)
    note: str | None = None

    version: str = "1.0"


class RuleSet(BaseModel):
    """完整規則集"""
    version: str = Field(..., description="規則集版本")
    source: str | None = None              # 規則來源說明
    updated_at: str | None = None

    materials: list[MaterialRule] = Field(default_factory=list)
    processes: list[ProcessRule] = Field(default_factory=list)
    surfaces: list[SurfaceRule] = Field(default_factory=list)

    # 元數據
    material_count: int = 0
    process_count: int = 0
    surface_count: int = 0

    def model_post_init(self, __context):
        self.material_count = len(self.materials)
        self.process_count = len(self.processes)
        self.surface_count = len(self.surfaces)
```

### 6.2 規則匹配邏輯（接口定義）

```python
# rules/matcher.py (Phase 4 實現)

def match_material(text: str, rule_set: RuleSet) -> MaterialRule | None:
    """
    從文字匹配材料規則。
    優先精確匹配 material_name，其次匹配 aliases。
    例: "6061鋁" → 匹配 A6061-T6 (alias "6061")
    """

def match_surface(text: str, rule_set: RuleSet) -> SurfaceRule | None:
    """
    從文字匹配表面處理規則。
    例: "表面噴砂陽極氧化銀色" → 匹配 陽極氧化 (alias "陽極")
    """

def match_process(feature: Feature, rule_set: RuleSet) -> list[ProcessRule]:
    """
    根據零件特徵匹配適用加工工序。
    例: 矩形 + 孔 → [CNC, 鉗工]
    """
```

### 6.3 字段說明

| Rule Model | 關鍵字段 | 說明 |
|---|---|---|
| MaterialRule | `material_id`, `aliases`, `unit_price`, `loss_rate`, `status` | PENDING 狀態的材料不計價 |
| ProcessRule | `process_id`, `rate` (元/h), `conditions` | 按工時計價 |
| SurfaceRule | `surface_id`, `pricing_mode`, `min_charge`, `applicable_materials` | 支持4種計價模式 |
| RuleSet | `version`, `materials[]`, `processes[]`, `surfaces[]` | 聚合根 |

---

## 七、Quote Model（報價單）

### 7.1 定義

```python
# domain/quote.py

class QuoteItem(BaseModel):
    """單個報價項目"""
    # 標識
    line_id: str = Field(..., description="行號 ID")

    # 項目
    category: str = Field(..., description="材料/加工/表面處理/外購/其他")
    name: str = Field(..., description="項目名稱")

    # 計算
    quantity: float = 1.0
    unit: str = "ST"
    unit_price: float = 0.0
    amount: float = 0.0               # quantity × unit_price

    # 來源與證據
    source: PriceSource = PriceSource.U
    rule_id: str | None = None         # 匹配的規則 ID
    bom_ref: str | None = None         # 參考的 BOM Item
    evidence: str | None = None        # 計算過程說明
    # 例: "928×796×15mm × 7.85g/cm³ = 86.9kg × 9元/kg = ¥782"

    # 信心度
    confidence: QuoteConfidence = QuoteConfidence.MEDIUM

    # 備註
    note: str | None = None


class Quote(BaseModel):
    """完整報價單"""
    id: str = Field(..., description="報價單 ID")
    drawing_id: str = Field(..., description="來源 Drawing.id")
    feature_id: str | None = None

    # 基本資訊
    part_number: str | None = None      # 零件號
    part_name: str | None = None        # 零件名稱
    material: str | None = None         # 材料
    quantity: int = 1                   # 報價數量

    # 報價項目
    items: list[QuoteItem] = Field(default_factory=list)

    # 彙總
    subtotal_material: float = 0.0      # 材料費小計
    subtotal_process: float = 0.0       # 加工費小計
    subtotal_surface: float = 0.0       # 表面處理費小計
    subtotal_purchased: float = 0.0     # 外購件費小計
    total: float = 0.0                  # 總價

    # 來源彙總
    source_summary: dict[str, float] = Field(default_factory=dict)
    # 例: {"C": 500.0, "H": 200.0, "U": 100.0}

    # 未知項數量
    unknown_count: int = 0              # source=U 的項目數

    # 元數據
    quoted_at: str | None = None        # ISO datetime
    quoted_by: str = "SYSTEM"

    def model_post_init(self, __context):
        """自動計算彙總"""
        for item in self.items:
            match item.category:
                case "material":  self.subtotal_material += item.amount
                case "process":   self.subtotal_process += item.amount
                case "surface":   self.subtotal_surface += item.amount
                case "purchased": self.subtotal_purchased += item.amount

        self.total = (self.subtotal_material + self.subtotal_process +
                      self.subtotal_surface + self.subtotal_purchased)

        # 來源彙總
        summary: dict[str, float] = {}
        for item in self.items:
            key = item.source.value
            summary[key] = summary.get(key, 0.0) + item.amount
        self.source_summary = summary

        self.unknown_count = sum(
            1 for item in self.items if item.source == PriceSource.U
        )
```

### 7.2 報價單與 BOM 的關聯

```
BomEntry (歷史成交價)
    │
    │ bom_ref 匹配
    ▼
Quote (系統報價)
    │
    │ 對比驗證
    ▼
回歸測試: abs(Quote.total - BomEntry.unit_cost) / BomEntry.unit_cost ≤ 15%
```

### 7.3 字段說明

| 字段 | 型別 | 說明 |
|---|---|---|
| `items` | list[QuoteItem] | 報價明細行 |
| `total` | float | 總價（自動計算） |
| `source_summary` | dict[str, float] | 各來源金額彙總 |
| `unknown_count` | int | 未知項數量（需人工確認） |
| `QuoteItem.source` | PriceSource | 該項價格來源 |
| `QuoteItem.evidence` | str \| None | 計算依據文字 |
| `QuoteItem.confidence` | QuoteConfidence | 信心度 |

---

## 八、Issue Model（異常/未知項）

### 8.1 定義

```python
# domain/issue.py

class Issue(BaseModel):
    """報價過程中發現的異常項"""

    id: str = Field(..., description="唯一標識")
    drawing_id: str | None = None
    quote_id: str | None = None

    # 分類
    severity: IssueSeverity = IssueSeverity.WARNING
    category: str = Field(..., description="異常類別")
    # "material_unknown" | "process_unknown" | "surface_unknown"
    # | "dimension_missing" | "rule_missing" | "price_uncertain"
    # | "parse_error" | "no_match" | "ambiguous_material"

    # 內容
    title: str = Field(..., description="簡短標題")
    description: str = Field(..., description="詳細描述")
    raw_input: str | None = None       # 觸發異常的原始輸入

    # AI 輔助（Phase 5）
    ai_suggestion: str | None = None   # AI 推薦方案
    ai_confidence: float | None = None # AI 信心度 0-1

    # 人工確認
    status: IssueStatus = IssueStatus.OPEN
    resolution: str | None = None      # 人工解決方案
    resolved_by: str | None = None
    resolved_at: str | None = None

    # 元數據
    created_at: str | None = None


class IssueReport(BaseModel):
    """單次報價的異常彙總"""
    quote_id: str
    issues: list[Issue] = Field(default_factory=list)

    total_issues: int = 0
    error_count: int = 0
    warning_count: int = 0
    unknown_count: int = 0
    resolved_count: int = 0

    def model_post_init(self, __context):
        self.total_issues = len(self.issues)
        self.error_count = sum(1 for i in self.issues if i.severity == IssueSeverity.ERROR)
        self.warning_count = sum(1 for i in self.issues if i.severity == IssueSeverity.WARNING)
        self.unknown_count = sum(1 for i in self.issues if i.severity == IssueSeverity.UNKNOWN)
        self.resolved_count = sum(1 for i in self.issues if i.status == IssueStatus.RESOLVED)
```

### 8.2 Issue 類別枚舉

| category | 觸發條件 | 處理 |
|---|---|---|
| `material_unknown` | 材料文字無法匹配任何 MaterialRule | 標記 U，AI 建議候選 |
| `process_unknown` | 無法判斷所需加工工序 | 標記 U，記錄到未知項 Sheet |
| `surface_unknown` | 表面處理文字無法匹配 SurfaceRule | 標記 U |
| `dimension_missing` | CAD 無法提取尺寸，BOM 也無數據 | 標記 ERROR |
| `rule_missing` | 材料規則存在但 status=PENDING | 標記 U，提示等待價格 |
| `price_uncertain` | 多個規則候選，無法確定 | 標記 AI/M |
| `parse_error` | DXF 解析異常 | 標記 ERROR |
| `no_match` | DWG 無 BOM 對應，無規則命中 | 標記 U |
| `ambiguous_material` | 材料文字有多個可能匹配 | 標記 AI/M |

---

## 九、模型關聯圖

```
┌─────────────┐     1:1     ┌─────────────┐
│   Drawing   │────────────▶│   Feature   │
│             │              │             │
│ drawing_num │              │ bounding_box│
│ file_path   │              │ holes[]     │
│ format      │              │ weight_kg   │
│ texts[]     │              │ material    │
│ parse_status│              │ surface     │
└─────────────┘              └──────┬──────┘
                                    │
                          bom_ref   │  1:1 (可選)
                                    ▼
┌─────────────┐              ┌─────────────┐
│  BomSheet   │              │  RuleSet    │
│             │    N:1       │             │
│ entries[]   │◀────────────│ materials[] │
│ parsed[]    │  匹配料號    │ processes[] │
│ total_cost  │              │ surfaces[]  │
└──────┬──────┘              └──────┬──────┘
       │                            │
       │ bom_ref                    │ rule_id
       ▼                            ▼
┌─────────────────────────────────────────┐
│                 Quote                    │
│                                          │
│  items: [                               │
│    {category, amount, source, evidence}  │
│  ]                                       │
│  total, source_summary, unknown_count    │
└────────────────────┬────────────────────┘
                     │
                     │ quote_id
                     ▼
┌─────────────────────────────────────────┐
│              IssueReport                │
│  issues: [{severity, category, status}] │
└─────────────────────────────────────────┘
```

---

## 十、數據流範例（以 UC1000005854-J003 為例）

### Step 1: Drawing 創建

```json
{
  "id": "dwg-j003",
  "file_path": "samples/drawings/UC1000005854-J003.DWG",
  "file_name": "UC1000005854-J003.DWG",
  "source_format": "DWG",
  "drawing_number": "UC1000005854",
  "part_name": "J003",
  "material_text": "S50C",
  "parse_status": "success"
}
```

### Step 2: Feature 提取

```json
{
  "id": "feat-j003",
  "drawing_id": "dwg-j003",
  "bom_ref": "UC1000005854",
  "overall_length": 928.0,
  "overall_width": 796.0,
  "overall_height": 15.0,
  "volume_mm3": 11070720.0,
  "weight_kg": 86.91,
  "material_normalized": "S50C",
  "surface_normalized": "熱處理",
  "feature_source": "BOTH"
}
```

### Step 3: BOM 匹配

```json
{
  "item": "UC1000005854",
  "unit_cost": 1425.0,
  "parsed": {
    "material": "S50C",
    "part_code": "J003",
    "dimensions_raw": "928*796*15",
    "surface_treatment": "熱處理"
  }
}
```

### Step 4: Rule 匹配與計算

```
材料費: 86.91 kg × 9 元/kg × 1.05(損耗) = ¥821    [source=C, MAT_S50C]
熱處理: 86.91 kg × 11 元/kg = ¥956                [source=C, SURF_HEAT]
CNC加工: 2h × 80 元/h = ¥160                       [source=C, PROC_CNC]

系統報價: ¥1,937
BOM 真實價: ¥1,425
偏差: +36% → 需要調整規則或工時估算
```

### Step 5: Issue（如有未匹配項）

```json
{
  "severity": "warning",
  "category": "price_uncertain",
  "title": "系統報價與歷史價格偏差 >15%",
  "description": "J003: 系統計算 ¥1,937 vs BOM ¥1,425 (偏差 +36%)",
  "status": "open"
}
```

---

*本文件為 Phase 1.1 產出。Phase 1.2 將據此實現 Pydantic 模型。*

---

## 十一、HistoricalFeature Model（Phase 2 新增）

### 11.1 定位

`HistoricalFeature` 是從 BOM + DWG + 真實報價 中提取的歷史零件知識條目。

它不是報價流程的輸入，而是**歷史知識庫的存儲單元**。

建立流程：

```
BOM Excel (真實價格)
    +
DWG 文件 (幾何數據)
    +
人工報價 (驗證)
    │
    ▼
ParsedPart (BOM 結構化)
    +
Feature (CAD 特徵)
    │
    ▼
HistoricalFeature (合併)
    │
    ▼
quotation_history.db (SQLite)
```

使用流程：

```
客戶 PDF/DWG
    │
    ▼
Feature Extractor → Feature
    │
    ▼
Similarity Search ← quotation_history.db
    │ (材料 + 尺寸 + 表面處理 相似度匹配)
    ▼
HistoricalFeature[] (最相似的 N 件歷史零件)
    │
    ▼
Rule Engine → Quote
    │ (歷史價格作為 H 來源參考)
```

### 11.2 定義

```python
# domain/historical.py (Phase 2)

class HistoricalFeature(BaseModel):
    """A historical part record for knowledge base and similarity search."""

    # -- Identity --
    id: str = Field(..., description="Unique record ID (UUID)")

    # -- Part identifiers --
    part_no: str = Field(..., description="Part/drawing number, e.g. 'UC1000005854'")
    part_code: str | None = Field(default=None, description="Part code, e.g. 'J003'")
    part_name: str | None = Field(default=None)

    # -- Material --
    material: str | None = Field(default=None, description="Normalized material name")
    material_raw: str | None = Field(default=None, description="Original material text")

    # -- Dimensions --
    overall_length: float = 0.0      # mm
    overall_width: float = 0.0       # mm
    overall_height: float = 0.0      # mm
    dimensions_raw: str | None = None  # Original text

    # -- Weight --
    weight_kg: float | None = None
    volume_mm3: float | None = None

    # -- Features --
    hole_count: int = 0
    thread_specs: list[str] = Field(default_factory=list)
    contour_type: str | None = None

    # -- Surface treatment --
    surface_treatment: str | None = None
    surface_raw: str | None = None

    # -- Process hint --
    process_hint: str | None = None   # "CNC+熱處理" / "車削+陽極"
    tolerance_grade: str | None = None

    # -- Historical price (ground truth) --
    historical_price: float = 0.0         # CNY — 真實成交價
    price_source: str = "BOM"             # BOM | MANUAL | SUPPLIER
    price_date: str | None = None         # ISO date of quotation

    # -- Source tracing --
    source_bom: str | None = None         # BOM file path
    source_bom_row: int = 0               # BOM row number
    source_dwg: str | None = None         # DWG file name
    source_pdf: str | None = None         # PDF file name (if any)

    # -- Metadata --
    project_name: str | None = None       # "GCS-雙滑台打磨設備"
    created_at: str | None = None
    updated_at: str | None = None
```

### 11.3 與其他模型的關係

```
BomEntry ─────────────────────┐
    │ item, unit_cost          │
    ▼                          │
ParsedPart ────────────────────┤
    │ material, dims, surface  │
    ▼                          │
HistoricalFeature ◄────────────┘
    │
    │ 相似度匹配
    ▼
Feature (from CAD) ────→ Quote
```

### 11.4 相似度匹配接口（Phase 4）

```python
def find_similar(
    feature: Feature,
    db_path: str,
    top_n: int = 5,
) -> list[tuple[HistoricalFeature, float]]:
    """Find the top-N most similar historical parts.

    Similarity is computed as weighted combination of:
    - Material match (exact: +0.4, same category: +0.2)
    - Dimension similarity (volume ratio within ±30%: +0.3)
    - Surface treatment match (exact: +0.2)
    - Contour type match (same: +0.1)

    Returns list of (HistoricalFeature, similarity_score) sorted by score desc.
    """
    ...

class SimilarityResult(BaseModel):
    """A single similarity match result."""
    historical: HistoricalFeature
    score: float                        # 0.0 - 1.0
    match_details: dict[str, float]     # Breakdown by dimension
```

---

## 十二、歷史資料庫設計 (quotation_history.db)

### 12.1 SQLite Schema

```sql
-- 歷史零件主表
CREATE TABLE historical_parts (
    id TEXT PRIMARY KEY,
    part_no TEXT NOT NULL,
    part_code TEXT,
    part_name TEXT,

    -- Material
    material TEXT,
    material_raw TEXT,

    -- Dimensions
    overall_length REAL DEFAULT 0,
    overall_width REAL DEFAULT 0,
    overall_height REAL DEFAULT 0,
    dimensions_raw TEXT,

    -- Weight
    weight_kg REAL,
    volume_mm3 REAL,

    -- Features
    hole_count INTEGER DEFAULT 0,
    thread_specs TEXT,          -- JSON array
    contour_type TEXT,

    -- Surface
    surface_treatment TEXT,
    surface_raw TEXT,

    -- Process
    process_hint TEXT,
    tolerance_grade TEXT,

    -- Price
    historical_price REAL DEFAULT 0,
    price_source TEXT DEFAULT 'BOM',
    price_date TEXT,

    -- Source
    source_bom TEXT,
    source_bom_row INTEGER DEFAULT 0,
    source_dwg TEXT,
    source_pdf TEXT,

    -- Metadata
    project_name TEXT,
    created_at TEXT,
    updated_at TEXT
);

-- 相似度搜索索引
CREATE INDEX idx_historical_material ON historical_parts(material);
CREATE INDEX idx_historical_surface ON historical_parts(surface_treatment);
CREATE INDEX idx_historical_contour ON historical_parts(contour_type);
CREATE INDEX idx_historical_part_no ON historical_parts(part_no);
```

### 12.2 資料庫訪問接口（Phase 2）

```python
# infrastructure/database/repository.py

class HistoryRepository:
    """CRUD and search for historical parts."""

    def __init__(self, db_path: str): ...

    def insert(self, record: HistoricalFeature) -> str: ...
    def insert_batch(self, records: list[HistoricalFeature]) -> int: ...
    def get_by_part_no(self, part_no: str) -> HistoricalFeature | None: ...
    def get_all(self, limit: int = 100) -> list[HistoricalFeature]: ...

    # Phase 4
    def find_similar(
        self, feature: Feature, top_n: int = 5
    ) -> list[tuple[HistoricalFeature, float]]: ...

    def count(self) -> int: ...
    def materials_summary(self) -> dict[str, int]: ...
```

使用 SQLite 而非複雜數據庫：

| 選擇 | 理由 |
|---|---|
| SQLite | 零配置、單文件、無需服務器 |
| 單表設計 | 歷史零件特徵扁平化，便於相似度查詢 |
| JSON 字段 | thread_specs 等列表字段序列化存儲 |
| 索引 | material + surface + contour 三個查詢維度 |
