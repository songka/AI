# 機構2D自動報價系統 — 報價生命週期設計

日期：2026-08-01
版本：V1.0

---

## 一、報價生命週期

```
建立 (DRAFT)
    │
    ▼
快照 (SNAPSHOT)    ← 不可變記錄
    │
    ▼
審核 (REVIEW)
    │
    ├── 通過 ──→ 確認 (CONFIRMED)
    │
    └── 需修正 ──→ 修正 (CORRECTED)
                      │
                      ▼
                   重新快照 (SNAPSHOT)
                      │
                      ▼
                   確認 (CONFIRMED)
                      │
                      ▼
                   歸檔 (ARCHIVED)
```

---

## 二、Quote 狀態機

```python
class QuoteStatus(str, Enum):
    DRAFT = "draft"            # 系統自動生成，尚未審核
    SNAPSHOT = "snapshot"      # 不可變快照（凍結價格版本）
    REVIEW = "review"          # 人工審核中
    CORRECTED = "corrected"    # 人工修正後
    CONFIRMED = "confirmed"    # 確認可用
    ARCHIVED = "archived"      # 歸檔保存
    REJECTED = "rejected"      # 退回
```

### 狀態轉換規則

| 從 | 到 | 觸發 | 誰 |
|---|---|---|---|
| DRAFT | SNAPSHOT | 系統自動 | 系統 |
| SNAPSHOT | REVIEW | 人工打開審核 | 人 |
| REVIEW | CONFIRMED | 審核通過 | 人 |
| REVIEW | CORRECTED | 人工修正某項 | 人 |
| CORRECTED | SNAPSHOT | 重新凍結 | 系統 |
| SNAPSHOT | ARCHIVED | 長期保存 | 系統/人 |
| REVIEW | REJECTED | 退回 | 人 |

---

## 三、Quote Snapshot（報價快照）

### 3.1 設計目的

快照 = 不可變的報價版本記錄。確保：
- 同一張圖紙的不同版本報價可對比
- 價格版本凍結（不會因後續價格更新而改變歷史報價）
- 審計追溯

### 3.2 Snapshot 數據模型

```python
class QuoteSnapshot(BaseModel):
    """Immutable snapshot of a quote at a point in time."""

    snapshot_id: str = Field(..., description="Unique snapshot ID")
    quote_id: str = Field(..., description="Source Quote.id")

    # -- Frozen data (copied from Quote) --
    drawing_id: str
    part_number: str | None
    total: float                          # Frozen total
    source_summary: dict[str, float]      # Frozen source breakdown
    items: list[QuoteItem]                # Frozen items

    # -- Frozen price versions --
    quote_date: str                       # 報價日期
    material_price_version: str | None    # 凍結的材料價格版本
    process_price_version: str | None
    surface_price_version: str | None
    labor_price_version: str | None

    # -- Snapshot metadata --
    status: QuoteStatus = QuoteStatus.SNAPSHOT
    snapshot_at: str = Field(...)         # ISO datetime of snapshot
    snapshot_by: str = "SYSTEM"

    # -- Notes --
    notes: str | None = None
```

---

## 四、Drawing Revision（圖紙版本管理）

### 4.1 設計目的

同一零件可能有多個版本圖紙。每次圖紙變更需要重新報價。

### 4.2 Revision 模型

```python
class DrawingRevision(BaseModel):
    """Track drawing version changes."""

    drawing_id: str = Field(...)
    revision: str = Field(..., description="e.g. 'A', 'B', 'C'")
    revision_date: str | None = None
    change_description: str | None = None  # "增加M8螺紋孔"
    previous_revision: str | None = None   # "A"

class RevisionHistory(BaseModel):
    """All revisions of a drawing."""
    drawing_number: str
    revisions: list[DrawingRevision]
    latest_revision: str | None = None
```

### 4.3 圖紙變更流程

```
圖紙 Revision B
    │
    ▼
系統檢測: drawing_number 相同, revision 不同
    │
    ▼
生成新 Drawing + 新 Feature
    │
    ▼
重新報價 (新 Quote + 新 Snapshot)
    │
    ▼
RevisionHistory 記錄變更
```

---

## 五、Quote Confidence（信心度評分）

### 5.1 評分模型

```python
class ConfidenceScorer:
    """Score a quote's overall confidence based on source composition."""

    @staticmethod
    def score(quote: Quote) -> tuple[float, QuoteConfidence]:
        """
        Calculate overall confidence score (0.0 - 1.0).

        Weight per item:
          C source: 1.0
          H source: 0.8
          E source: 0.5
          AI source: 0.3
          M source: 0.7 (manual confirmation)
          U source: 0.0

        Overall = weighted average by amount.
        """
        ...

# Scoring thresholds:
#   >= 0.9  → HIGH
#   >= 0.6  → MEDIUM
#   >= 0.3  → LOW
#   < 0.3   → UNCERTAIN
```

