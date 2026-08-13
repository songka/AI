# 機構2D自動報價系統 — 特徵提取設計

日期：2026-08-01
版本：V1.1（Phase 3 設計約束更新）

---

## 〇、CAD 解析分層架構

報價邏輯**禁止**直接依賴 CAD Entity。必須經過四層轉換：

```
Layer 1: Raw CAD Entity (ezdxf)
         LINE, CIRCLE, ARC, POLYLINE, TEXT, MTEXT
              │
              ▼
Layer 2: Geometric Feature
         BoundingBox, CircleGroup, LineChain, TextCluster
         (純幾何，無製造語義)
              │
              ▼
Layer 3: Manufacturing Feature
         Hole, Thread, Slot, Step, Chamfer, Fillet, MachiningSurface
         (加工語義，含 source + confidence)
              │
              ▼
Layer 4: Quotation Feature
         MaterialRequirement, ProcessRequirement, SurfaceRequirement
         (報價輸入，直接對應 Rule Engine)
```

### 依賴規則

| 層 | 可依賴 | 禁止依賴 |
|---|---|---|
| Layer 4 (Quotation) | Layer 3 | Layer 1, Layer 2 |
| Layer 3 (Manufacturing) | Layer 2 | Layer 1 |
| Layer 2 (Geometric) | Layer 1 | — |
| Layer 1 (Raw CAD) | ezdxf | 所有上層 |

---

## 一、特徵來源優先級

當同一特徵有多個來源時，按以下優先級合併：

| 優先級 | 來源 | 說明 | Confidence 基線 |
|---|---|---|---|
| **1** | `BOM` | BOM Excel 結構化數據 | 0.95 |
| **2** | `TITLE_BLOCK` | DWG 圖框屬性 (Author, Title, Material) | 0.90 |
| **3** | `DRAWING_TEXT` | TEXT/MTEXT 實體內容 | 0.80 |
| **4** | `CAD_GEOMETRY` | 從幾何實體測量計算 | 0.85 |
| **5** | `OCR` | 掃描 PDF OCR 結果 | 0.50 |
| **6** | `AI` | AI 模型推論 | 0.40 |
| **7** | `INFERRED` | 從其他特徵推論 | 0.30 |

### 合併規則

```python
def merge_feature_value(sources: list[FeatureValue]) -> FeatureValue:
    """Select the highest-priority source with confidence >= threshold."""
    priority_order = ["BOM", "TITLE_BLOCK", "DRAWING_TEXT", "CAD_GEOMETRY", "OCR", "AI", "INFERRED"]
    for source in priority_order:
        match = next((v for v in sources if v.source == source and v.confidence >= 0.3), None)
        if match:
            return match
    return FeatureValue(source="UNKNOWN", confidence=0.0)
```

---

## 二、從幾何特徵到加工特徵

```
幾何 Entity              加工特徵              報價影響
─────────────────────    ─────────────────     ──────────
CIRCLE (小直徑)     →    孔 (through/blind)  → 鑽孔工時
CIRCLE + TEXT "M6"  →    螺紋孔              → 攻牙工時
CIRCLE (大直徑)     →    沉孔                → 銑孔工時
LINE (閉合矩形)     →    槽                  → 銑槽工時
LINE (平行面)       →    台階                → 多面加工
LINE (相交角)       →    倒角/圓角           → 去毛刺
多個 LINE            →    外形輪廓            → 材料費 (bounding box)
LINE (封閉邊界)     →    加工面              → 表面積計算
TEXT                →    材料/技術要求        → 材料+表面處理
```

---

## 三、加工特徵模型

### 3.1 所有特徵共用格式

```python
class FeatureValue(BaseModel):
    """A feature measurement with source and confidence."""
    value: float | str | None = None
    source: str = "UNKNOWN"    # BOM|TITLE_BLOCK|DRAWING_TEXT|CAD_GEOMETRY|OCR|AI|INFERRED
    confidence: float = 0.0    # 0.0 - 1.0
```

### 3.2 孔 (Hole) — 完整版

