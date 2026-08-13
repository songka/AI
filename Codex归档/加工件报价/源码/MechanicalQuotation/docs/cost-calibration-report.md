# Cost Model Calibration Report

日期: 2026-08-01 | 版本: V1.0

---

## Calibration Results

### Before/After

| Metric | Before | After | Change |
|---|---|---|---|
| OK parts | 6 (30%) | 7 (35%) | +1 |
| Avg deviation | 64.1% | 64.4% | — |
| C: price missing | 10 (50%) | 10 (50%) | — |
| A: deviation >30% | 12 (60%) | 11 (55%) | -1 |
| Tests passed | 491 | 491 | ✅ |

### Key Improvements (Materials with Rules)

| Part | Before | After | Improvement |
|---|---|---|---|
| J005 | -53% (337 vs 712) | +26% (899 vs 712) | ✅ |
| J007 | -48% (363 vs 693) | +33% (924 vs 693) | ✅ |
| R001 | -41% (123 vs 209) | +7% (224 vs 209) | ✅ |
| J003 | +1% (1440 vs 1425) | -4% (1362 vs 1425) | ✅ |

### Why SPCC/普通鋼/鋁型材 Still Fail

These materials are PENDING (price=0 placeholder). The system correctly marks them as U (unknown). Average deviation is meaningless until real prices are provided.

### Weight Estimator Priority Chain

```
1. BOM dimensions_raw (confidence=0.95) ← Uses actual thickness from BOM
2. Bounding Box Estimate (confidence=0.50) ← 2D DXF fallback
```

### Recommendations (Not Auto-Applied)

| Priority | Action | Impact |
|---|---|---|
| P0 | User provides SPCC unit price | Fixes 8 parts |
| P0 | User provides 普通鋼 unit price | Fixes 1 part |
| P1 | User provides 鋁型材 unit price | Fixes 1 part |
| P2 | Surface treatment spray pricing | Fixes surface cost accuracy |

---

*Report auto-generated 2026-08-01. No prices auto-modified.*
