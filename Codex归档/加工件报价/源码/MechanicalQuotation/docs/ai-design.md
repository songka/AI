# 機構2D自動報價系統 — AI 輔助層設計

日期：2026-08-01
版本：V1.0

---

## 一、AI 定位

```
AI 不參與               AI 參與
─────────────          ─────────────
DWG/PDF 幾何解析       材料名稱標準化
孔數計算               技術備註理解
尺寸提取               工藝候選推薦
輪廓計算               AI 價格建議
正式規則計算           歷史案例解釋
                       外部資料整理
```

### 核心原則

| 原則 | 說明 |
|---|---|
| **AI 不是 CAD Parser** | 幾何解析必須由 ezdxf + ODA 完成 |
| **AI 不直接定價** | AI 輸出為 Suggestion，需人工確認後變 M |
| **AI 不可用不影響核心** | CAD解析 + 規則引擎 + 歷史查詢 獨立運作 |
| **已知 DeepSeek 限制** | DeepSeek 不支持圖片識別，不送圖片 |

---

## 二、價格來源擴展

### 2.1 完整來源枚舉

```python
class PriceSource(str, Enum):
    # -- 確定性來源（不需人工確認） --
    C = "C"              # 公司正式規則 (Company Rule)
    H = "H"              # 歷史成交價格 (Historical)

    # -- 參考性來源（需人工確認變 M） --
    E = "E"              # 行業規則 (Industry Rule)
    AI_WEB = "AI-WEB"    # AI 查詢外部資料後估算
    AI_EST = "AI-EST"    # AI 模型根據特徵估算
    AI_HYBRID = "AI-HYBRID"  # AI 綜合（歷史案例 + 規則 + 外部資料）

    # -- 人工 --
    M = "M"              # 人工確認 (Manual Confirm)

    # -- 未知 --
    U = "U"              # 未知 (Unknown)
```

### 2.2 來源可信度

| 來源 | 可信度 | 可直接用於報價? | 需人工確認? |
|---|---|---|---|
| C | 最高 | ✅ 是 | ❌ 否 |
| H | 高 | ✅ 是 | ❌ 否 (偏差<15%) |
| E | 中 | ⚠️ 標記來源 | 建議確認 |
| AI-HYBRID | 中 | ❌ 否 | ✅ 必須 |
| AI-WEB | 中低 | ❌ 否 | ✅ 必須 |
| AI-EST | 低 | ❌ 否 | ✅ 必須 |
| M | 高 (確認後) | ✅ 是 | ❌ 已完成 |
| U | 無 | ❌ 否 | — |

---

## 三、AI 價格資料結構

### 3.1 QuoteSuggestion

```python
class QuoteSuggestion(BaseModel):
    """An AI-generated price suggestion — never a final quote."""

    suggestion_id: str

    # Target
    quote_item_ref: str                # Which QuoteItem this suggests for

    # Value
    amount: float                      # Suggested price (CNY)
    source_level: str                  # "AI-WEB" | "AI-EST" | "AI-HYBRID"
    confidence: float = Field(ge=0.0, le=1.0)

    # Model info
    model: str                         # "DeepSeek" | "Mock"
    model_version: str | None = None

    # Context
    input_features: dict               # Feature data sent to AI
    reasoning: str                     # AI's explanation
    references: list[str] | None = None  # URLs or sources cited

    # Metadata
    created_at: str
    response_time_ms: float = 0.0
```

### 3.2 多個 Suggestion 合併

當同一 QuoteItem 有多個 Suggestion 時：

```python
def merge_suggestions(suggestions: list[QuoteSuggestion]) -> QuoteSuggestion:
    """Merge multiple AI suggestions into one AI-HYBRID."""
    if len(suggestions) == 1:
        return suggestions[0]
    return QuoteSuggestion(
        source_level="AI-HYBRID",
        amount=weighted_average([s.amount for s in suggestions],
                                [s.confidence for s in suggestions]),
        confidence=min(max(s.confidence for s in suggestions) + 0.05, 0.85),
        reasoning="; ".join(s.reasoning for s in suggestions),
        ...
    )
```

---

## 四、AI 報價流程