```python
class HoleType(str, Enum):
    THROUGH_HOLE = "THROUGH_HOLE"        # 貫穿孔
    BLIND_HOLE = "BLIND_HOLE"            # 盲孔
    COUNTERBORE = "COUNTERBORE"          # 沉頭孔
    COUNTERSINK = "COUNTERSINK"          # 錐形沉孔
    THREAD = "THREAD"                    # 螺紋孔

class HoleFeature(BaseModel):
    """A hole detected from CAD geometry."""

    hole_id: str

    # -- Core --
    type: HoleType = HoleType.THROUGH_HOLE
    diameter: float = Field(..., gt=0)        # mm
    depth: float | None = None                # None = through
    position_x: float
    position_y: float
    quantity: int = 1                         # Same-type holes grouped

    # -- Thread (for THREAD type) --
    thread_spec: str | None = None            # "M6", "M8×1.25"
    thread_depth: float | None = None

    # -- Counterbore (for COUNTERBORE type) --
    cb_diameter: float | None = None
    cb_depth: float | None = None

    # -- Confidence --
    confidence: float = 0.0
    source: str = "CAD_GEOMETRY"

    # -- Process hint --
    process_hint: str | None = None           # "DRILL" | "TAP" | "REAM" | "BORE"
```

### 3.3 螺紋解析器 (Thread Parser)

支援格式：

| 輸入 | size | count | depth | spec |
|---|---|---|---|---|
| `M6` | M6 | 1 | — | M6 |
| `6-M6` | M6 | 6 | — | 6×M6 |
| `M6深10` | M6 | 1 | 10mm | M6×10 |
| `M8x1.25` | M8 | 1 | — | M8×1.25 |
| `M8×1.25深15` | M8 | 1 | 15mm | M8×1.25×15 |
| `4-M10深20` | M10 | 4 | 20mm | 4×M10×20 |

```python
class ThreadSpec(BaseModel):
    """Parsed thread specification from text."""

    raw_text: str                        # "6-M6深10"
    size: str                            # "M6"
    count: int = 1                       # 6
    depth: float | None = None           # 10.0
    pitch: float | None = None           # 1.25 (from M8x1.25)
    process_hint: str = "TAP"           # TAP | THREAD_MILL
    confidence: float = 0.0
    source: str = "DRAWING_TEXT"

class ThreadParser:
    """Parse thread specifications from CAD text."""

    # Pattern order matters — most specific first
    PATTERNS = [
        # 6-M6深10 or 4-M10深20
        (r"(\d+)\s*[-xX×]\s*M(\d+(?:[xX×]\d+(?:\.\d+)?)?)\s*深\s*(\d+(?:\.\d+)?)", "counted_depth"),
        # M6深10
        (r"M(\d+(?:[xX×]\d+(?:\.\d+)?)?)\s*深\s*(\d+(?:\.\d+)?)", "depth_only"),
        # 6-M6
        (r"(\d+)\s*[-xX×]\s*M(\d+(?:[xX×]\d+(?:\.\d+)?)?)", "counted"),
        # M8x1.25 or M6
        (r"M(\d+(?:[xX×]\d+(?:\.\d+)?)?)", "basic"),
    ]

    def parse(self, text: str) -> ThreadSpec | None: ...
```

### 3.4 沉孔 (Counterbore/Countersink)

```python
class CounterboreFeature(BaseModel):
    cb_id: str
    cb_type: str                     # "COUNTERBORE" | "COUNTERSINK"
    pilot_diameter: float
    pilot_depth: float | None
    cb_diameter: float
    cb_depth: float | None
    cb_angle: float | None = None   # Countersink angle (82°/90°)
    source_hole_id: str | None = None
    confidence: float = 0.0
    source: str = "CAD_GEOMETRY"
```

### 3.5 槽 (Slot)

```python
class SlotFeature(BaseModel):
    slot_id: str
    length: float
    width: float                    # = cutter diameter
    depth: float | None
    orientation_deg: float = 0.0
    slot_type: str = "open"         # "open" | "closed" | "t-slot"
    confidence: float = 0.0
    source: str = "CAD_GEOMETRY"
```

### 3.6 台階 (Step)

