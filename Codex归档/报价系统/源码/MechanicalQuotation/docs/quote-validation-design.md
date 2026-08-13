# Quote Calibration Design

日期: 2026-08-01 | 版本: V1.0

---

## 问题

| # | 问题 | 根因 |
|---|---|---|
| 1 | J003 weight=462kg vs 87kg expected | BBox uses `width*0.1` as thickness; DXF is 2D |
| 2 | W001 duplicate items (U+E for same material) | Material calc + Frame calc both generate items |
| 3 | Confidence=100% for all C-source items | No feature confidence integration |

## 修复

### 1. Weight Estimation

```python
class WeightSource(str, Enum):
    BOUNDING_BOX_ESTIMATE = "BOUNDING_BOX_ESTIMATE"  # L*W*H_estimate
    CAD_GEOMETRY_VOLUME = "CAD_GEOMETRY_VOLUME"        # actual CAD volume
    BOM_DIMENSIONS = "BOM_DIMENSIONS"                  # from BOM text
    MODEL_MASS = "MODEL_MASS"                          # from 3D model property

class WeightEstimate:
    value_kg: float
    source: WeightSource
    confidence: float  # BBOX=0.5, CAD=0.9, BOM=0.95
```

BBox estimate for 2D DXF: use `min(length, width) * 0.02` as thickness (plausible for plates).

### 2. Dedup

同一 QuotationFeature 只生成一次材料費。Material 和 Frame 的材料費來自不同路徑，應在 Quote Builder 中去重。

### 3. Confidence

```
overall = 0.4 * feature_confidence + 0.3 * price_source_weight + 0.3 * (1 - unknown_penalty)
```

### 4. Calibration Report

```python
class CalibrationReport:
    system_total: float
    historical_price: float | None
    deviation_pct: float | None
    items: list[QuoteItem]
    status: str  # "WITHIN_RANGE" | "OVER_ESTIMATE" | "UNDER_ESTIMATE" | "NO_REFERENCE"
```