```
正式流程 (不需 AI):
  DWG/PDF → CAD Parser → Feature → Rule Engine → Quote (C/H source)

補充流程 (需要 AI):
  Feature
      │
      ▼
  Historical Search (quotation_history.db)
      │
      ├── 命中 (score≥0.7) → QuoteItem(source=H, confidence=MEDIUM)
      │
      └── 未命中 → AI 補充
                      │
                      ├── normalize_material()  → 材料標準化
                      ├── suggest_process()     → 工藝候選
                      ├── estimate_price()      → AI-EST 價格
                      ├── query_external()      → AI-WEB 價格
                      └── explain_quote()       → 歷史解釋
                      │
                      ▼
                  QuoteSuggestion (source=AI-EST|AI-WEB)
                      │
                      ▼
                  人工確認 → M
                      │
                      ├── 接受 → Quote 使用 AI 建議金額
                      └── 修改 → Correction Record
```

---

## 五、AI 使用場景

### 5.1 材料名稱標準化

```
輸入: "SUS-304", "304", "SUS304"
AI 輸出: { "normalized": "SUS304", "confidence": 0.95 }
```

MaterialNormalizer（Phase 2 已完成）處理常見別名。AI 處理 Normalizer 無法匹配的罕見材料名稱。

### 5.2 技術備註理解

```
輸入: "不得有刀紋", "銳角去毛刺", "Ra0.8"
AI 輸出: {
  "process_hints": ["deburring", "surface_finish"],
  "tolerance_grade": "Ra0.8",
  "confidence": 0.80
}
```

### 5.3 工藝候選推薦

```
輸入: { material: "SUS304", surface_finish: "Ra0.8", flatness: "0.01" }
AI 輸出: {
  "candidates": [
    {"process": "磨削", "confidence": 0.85},
    {"process": "精加工", "confidence": 0.70}
  ],
  "source": "AI-EST"
}
```

### 5.4 AI 價格建議

```
輸入: { material: "SUS304", weight_kg: 2.5, holes: 6, surface: "Ra0.8" }
AI 輸出: {
  "estimated_cost": 800,
  "breakdown": "材料~200 + CNC~400 + 磨削~200",
  "source_level": "AI-EST",
  "confidence": 0.68
}
```

### 5.5 歷史案例解釋

```
輸入: Feature + 相似案例 J003 (score=0.92)
AI 輸出: {
  "similarity_reason": "材料相同(S50C)、尺寸接近(928×796 vs 900×800)、表面處理一致(熱處理)",
  "price_reference": "J003 成交價 ¥1,425，建議參考",
  "confidence": 0.88
}
```

---

## 六、AI 外部資料查詢 (AI-WEB)

### 6.1 用途

| 查詢類型 | 說明 | 更新頻率 |
|---|---|---|
| 材料市場價格 | 當日 A6061/SUS304 行情 | 每次報價時 |
| 加工行情 | CNC/線割/放電 市場價 | 每週 |
| 表面處理行情 | 陽極/鍍鉻 外發價 | 每月 |
| 標準件價格 | 螺絲/軸承/氣缸 | 按需 |

### 6.2 限制

```
外部資料
    │
    ▼
AI 整理 → Suggestion (AI-WEB)
    │
    ▼
人工確認 → M
    │
    ├── 可選：加入正式規則 C
    │
    └── 禁止：外部資料直接覆蓋公司規則
```

---

## 七、AI Provider 接口

### 7.1 目錄結構

```
src/quotation/infrastructure/ai/
├── __init__.py
├── provider.py            # AIProvider 抽象接口
├── deepseek_provider.py   # DeepSeek 實現
├── mock_provider.py       # 測試用 Mock
└── suggestion_store.py    # QuoteSuggestion 持久化
```

### 7.2 抽象接口