```python
class StepFeature(BaseModel):
    step_id: str
    face_count: int = 1
    max_depth: float = 0.0
    requires_flip: bool = False     # 需要翻面加工
    confidence: float = 0.0
    source: str = "CAD_GEOMETRY"
```

### 3.7 倒角 (Chamfer)

```python
class ChamferFeature(BaseModel):
    chamfer_id: str
    size: float                     # C1 = 1.0
    angle_deg: float = 45.0
    total_length_mm: float = 0.0
    confidence: float = 0.0
    source: str = "CAD_GEOMETRY"
```

### 3.8 圓角 (Fillet)

```python
class FilletFeature(BaseModel):
    fillet_id: str
    radius: float
    total_length_mm: float = 0.0
    confidence: float = 0.0
    source: str = "CAD_GEOMETRY"
```

### 3.9 加工面 (Machining Surface)

```python
class MachiningSurface(BaseModel):
    surface_id: str
    area_mm2: float
    surface_finish: str | None = None    # "Ra0.8"
    flatness: str | None = None          # "平面度 0.01"
    is_critical: bool = False
    confidence: float = 0.0
    source: str = "CAD_GEOMETRY"
```

---

## 四、Feature Model 擴展（完整版）

```python
# domain/feature.py (Phase 3 擴展)

class Feature(BaseModel):
    """Extended feature model for manufacturing quotation."""

    # -- Existing (Phase 1) --
    id: str
    drawing_id: str
    bom_ref: str | None
    bounding_box: BoundingBox | None
    overall_length: float
    overall_width: float
    overall_height: float
    volume_mm3: float | None
    surface_area_mm2: float | None
    weight_kg: float | None
    material_text: str | None
    material_normalized: str | None
    surface_text: str | None
    surface_normalized: str | None
    tolerances: list[str]
    tech_requirements: list[str]
    feature_source: str

    # -- New (Phase 3) --
    holes: list[HoleFeature] = Field(default_factory=list)
    threads: list[ThreadSpec] = Field(default_factory=list)
    counterbores: list[CounterboreFeature] = Field(default_factory=list)
    slots: list[SlotFeature] = Field(default_factory=list)
    steps: list[StepFeature] = Field(default_factory=list)
    chamfers: list[ChamferFeature] = Field(default_factory=list)
    fillets: list[FilletFeature] = Field(default_factory=list)
    machining_surfaces: list[MachiningSurface] = Field(default_factory=list)

    # -- Summary counts --
    hole_total: int = 0
    thread_total: int = 0
    slot_total: int = 0
    step_count: int = 1

    # -- Extraction metadata --
    extraction_confidence: float = 0.0
    extraction_warnings: list[str] = Field(default_factory=list)
```

---

## 五、特徵提取流程

```
Drawing.entities[] (Layer 1)
        │
        ▼
[Entity Classifier] → Layer 2: Geometric Features
  CIRCLE → CircleGroup (center, radius)
  LINE → LineChain (connected lines)
  TEXT → TextCluster (content, position)
        │
        ▼
[Pattern Recognizer] → Layer 3: Manufacturing Features
  小 CIRCLE (φ<20) → HoleFeature
  CIRCLE + TEXT "M*" → ThreadSpec
  同心 CIRCLE → CounterboreFeature
  平行 LINE (長/寬>2) → SlotFeature
  45° 短 LINE → ChamferFeature
  ARC (內角) → FilletFeature
  最外層 POLYLINE → BoundingBox → 外形
        │
        ▼
[Feature Builder] → Layer 4: Quotation Features
  Material (BOM > TITLE_BLOCK > TEXT)
  Surface Treatment (BOM > TEXT)
  Process Requirements (Inferred from features)
        │
        ▼
Feature Model (Layer 3 + Layer 4)
```

---

## 六、Confidence 評估

