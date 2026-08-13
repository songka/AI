# 機構2D自動報價系統 — DWG/BOM 匹配管線設計

日期：2026-08-01
版本：V1.0

---

## 一、匹配管線

```
DWG 文件列表                    BOM ParsedPart 列表
      │                              │
      ▼                              ▼
Drawing Identifier Extractor    Part Index Builder
  (文件名→料號候選)              (part_no, material, dims)
      │                              │
      └──────────┬───────────────────┘
                 ▼
         Level 1: 精確匹配
         (文件名數字部分 ↔ BOM item)
                 │
         ┌───────┴───────┐
         ▼               ▼
      命中            未命中
         │               │
         ▼               ▼
    [MATCHED]     Level 2: 語義匹配
                  (part_code, material 比對)
                         │
                 ┌───────┴───────┐
                 ▼               ▼
              命中            未命中
                 │               │
                 ▼               ▼
            [MATCHED]     Level 3: 特徵匹配
                         (dimensions, material, surface)
                                 │
                         ┌───────┴───────┐
                         ▼               ▼
                    confidence≥0.6  confidence<0.6
                         │               │
                         ▼               ▼
                    [MATCHED]      [UNMATCHED]
                                   → Issue
```

---

## 二、三級匹配策略

### Level 1: 精確匹配（文件名 → BOM item）

| 方法 | 說明 |
|---|---|
| 文件名提取 | `UC1000005854-J003.DWG` → 數字部分 `1000005854` |
| BOM 查詢 | 在 BomSheet 中查找 item 包含該數字的條目 |
| 匹配條件 | 唯一命中 → MATCHED；多命中 → 降級到 L2 |

```python
def extract_candidate(filename: str) -> str | None:
    """UC1000005854-J003.DWG → '1000005854'"""
    import re
    m = re.search(r'UC(\d+)', filename)
    return m.group(1) if m else None
```

### Level 2: 語義匹配（part_code + material）

| 方法 | 說明 |
|---|---|
| part_code 匹配 | BOM 中 part_code（如 "J003"）與文件名中提取的代碼比對 |
| material 匹配 | BOM 中 material 與 DWG 相關聯的材料文字比對 |
| 加權評分 | part_code 匹配 +0.5, material 匹配 +0.5 |

### Level 3: 特徵匹配（dimensions + material + surface）

| 方法 | 說明 |
|---|---|
| 尺寸比對 | 長/寬/高公差 ±10% 內視為匹配 |
| 材料比對 | 材料名稱標準化後比對 |
| 表面處理比對 | 表面處理文字比對 |
| 加權評分 | dimensions 0.4 + material 0.4 + surface 0.2 |

---

## 三、MatchResult Model

```python
# domain/matching.py

class MatchLevel(str, Enum):
    LEVEL_1 = "L1"    # 精確匹配（文件名↔料號）
    LEVEL_2 = "L2"    # 語義匹配（part_code + material）
    LEVEL_3 = "L3"    # 特徵匹配（dimensions + material + surface）
    UNMATCHED = "UNMATCHED"

class MatchResult(BaseModel):
    """Result of matching one DWG file to BOM data."""

    # Source
    source_dwg: str = Field(..., description="DWG filename")
    dwg_candidate: str | None = Field(default=None, description="Extracted candidate number")

    # Match target
    matched_part: ParsedPart | None = Field(default=None, description="Matched BOM part")
    matched_bom_item: str | None = Field(default=None)

    # Match quality
    match_level: MatchLevel = MatchLevel.UNMATCHED
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    matched_by: str = Field(default="", description="What field(s) produced the match")
    evidence: str = Field(default="", description="Human-readable evidence")

    # Issues
    issues: list[str] = Field(default_factory=list)


class MatchReport(BaseModel):
    """Summary of all DWG↔BOM matching results."""

    total_dwg: int = 0
    total_bom_parts: int = 0

    l1_matched: int = 0
    l2_matched: int = 0
    l3_matched: int = 0
    unmatched: int = 0

    results: list[MatchResult] = Field(default_factory=list)
```

---

## 四、匹配引擎

```python
# infrastructure/parser/dwg_matcher.py

class DwgBomMatcher:
    """Three-level DWG→BOM matching engine."""

    def __init__(self, bom_parts: list[ParsedPart]): ...

    def match(self, dwg_filename: str) -> MatchResult:
        """Run three-level matching for a single DWG file."""
        ...

    def match_all(self, dwg_filenames: list[str]) -> MatchReport:
        """Match all DWG files and produce a report."""
        ...

    def get_unmatched(self) -> list[MatchResult]:
        """Get all unmatched DWG files."""
        ...
```

---

## 五、匹配檢查清單

每筆匹配完成後檢查：

| # | 檢查項 | 不通過處理 |
|---|---|---|
| 1 | candidate 提取成功 | → UNMATCHED |
| 2 | 唯一 BOM item 命中 | → 多命中降級 L2 |
| 3 | material 非空 | → WARNING issue |
| 4 | dimensions_raw 非空 | → WARNING issue |
| 5 | surface_treatment 非空 | → INFO |
| 6 | confidence ≥ 0.6 | → UNMATCHED + Issue |
| 7 | unit_cost > 0 | → WARNING (PENDING material) |
| 8 | is_quotable = True | → INFO（外購件標記） |
| 9 | 無多個 DWG 指向同一 BOM item | → WARNING (duplicate) |
| 10 | 無多個 BOM item 指向同一 DWG | → WARNING (ambiguous) |

---

## 六、禁止事項

| 禁止 | 正確做法 |
|---|---|
| 強制匹配低信心結果 | confidence < 0.6 → UNMATCHED |
| 文件名猜測材料 | 材料僅從 BOM description 獲取 |
| 忽略 Z 系列 | Z 系列 9 件必須標記 UNMATCHED |
| 匹配結果覆蓋 BOM 原始數據 | BOM 數據不可修改 |

---

*本文件為 Phase 2.3 設計。*