### 5.2 信心度顯示

```
報價單 #Q001:
  材料費: ¥782  [C, HIGH]
  加工費: ¥160  [C, HIGH]
  表面處理: ¥0  [U, UNCERTAIN]  ← 需確認
  ─────────────────────
  總計: ¥942
  整體信心度: MEDIUM (0.72)
  未知項: 1
```

---

## 六、Correction Record（人工修正記錄）

### 6.1 設計目的

記錄每次人工修正，用於：
- 審計追溯
- 規則優化（頻繁修正的項 → 更新規則）
- AI 訓練資料

### 6.2 Correction 模型

```python
class CorrectionType(str, Enum):
    PRICE_CHANGE = "price_change"        # 修改了價格
    MATERIAL_CHANGE = "material_change"  # 修改了材料判斷
    SURFACE_CHANGE = "surface_change"    # 修改了表面處理
    PROCESS_CHANGE = "process_change"    # 修改了加工工序
    ADD_ITEM = "add_item"               # 增加了報價項目
    REMOVE_ITEM = "remove_item"         # 移除了報價項目
    OTHER = "other"

class CorrectionRecord(BaseModel):
    """A single human correction to a quote or quote item."""

    correction_id: str = Field(...)
    quote_id: str
    snapshot_id: str | None = None

    # What was changed
    correction_type: CorrectionType
    field_path: str                      # "items[0].unit_price"
    original_value: str                  # "0.0" (system value)
    corrected_value: str                 # "38.0" (human value)
    reason: str                          # "確認材料為A6061-T6，補入價格"

    # Who and when
    corrected_by: str = "UNKNOWN"
    corrected_at: str                    # ISO datetime

    # Impact
    price_impact: float = 0.0            # 金額變動

class CorrectionSummary(BaseModel):
    """Summary of corrections for a quote."""
    quote_id: str
    corrections: list[CorrectionRecord]
    total_corrections: int
    total_price_impact: float            # 總金額變動
```

---

## 七、Cost vs Selling Price（成本與售價分離）

### 7.1 設計目的

- **成本 (Cost)**：材料費+加工費+表面處理+外購件 = 實際生產成本
- **售價 (Selling Price)**：成本 + 利潤 + 管理費 + 風險溢價

系統計算的是成本，售價由人員設定利潤率。

### 7.2 數據模型

```python
class Quote(BaseModel):
    ...
    # -- Cost (系統計算) --
    subtotal_material: float     # 材料成本
    subtotal_process: float      # 加工成本
    subtotal_surface: float      # 表面處理成本
    subtotal_purchased: float    # 外購件成本
    total_cost: float            # 總成本

    # -- Selling Price (人工設定) --
    profit_rate: float = 0.15                  # 利潤率 15%
    management_fee: float = 0.0                # 管理費
    risk_premium: float = 0.0                  # 風險溢價
    selling_price: float | None = None         # 最終售價
    selling_price_set_by: str | None = None    # 誰設定的
    selling_price_set_at: str | None = None    # 設定時間

# 售價計算:
# selling_price = total_cost × (1 + profit_rate) + management_fee + risk_premium
```

---

## 八、Drawing Validation（圖紙完整性檢查）

### 8.1 檢查項目

```python
class DrawingValidationResult(BaseModel):
    """Result of drawing completeness validation."""

    drawing_id: str
    is_valid: bool

    checks: list[ValidationCheck]

class ValidationCheck(BaseModel):
    check_name: str           # "has_geometry" | "has_dimensions" | "has_material_text"
    passed: bool
    severity: str             # "error" | "warning"
    message: str

# 檢查清單:
# ✅ has_geometry          — 至少有 LINE/CIRCLE/ARC 實體
# ✅ has_boundary          — 可以計算邊界框
# ⚠️ has_material_text     — 圖紙中有材料標註文字
# ⚠️ has_surface_text      — 圖紙中有表面處理文字
# ⚠️ no_parse_errors       — 無解析錯誤
# ℹ️ entity_count_reasonable — 實體數量合理 (>10)
```

### 8.2 檢查時機

```
Drawing 解析完成後立即執行。
  ├── is_valid=False → parse_status=FAILED → 生成 ERROR Issue
  └── is_valid=True  → 進入 Feature Extraction
```

---

## 九、Feature Similarity（相似零件搜尋）

### 9.1 相似度計算