| 特徵 | 默認來源 | Confidence | 提升條件 |
|---|---|---|---|
| 孔直徑 | CAD_GEOMETRY | 0.95 | 標準鑽頭尺寸 → 0.98 |
| 螺紋規格 | DRAWING_TEXT | 0.85 | ThreadParser 精確匹配 → 0.95 |
| 沉孔 | CAD_GEOMETRY | 0.85 | 同心圓精確 → 0.95 |
| 槽 | CAD_GEOMETRY | 0.80 | 長>3×寬 → 0.90 |
| 倒角 | CAD_GEOMETRY | 0.75 | TEXT "C1" 確認 → 0.90 |
| 材料(TITLE_BLOCK) | TITLE_BLOCK | 0.90 | 匹配 Normalizer → 0.95 |
| 材料(TEXT) | DRAWING_TEXT | 0.80 | 匹配 Normalizer → 0.90 |
| 材料(BOM) | BOM | 0.95 | 直接匹配 → 1.0 |
| 表面處理(TEXT) | DRAWING_TEXT | 0.60 | 關鍵詞精確匹配 → 0.85 |
| 表面處理(BOM) | BOM | 0.95 | — |
| 外形尺寸 | CAD_GEOMETRY | 0.98 | — |

---

## 七、PDF Import 接口

### 7.1 策略

第一版優先實現 **Vector PDF 文字/線條解析**。OCR 作為低 confidence 來源後續加入。

### 7.2 接口定義

```python
# infrastructure/pdf/

class PdfImporter:
    """PDF import with layered confidence."""

    def import_pdf(self, file_path: str) -> ImportResult:
        """
        1. Detect PDF type (vector vs image)
        2. Vector: extract text via pdfminer/PyMuPDF
        3. Vector: extract line art (future)
        4. Image: OCR via Tesseract (future)
        5. Return ImportResult with source=OCR|DRAWING_TEXT
        """
        ...

    def detect_type(self, file_path: str) -> str:
        """Return 'vector' | 'image' | 'mixed'."""
        ...

    def extract_text_vector(self, file_path: str) -> list[TextEntity]:
        """Extract text from vector PDF. source=DRAWING_TEXT, confidence=0.70."""
        ...

    def extract_text_ocr(self, file_path: str) -> list[TextEntity]:
        """Extract text via OCR. source=OCR, confidence=0.50."""
        ...
```

### 7.3 PDF Confidence

```python
class PdfConfidence(str, Enum):
    HIGH = "high"          # 向量 PDF，文字可直接提取，confidence ≥ 0.70
    MEDIUM = "medium"      # 混合 PDF
    LOW = "low"            # 掃描 PDF，OCR 結果，confidence 0.40-0.60
    UNUSABLE = "unusable"  # 無法處理
```

---

## 八、CAD Golden Dataset

基於 Phase 2 的 20 件 Golden Dataset，擴充 CAD 預期值：

```json
{
  "dwg_file": "UC1000005854-J003.DWG",
  "cad_expected": {
    "entity_count_min": 50,
    "bounding_box": {"length": 928, "width": 796, "height": 15},
    "hole_count_min": 4,
    "text_entities_min": 1,
    "material_text_present": true,
    "circle_count_min": 4,
    "line_count_min": 20
  }
}
```

### CAD Golden Test 檢查項

| # | 測試 | 驗證 |
|---|---|---|
| C1 | DWG → DXF 轉換成功 | ODA exit code 0 |
| C2 | DXF 可解析 | ezdxf readfile 成功 |
| C3 | Entity 總數合理 | >= entity_count_min |
| C4 | Bounding box 正確 | ±5% of Golden dims |
| C5 | 孔數量 | >= hole_count_min |
| C6 | 文字提取 | 至少 1 個 TEXT/MTEXT |
| C7 | CIRCLE 數量 | >= circle_count_min |

---

## 九、禁止事項

| 禁止 | 原因 |
|---|---|
| 報價邏輯直接讀取 CIRCLE/LINE | 必須通過 ManufacturingFeature |
| 從圖片提取幾何尺寸 | 精度不足 |
| 假設所有 CIRCLE 都是孔 | 需區分孔 vs 外形圓 |
| Feature 值無 source 標記 | 必須可追溯 |
| OCR 結果直接作為報價依據 | source=OCR, confidence<0.7 |
| 跳過 TITLE_BLOCK | 圖框屬性優先級高於文字 |

---

*本文件為 Phase 3 設計 V1.1。Phase 3.0 開始編碼。*