```python
class AIProvider(ABC):
    """Abstract AI assistant — never a pricing authority."""

    @abstractmethod
    def normalize_material(self, text: str) -> NormalizationResult:
        """Normalize unknown material names. Returns with confidence."""
        ...

    @abstractmethod
    def analyze_tech_notes(self, notes: list[str]) -> list[ProcessHint]:
        """Parse technical notes into process hints."""
        ...

    @abstractmethod
    def suggest_process(self, feature: Feature) -> list[ProcessCandidate]:
        """Suggest machining processes based on features."""
        ...

    @abstractmethod
    def estimate_price(self, feature: Feature, similar: list[HistoricalFeature]) -> QuoteSuggestion:
        """Estimate price when no rule or history matches. source=AI-EST."""
        ...

    @abstractmethod
    def explain_similarity(self, feature: Feature, historical: HistoricalFeature, score: float) -> str:
        """Generate human-readable explanation for similarity match."""
        ...

    @abstractmethod
    def query_external_price(self, material: str, category: str) -> QuoteSuggestion | None:
        """Query external sources for market prices. source=AI-WEB."""
        ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @property
    @abstractmethod
    def is_available(self) -> bool: ...
```

### 7.3 DeepSeek Provider

```python
class DeepSeekProvider(AIProvider):
    """DeepSeek API — text-only, no image support."""

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self._api_key = api_key
        self._model = model

    @property
    def model_name(self) -> str:
        return f"DeepSeek/{self._model}"

    @property
    def is_available(self) -> bool:
        """Check API connectivity."""
        ...
```

---

## 八、AI 故障處理

### 8.1 降級策略

```
AI 調用
    │
    ├── 成功 → 返回 Suggestion
    │
    └── 失敗
         ├── 超時 (>10s) → 放棄該次調用
         ├── API 錯誤 (5xx) → 重試 1 次 → 仍失敗 → 放棄
         ├── 網路錯誤 → 不重試，標記 U
         └── 配額耗盡 → 標記 U，通知管理員
```

### 8.2 AI 不可用時

| 功能 | AI 不可用時的行為 |
|---|---|
| CAD 解析 | ✅ 完全不受影響 |
| 規則報價 | ✅ 完全不受影響 |
| 歷史查詢 | ✅ 完全不受影響 |
| 材料標準化 | ⚠️ 使用 Normalizer 規則庫（Phase 2 已完成） |
| 價格建議 | ❌ 標記 U，進入人工確認 |
| 工藝推薦 | ❌ 從規則庫推論（Rule Engine fallback） |

### 8.3 全局開關

```yaml
# config/ai.yaml
ai:
  enabled: false               # 默認關閉
  provider: "deepseek"
  timeout_seconds: 10
  max_retries: 1
  fallback_on_error: true      # AI 失敗不影響主流程
```

---

## 九、顯示要求

### 9.1 Excel 報價顯示

| 項目 | 金額 | 來源 | Confidence |
|---|---|---|---|
| 材料費 (S50C) | ¥782 | C | — |
| CNC 加工 | ¥160 | C | — |
| 熱處理 | ¥956 | H | — |
| 特殊工藝 | ¥300 | **AI-EST** | 0.68 |
| 表面處理 | ¥150 | **AI-WEB** | 0.55 |
| 未知項 | ¥0 | U | — |

### 9.2 顏色標記

| 來源 | 顏色 |
|---|---|
| C | 綠色 (確定) |
| H | 藍色 (參考) |
| AI-* | 橙色 (需確認) |
| M | 灰色 (已確認) |
| U | 紅色 (未知) |

---

## 十、人工確認整合

```
QuoteSuggestion (AI-EST, confidence=0.68)
        │
        ▼
人工審核
        │
   ┌────┴────┐
   ▼         ▼
 接受      修改
   │         │
   │         ▼
   │    CorrectionRecord(
   │      original: AI-EST ¥300,
   │      corrected: ¥350,
   │      reason: "實際外發價為350"
   │    )
   │         │
   └────┬────┘
        │
        ▼
   QuoteItem(source=M, amount=最終值)
        │
        ▼
   可選: 加入正式規則 C
   "此價格已驗證，加入材料規則"
```

---

## 十一-A、AI Feedback Record

### 用途

保存每次 AI Suggestion → 人工決策的完整記錄，用於後續 AI 模型優化。

### 數據模型

