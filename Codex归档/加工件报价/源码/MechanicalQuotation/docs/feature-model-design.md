# 機構2D自動報價系統 — Feature Model 設計 (Layer 2 & 3)

日期：2026-08-01
版本：V1.0

---

## 一、分層架構

```
Layer 1: RawEntity          (domain/raw_entity.py) ✅
    LINE, CIRCLE, ARC, POLYLINE, TEXT — raw CAD data

Layer 2: GeometricFeature    (domain/geometric_feature.py) [本階段]
    BoundingBox, HoleCandidate, TextCluster — 幾何分組

Layer 3: ManufacturingFeature (domain/manufacturing_feature.py) [本階段]
    Hole, Thread, Material, SurfaceTreatment — 加工語義

Layer 4: QuotationFeature    (Phase 4)
    MaterialRequirement, ProcessRequirement — 報價輸入
```

---

## 二、Layer 2: GeometricFeature

### BoundingBox

```python
class BoundingBox(BaseModel):
    min_x, min_y, max_x, max_y: float
    length, width: float
    source: str = "CAD_GEOMETRY"
    confidence: float = 0.98
    source_entities: list[str] = []  # RawEntity handles
```

來源：所有 LINE/POLYLINE 端點的最小/最大包圍盒。

### HoleCandidate

```python
class HoleCandidate(BaseModel):
    center_x, center_y: float
    diameter: float
    source_entity: str          # RawEntity handle
    confidence: float = 0.90
```

來源：直徑 < 30mm 的 CIRCLE（排除外形大圓）。
直徑 > 30mm → 可能是外形圓或沉孔，後續 Layer 3 處理。

### TextCluster

```python
class TextCluster(BaseModel):
    content: str
    position_x, position_y: float
    source_entity: str
```

來源：TEXT/MTEXT 實體。

---

## 三、Layer 3: ManufacturingFeature

所有欄位共用 `FeatureValue`：

```python
class FeatureValue(BaseModel):
    value: float | str | None = None
    source: str = "UNKNOWN"    # CAD_GEOMETRY | DRAWING_TEXT | INFERRED
    confidence: float = 0.0
    source_entities: list[str] = Field(default_factory=list)
```

### HoleFeature

```python
class HoleFeature(BaseModel):
    hole_id: str
    diameter: FeatureValue        # mm
    count: int                    # grouped count
    position_x: float | None
    position_y: float | None
    source_entities: list[str]    # CIRCLE handles
    confidence: float
```

### ThreadFeature

```python
class ThreadFeature(BaseModel):
    thread_id: str
    spec: FeatureValue            # "M6"
    size: str                     # "M6"
    count: int = 1
    depth: float | None = None
    linked_hole_id: str | None    # 關聯的 HoleFeature
    source_entities: list[str]    # TEXT handle + CIRCLE handle
    confidence: float
```

Thread Parser 支援：M3, M4, M5, M6, M8, M10
從 TEXT 中提取，並尋找附近的 CIRCLE (距離 < 螺紋標註高度的 5 倍)。

### MaterialFeature

```python
class MaterialFeature(BaseModel):
    material_id: str
    raw_text: FeatureValue        # 原始文字
    normalized: FeatureValue      # 標準化後 (S50C, A6061-T6...)
    source_entities: list[str]
    confidence: float
```

來源：TEXT/MTEXT → MaterialNormalizer → 標準化。

### SurfaceTreatmentFeature

```python
class SurfaceTreatmentFeature(BaseModel):
    surface_id: str
    raw_text: FeatureValue
    normalized: FeatureValue | None
    source_entities: list[str]
    confidence: float
```

來源：TEXT/MTEXT 中的表面處理關鍵詞。

---

## 四、Extractor 接口

```python
# infrastructure/feature/

class GeometricExtractor:
    """RawEntity[] → GeometricFeature[]"""

    def extract(self, entities: list[RawEntity]) -> GeometricFeatures:
        ...

class GeometricFeatures(BaseModel):
    bounding_box: BoundingBox | None
    hole_candidates: list[HoleCandidate]
    text_clusters: list[TextCluster]


class ManufacturingExtractor:
    """GeometricFeatures → ManufacturingFeatures"""

    def extract(self, geo: GeometricFeatures) -> ManufacturingFeatures:
        ...

class ManufacturingFeatures(BaseModel):
    holes: list[HoleFeature]
    threads: list[ThreadFeature]
    material: MaterialFeature | None
    surface_treatment: SurfaceTreatmentFeature | None
    bounding_box_mm: BoundingBox | None
```

---

## 五、CAD Golden Dataset 驗證

使用 Phase 2 的 20 件 Golden Dataset，驗證：

| # | 測試 | 預期 |
|---|---|---|
| F1 | BoundingBox 尺寸 | ±10% of Golden dimensions |
| F2 | 材料文字存在 | TEXT 中包含材料關鍵詞 |
| F3 | 表面處理文字存在 | TEXT 中包含表面處理關鍵詞 |
| F4 | 孔數量 | > 0 (加工件都有孔) |

---

*本文件為 Phase 3.1 設計。*