```python
class FeatureSimilarity:
    """Compute similarity between a Feature and HistoricalFeature."""

    @staticmethod
    def compute(feature: Feature, historical: HistoricalFeature) -> SimilarityResult:
        """
        Weighted similarity:
          material_match:     0.40  (exact=1.0, same_category=0.5, different=0.0)
          dimension_ratio:    0.30  (1 - |vol1-vol2|/max(vol1,vol2))
          surface_match:      0.20  (exact=1.0, different=0.0)
          contour_match:      0.10  (same=1.0, different=0.0)

        Returns SimilarityResult with total_score and breakdown.
        """
        ...

class SimilarityResult(BaseModel):
    historical: HistoricalFeature
    total_score: float           # 0.0 - 1.0
    material_score: float
    dimension_score: float
    surface_score: float
    contour_score: float
    match_details: dict[str, str]  # Human-readable explanation
```

### 9.2 搜尋接口

```python
class SimilaritySearch:
    """Search historical database for similar parts."""

    def __init__(self, db_path: str): ...

    def search(
        self,
        feature: Feature,
        top_n: int = 5,
        min_score: float = 0.3,
    ) -> list[SimilarityResult]:
        """
        Find top-N similar historical parts.
        Results with score >= 0.6 are used as H source quotes.
        Results with score 0.3-0.6 are listed as reference only.
        """
        ...
```

---

## 十、Supplier Database（供應商資料）

### 10.1 模型

```python
class Supplier(BaseModel):
    """A supplier/vendor record."""

    supplier_id: str
    name: str
    category: str              # "CNC加工" | "材料" | "表面處理" | "外購件"
    contact: str | None = None
    phone: str | None = None
    email: str | None = None

    # Default pricing
    default_markup: float = 0.0  # 默認加價率
    payment_terms: str | None = None
    lead_time_days: int | None = None

    status: str = "ACTIVE"

class SupplierQuote(BaseModel):
    """A quotation received from a supplier."""

    supplier_id: str
    part_no: str
    quoted_price: float
    quoted_at: str             # ISO date
    valid_until: str | None = None
    moq: int = 1               # Minimum order quantity
    notes: str | None = None
```

### 10.2 使用場景

```
規則引擎未命中 + 歷史庫無相似零件
    │
    ▼
查詢 SupplierQuote 表
    ├── 有供應商報價記錄 → source=E, confidence=LOW
    └── 無記錄 → source=U, 進入 AI 建議
```

---

## 十一、AI 價格來源擴展 (Phase 7)

### 11.1 完整來源枚舉

詳見 `docs/ai-design.md`。

| 來源 | 代碼 | 可直接報價? | 需人工確認? |
|---|---|---|---|
| 公司規則 | C | ✅ | ❌ |
| 歷史成交 | H | ✅ | ❌ |
| 行業規則 | E | ⚠️ | 建議 |
| AI查詢外部 | AI-WEB | ❌ | ✅ 必須 |
| AI特徵估算 | AI-EST | ❌ | ✅ 必須 |
| AI綜合 | AI-HYBRID | ❌ | ✅ 必須 |
| 人工確認 | M | ✅ | 已完成 |
| 未知 | U | ❌ | — |

### 11.2 AI Suggestion 整合

```
QuoteItem(source=U)
    │
    ▼
AI → QuoteSuggestion(AI-EST/AI-WEB)
    │
    ▼
人工確認 → M
    │
    ▼
CorrectionRecord (保存 AI 預測 vs 人工修改)
```

### 11.3 AI Feedback Record

每次 AI Suggestion 被人工審核後，保存反饋記錄：

```
AI Suggestion (¥300, AI-EST, c=0.68)
    │
    ▼
人工決策 → AIFeedbackRecord(
    ai_value=300,
    decision=MODIFIED,
    final_value=350,
    reason="實際外發報價為350",
    feedback_tags=["under_estimate"]
)
    │
    ▼
儲存到 SMB:/ai-feedback/ 供後續 AI 優化
```

### 11.4 AI-WEB 來源追蹤

所有 AI-WEB 查詢必須記錄原始來源：

```python
AIWebSource(
    source_url="https://example.com/market/A6061",
    source_type="market_price",
    extracted_value=38.50,
    confidence=0.70,
)
```

詳見 `docs/ai-design.md` §十一-A、§十一-B。

### 11.5 Excel 顯示要求

| 項目 | 金額 | 來源 | Confidence |
|---|---|---|---|
| 材料 | ¥782 | C | — |
| 加工 | ¥160 | H | — |
| 特殊工藝 | ¥300 | **AI-EST** | 0.68 |
| 表面處理 | ¥150 | **AI-WEB** | 0.55 |

顏色: C=綠, H=藍, AI-*=橙, M=灰, U=紅


*本文件為 Phase 2-7 設計。AI 整合在 Phase 7 實施。*