```python
class FeedbackDecision(str, Enum):
    ACCEPTED = "accepted"        # 完全接受 AI 建議
    MODIFIED = "modified"        # 接受但修改金額
    REJECTED = "rejected"        # 拒絕 AI 建議
    REPLACED = "replaced"        # 用其他來源替換

class AIFeedbackRecord(BaseModel):
    """Immutable record of human decision on AI suggestion."""

    feedback_id: str = Field(..., description="UUID")

    # Link to AI suggestion
    suggestion_id: str = Field(..., description="QuoteSuggestion.suggestion_id")
    quote_item_ref: str

    # AI values
    ai_value: float                      # AI 建議金額
    ai_source: str                       # "AI-EST" | "AI-WEB" | "AI-HYBRID"
    ai_confidence: float                 # AI 信心度
    ai_model: str                        # "DeepSeek"
    ai_reasoning: str | None = None      # AI 原始推理

    # Human decision
    decision: FeedbackDecision
    final_value: float                   # 最終使用的金額
    reason: str                          # 修改/拒絕原因（必填）
    corrected_by: str                    # user_id
    corrected_by_name: str              # "張三"

    # Metadata
    created_at: str
    quote_id: str | None = None          # 關聯的 Quote

    # For AI model improvement
    feedback_tags: list[str] = Field(default_factory=list)
    # ["over_estimate", "missing_surface_cost", "material_price_outdated"]
```

### 儲存

```
SMB:/ai-feedback/
├── FB-2026-0801-001.json
├── FB-2026-0801-002.json
└── ...

本地分析用:
C:\ProgramData\MechanicalQuotation\ai_feedback_cache.db
```

### 使用場景

```python
# 後續 AI 優化時
feedbacks = load_recent_feedback(days=90)
over_estimate_rate = sum(1 for f in feedbacks if "over_estimate" in f.feedback_tags) / len(feedbacks)
# → 調整 AI 估算參數
```

---

## 十一-B、AI-WEB 來源追蹤

### 問題

AI-WEB 從外部查詢價格，若不記錄來源，價格不可追溯。

### 數據模型

```python
class AIWebSource(BaseModel):
    """Traceable external data source for AI-WEB queries."""

    source_id: str = Field(..., description="UUID")

    # Source identification
    source_url: str = Field(..., description="查詢的 URL")
    source_type: str = Field(..., description="market_price | supplier_quote | industry_db")
    source_name: str = Field(..., description="網站/平台名稱")

    # Query context
    query_material: str | None = None
    query_category: str | None = None   # "material" | "process" | "surface"

    # Extracted data
    extracted_value: float              # 從頁面提取的價格
    extracted_unit: str = "CNY/kg"
    raw_response_snippet: str | None = None  # 原始回應摘要（截斷至500字）

    # Quality
    confidence: float = Field(ge=0.0, le=1.0)
    data_freshness: str | None = None   # "2026-08-01" (資料日期)

    # Metadata
    queried_at: str                     # ISO datetime

    # Link
    suggestion_id: str                  # 關聯的 QuoteSuggestion
```

### QuoteSuggestion 關聯

```python
class QuoteSuggestion(BaseModel):
    ...
    # Source tracing (required for AI-WEB)
    ai_web_sources: list[AIWebSource] = Field(default_factory=list)
    # 每個 AI-WEB Suggestion 必須至少有 1 個 AIWebSource
```

### 可追溯性檢查

```python
def validate_ai_suggestion(s: QuoteSuggestion) -> list[str]:
    """Validate AI suggestion meets traceability requirements."""
    issues = []
    if s.source_level == "AI-WEB" and not s.ai_web_sources:
        issues.append("AI-WEB suggestion missing source_url")
    if s.source_level == "AI-WEB":
        for src in s.ai_web_sources:
            if not src.source_url:
                issues.append("AIWebSource missing source_url")
            if src.extracted_value <= 0:
                issues.append("AIWebSource has invalid extracted_value")
    return issues
```

---

## 十一-C、Phase 規劃

AI 模塊是最後開發的模塊（Phase 7），在核心報價流程完全驗證後實施。

```
Phase 7.0: AI Provider 接口 + Mock (測試)
Phase 7.1: DeepSeek Provider (材料標準化 + 工藝推薦)
Phase 7.2: AI 價格建議 (AI-EST)
Phase 7.3: AI 外部查詢 (AI-WEB)
Phase 7.4: AI 與人工確認整合
```

---

*本文件為 Phase 7 設計。Phase 3-6 開發不依賴 AI。*
