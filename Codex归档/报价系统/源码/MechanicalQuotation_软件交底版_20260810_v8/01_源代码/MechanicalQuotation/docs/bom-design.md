# 機構2D自動報價系統 — BOM 數據模型設計

日期：2026-08-01
版本：V1.0
階段：Phase 2.0

---

## 一、真實 BOM 結構分析

### 1.1 來源文件

```
文件: GCS-雙滑台打磨設備-BOM.xlsx
Sheet: 工作表1
總行數: 323 (含表頭)
數據行: 318
```

### 1.2 表頭結構

| 行 | Col A | Col B | Col C | Col D | Col E | Col F | Col G | Col H | Col I | Col J |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | MPTZ | — | 公司名稱 | 項目名稱 | — | — | 建立時間 | 2026-07-29 | 設計 | — |
| 2 | — | — | 產品描述 | — | — | — | 客戶 | — | 核對 | — |
| 3 | — | — | — | — | — | — | 頁數 | — | 圖紙 | — |
| 4 | **Level** | **Item** | **Description** | — | **Type** | **Uom** | **Quantity** | **Unit Cost** | **Extended Cost** | **備註** |
| 5+ | int | str | str | — | str | str | float | float | float | str |

### 1.3 真實數據範例

```
Row 5:  Level=0  Item=UA0050000023  Type=Finished good
        Desc=成品;打磨;雙臺;通用;自動;GCS;雙滑台打磨設備;機器人精修機
        價格=0 (成品，非零件)

Row 6:  Level=1  Item=UB100D000654  Type=Subassembly
        Desc=半成品;工單;評估代碼;GCS-雙滑台打磨設備
        價格=0

Row 158: Level=2  Item=UC1000005854  Type=Purchased item
        Desc=原材料;加工件;S50C;J003;928*796*15;熱處理
        單價=1425 總價=1425
```

### 1.4 Item 前綴分類

| 前綴 | 含義 | 數量 | 範例 |
|---|---|---|---|
| **UA** | 成品 (Finished Good) | 1 | UA0050000023 |
| **UB** | 半成品/組件 (Subassembly) | 28 | UB100D000654 |
| **UC** | 採購件/加工件 (Purchased Item) | 288 | UC1000005854 |

### 1.5 Description 解析結構

Description 使用分號 `;` 分隔，格式為：

```
Segment 0      Segment 1     Segment 2    Segment 3    Segment 4       Segment 5+
   ↓              ↓             ↓            ↓            ↓               ↓
  類別          子類別        材料/類型     零件碼/規格   尺寸            表面處理/品牌/備註
```

**範例 A — 加工件:**
```
原材料;加工件;S50C;J003;928*796*15;熱處理
  ↓      ↓      ↓     ↓      ↓         ↓
 cat=原材料 type=加工件 mat=S50C code=J003 dims=928*796*15 surf=熱處理
```

**範例 B — 電控外購件:**
```
原材料;電控外購件;控制類;PLC擴展;擴展IO模塊;型號:AS16AP11T-A;品牌:台達
  ↓      ↓           ↓        ↓         ↓              ↓                  ↓
 cat=原材料 type=電控外購 cat=控制類 subcat=PLC spec=擴展IO model=AS16AP11T-A brand=台達
```

**範例 C — 機構外購件:**
```
原材料;機構外購件;鋁型材;40*40;圖號:W001;1300*1300*995;顏色透明
  ↓      ↓           ↓       ↓       ↓          ↓              ↓
 cat=原材料 type=機構外購 mat=鋁型材 dims=40*40 code=W001 spec=1300*1300*995 color=透明
```

### 1.6 零件類型分佈

| Type (Col E) | 數量 | Description 子類別 |
|---|---|---|
| Finished good | 1 | 成品 |
| Subassembly | 44 | 工單(6), 運輸(6), 軟體(10), 機頭(2), 機架(2), 防護(2), 加工件(16) |
| Purchased item | 262 | 加工件(66), 電控外購件(140), 機構外購件(56) |
| Phantom item | 10 | 軟體(10) |

### 1.7 我們關心的目標零件

**加工件 (Description segment 1 = "加工件")：共 82 件**

- 其中 20 件有對應 DWG 文件
- 其中 66 件有 BOM 價格但無對應 DWG
- 9 件 DWG 文件無 BOM 對應 (Z 系列)

---

## 二、零件分類模型

### 2.1 分類枚舉

```python
class PartCategory(str, Enum):
    """Description segment 0 — 頂層分類"""
    RAW_MATERIAL = "原材料"       # 原材料
    SEMI_FINISHED = "半成品"      # 半成品

class PartSubType(str, Enum):
    """Description segment 1 — 子類別"""
    MACHINED = "加工件"           # CNC/車床/線割 加工件 ← 我們定價的目標
    ELECTRICAL = "電控外購件"      # PLC/傳感器/電機 等
    MECHANICAL = "機構外購件"      # 鋁型材/導軌/氣缸 等
    SOFTWARE = "軟體"             # PLC程序/圖紙
    WORK_ORDER = "工單"           # 評估/設計/調試
    TRANSPORT = "運輸"            # 運輸/包裝
    FRAME = "機架"                # 機架焊接
    HEAD = "機頭"                 # 機頭模組
    GUARD = "防護"                # 安全防護

class BomItemType(str, Enum):
    """Col E — ERP 系統中的項目類型"""
    FINISHED_GOOD = "Finished good"
    SUBASSEMBLY = "Subassembly"
    PURCHASED = "Purchased item"
    PHANTOM = "Phantom item"
```

### 2.2 分類決策樹

```
BOM Row
  │
  ├─ Col E = "Finished good"  → 成品，不報價
  ├─ Col E = "Phantom item"   → 虛擬項（軟體），不報價
  ├─ Col E = "Subassembly"    → 組件，需根據子類別判斷
  │    ├─ segment 1 = "工單"   → 人工費用，非零件
  │    ├─ segment 1 = "加工件"  → 可能含零件（少見）
  │    └─ segment 1 = 其他     → 跳過
  │
  └─ Col E = "Purchased item" → 需要採購/加工
       ├─ segment 1 = "加工件"      → ✅ 我們定價的目標
       ├─ segment 1 = "機構外購件"   → H 來源（直接使用 BOM 價格）
       ├─ segment 1 = "電控外購件"   → H 來源（直接使用 BOM 價格）
       └─ segment 1 = 其他          → 跳過
```

---

## 三、BOM 數據模型（最終版）

### 3.1 BomEntry — BOM 單行（含來源追蹤）

```python
# domain/bom.py (修訂版)

class BomEntry(BaseModel):
    """BOM 單行 — 保留 Excel 原始信息 + 來源追蹤"""

    # === 來源追蹤 ===
    source_file: str = Field(..., description="BOM Excel 文件路徑")
    source_row: int = Field(..., ge=5, description="Excel 行號（1-based）")
    source_sheet: str = Field(default="工作表1", description="Sheet 名稱")

    # === ERP 字段（直接映射 Excel Column） ===
    level: int = Field(..., ge=0, description="BOM 層級 (Col A)")
    item: str = Field(..., description="Item 編號 (Col B)")
    description: str = Field(..., description="完整描述 (Col C)")
    item_type: str = Field(..., description="ERP 類型 (Col E)")
    uom: str = Field(default="ST", description="單位 (Col F)")
    quantity: float = Field(default=1.0, gt=0, description="數量 (Col G)")

    # === 價格（Col H, I） ===
    unit_cost: float = Field(default=0.0, ge=0, description="單價 CNY (Col H)")
    extended_cost: float = Field(default=0.0, ge=0, description="總價 CNY (Col I)")

    # === 備註（Col J） ===
    notes: str | None = Field(default=None, description="備註")

    # === 結構 ===
    parent_item: str | None = Field(default=None, description="父項 Item（用於樹狀結構重建）")
```

### 3.2 ParsedPart — 結構化解析（修訂版）

```python
class ParsedPart(BaseModel):
    """從 BomEntry.description 解析出的結構化零件數據"""

    # === 來源 ===
    bom_item: str = Field(..., description="來源 BomEntry.item")
    source_row: int = Field(..., description="來源 Excel 行號")

    # === 分類（從 description segment 0-1 解析） ===
    category: str | None = Field(default=None, description="原材料 / 半成品")
    sub_type: str | None = Field(default=None, description="加工件 / 電控外購件 / 機構外購件 / …")

    # === 加工件專用字段 ===
    material: str | None = Field(default=None, description="材料，如 S50C, A6061-T6, SPCC")
    part_code: str | None = Field(default=None, description="零件代碼，如 J003, R001")
    dimensions_raw: str | None = Field(default=None, description="原始尺寸文字，如 928*796*15")
    surface_treatment: str | None = Field(default=None, description="表面處理，如 熱處理")

    # === 外購件專用字段 ===
    model_number: str | None = Field(default=None, description="型號")
    brand: str | None = Field(default=None, description="品牌")
    spec: str | None = Field(default=None, description="規格說明")

    # === 價格 ===
    unit_cost: float = Field(default=0.0, ge=0)
    quotation_source: str = Field(default="BOM", description="BOM | SUPPLIER | MANUAL")

    # === 關聯 ===
    drawing_ref: str | None = Field(default=None, description="匹配的 DWG 文件名")
    feature_ref: str | None = Field(default=None, description="匹配的 Feature.id")

    # === 是否為報價目標 ===
    is_quotable: bool = Field(default=False, description="是否為加工件（需要系統報價）")
    is_matched: bool = Field(default=False, description="是否已匹配 DWG")
```

### 3.3 BomSheet — BOM 匯總（修訂版）

```python
class BomSheet(BaseModel):
    """完整 BOM 匯入結果"""

    # === 來源 ===
    source_file: str = Field(..., description="BOM Excel 文件路徑")
    source_sheet: str = Field(default="工作表1")

    # === 基本資訊 ===
    project_name: str | None = Field(default=None)
    total_rows: int = Field(default=0, ge=0)

    # === 數據 ===
    entries: list[BomEntry] = Field(default_factory=list)
    parsed_parts: list[ParsedPart] = Field(default_factory=list)

    # === 分類統計 ===
    machined_count: int = Field(default=0, description="加工件數量")
    electrical_count: int = Field(default=0, description="電控外購件數量")
    mechanical_count: int = Field(default=0, description="機構外購件數量")
    subassembly_count: int = Field(default=0)

    # === 匹配統計 ===
    matched_drawings: int = Field(default=0)
    unmatched_drawings: int = Field(default=0)
    matched_parts: list[ParsedPart] = Field(default_factory=list)

    # === 價格統計 ===
    total_machined_cost: float = Field(default=0.0, description="加工件總成本")
    total_purchased_cost: float = Field(default=0.0, description="全部採購件總成本")
```

---

## 四、BOM 與 Drawing 關聯設計

### 4.1 關聯方式

```
BomEntry.item                          DWG 文件名
    │                                      │
    │  "UC1000005854"                       │  "UC1000005854-J003.DWG"
    │                                      │
    └──────── 數字部分匹配 ─────────────────┘
              "1000005854"
```

### 4.2 匹配規則

```python
# 從 DWG 文件名提取數字部分
# UC1000005854-J003.DWG → "1000005854"
# UC1002006858_J026.DWG → "1002006858"
# UC1004001886-J036.stp.DWG → "1004001886"

def extract_dwg_item_number(filename: str) -> str | None:
    """從 DWG 文件名提取 Item 編號的數字部分"""
    import re
    match = re.search(r'UC(\d+)', filename)
    return match.group(1) if match else None

def match_bom_to_dwg(bom_items: list[str], dwg_filenames: list[str]) -> dict:
    """
    返回:
    {
        "matched": {"UC1000005854": "UC1000005854-J003.DWG", ...},
        "unmatched_bom": [...],   # BOM 中有但無 DWG
        "unmatched_dwg": [...],   # DWG 有但 BOM 中無
    }
    """
```

### 4.3 關聯數據流

```
BOM Excel                           DWG 目錄
    │                                   │
    ▼                                   ▼
BomSheet.entries[]                 [filename, filename, ...]
    │                                   │
    ├── BomEntry.item ──匹配──→ DWG filename
    │                                   │
    ▼                                   ▼
ParsedPart.drawing_ref ←──────── ParsedPart.is_matched = True
    │
    ▼
Drawing.drawing_number ←── Drawing.feature_id ←── Feature.bom_ref
```

---

## 五、20 件回歸測試資料格式

### 5.1 回歸測試基準數據

從 BOM 提取的 20 件已匹配零件作為 ground truth：

```python
# tests/regression/test_bom_ground_truth.py

GROUND_TRUTH: list[dict] = [
    {
        "dwg_file": "UC1000005854-J003.DWG",
        "bom_item": "UC1000005854",
        "material": "S50C",
        "part_code": "J003",
        "dimensions_raw": "928*796*15",
        "surface_treatment": "熱處理",
        "bom_unit_cost": 1425.0,
        "bom_source_row": 158,
        "category": "加工件",
    },
    {
        "dwg_file": "UC1000005855-J005.DWG",
        "bom_item": "UC1000005855",
        "material": "S50C",
        "part_code": "J005",
        "dimensions_raw": "1400*250*15",
        "surface_treatment": "熱處理",
        "bom_unit_cost": 712.0,
        "bom_source_row": 159,
        "category": "加工件",
    },
    # ... 共 20 件
]
```

### 5.2 回歸測試結構

```python
# tests/regression/conftest.py (Phase 2.4)

@pytest.fixture(scope="module")
def bom_sheet():
    """載入真實 BOM → BomSheet"""
    ...

@pytest.fixture(scope="module")
def regression_parts(bom_sheet):
    """提取 20 件已匹配加工件"""
    ...

# tests/regression/test_bom_ground_truth.py

class TestBomParsing:
    """Phase 2.2: Description 解析正確性"""
    @pytest.mark.parametrize("part", GROUND_TRUTH)
    def test_material_parsed(self, part, regression_parts): ...

    @pytest.mark.parametrize("part", GROUND_TRUTH)
    def test_dimensions_parsed(self, part, regression_parts): ...

class TestBomDwgMatching:
    """Phase 2.3: DWG/BOM 匹配正確性"""
    def test_20_matches_found(self, bom_sheet): ...
    def test_9_unmatched_z_series(self, bom_sheet): ...
    def test_no_false_matches(self, bom_sheet): ...

class TestRegressionBaseline:
    """Phase 2.4: 回歸測試基準就緒"""
    @pytest.mark.parametrize("part", GROUND_TRUTH)
    def test_has_unit_cost(self, part, regression_parts):
        """每件都有真實價格"""
        ...

    @pytest.mark.parametrize("part", GROUND_TRUTH)
    def test_has_dimensions(self, part, regression_parts):
        """每件都有尺寸數據"""
        ...
```

### 5.3 回歸測試 JSON 輸出格式

```json
{
  "regression_baseline": {
    "version": "1.0",
    "source": "GCS-雙滑台打磨設備-BOM.xlsx",
    "created_at": "2026-08-01",
    "total_matched": 20,
    "total_unmatched": 9,
    "parts": [
      {
        "bom_item": "UC1000005854",
        "dwg_file": "UC1000005854-J003.DWG",
        "source_row": 158,
        "material": "S50C",
        "part_code": "J003",
        "dimensions": {"length": 928, "width": 796, "height": 15},
        "dimensions_raw": "928*796*15",
        "surface_treatment": "熱處理",
        "bom_unit_cost": 1425.0,
        "quotation_source": "BOM",
        "category": "加工件"
      }
    ]
  }
}
```

---

## 六、BOM 數據模型與 Phase 1 Domain Model 的關係

```
Phase 1 (已完成)              Phase 2 (本階段)
─────────────────            ─────────────────
domain/bom.py                infrastructure/excel/bom_reader.py
  BomEntry (靜態模型)          → 填充 BomEntry 實例
  ParsedPart (靜態模型)        → 解析 description → ParsedPart
  BomSheet (靜態模型)          → 匯總 BomSheet

domain/drawing.py
  Drawing                     → drawing_number ← BomEntry.item 匹配

domain/feature.py
  Feature                     → bom_ref ← BomEntry.item
                              → material_normalized ← ParsedPart.material
                              → dimensions_raw ← ParsedPart.dimensions_raw

tests/unit/domain/            tests/unit/infrastructure/
  test_bom.py (模型驗證)       → test_bom_reader.py (讀取器)
                              tests/regression/
                                test_bom_ground_truth.py (20件基準)
```

---

## 七、與 Phase 1 模型的一致性確認

| Phase 1 設計 | 真實 BOM 需求 | 是否需要修改 |
|---|---|---|
| BomEntry.item | ✅ 對應 Col B | 無需修改 |
| BomEntry.description | ✅ 對應 Col C | 無需修改 |
| BomEntry.level | ✅ 對應 Col A | 無需修改 |
| BomEntry.item_type | ✅ 對應 Col E | 無需修改 |
| BomEntry.uom | ✅ 對應 Col F | 無需修改 |
| BomEntry.unit_cost | ✅ 對應 Col H | 無需修改 |
| BomEntry.quantity | ✅ 對應 Col G | 無需修改 |
| **source_row** | ❌ Phase 1 缺失 | **需新增** |
| **source_sheet** | ❌ Phase 1 缺失 | **需新增** |
| BomEntry.supplier | ⚠️ Col J 備註中偶有 | 保留 optional |
| ParsedPart.sub_type | ❌ Phase 1 命名為 category | **需重命名為 sub_type，新增 category** |
| ParsedPart.is_quotable | ❌ Phase 1 缺失 | **需新增**（用來區分加工件 vs 外購件） |
| ParsedPart.is_matched | ❌ Phase 1 缺失 | **需新增**（DWG 匹配狀態） |
| BomSheet.matched_parts | ❌ Phase 1 缺失 | **需新增** |
| BomSheet 分類統計 | ❌ Phase 1 缺失 | **需新增** |

### 需要的 Phase 1 模型修改

以下字段需要增加到現有 domain/bom.py：

1. `BomEntry.source_row: int` — Excel 行號
2. `BomEntry.source_sheet: str` — Sheet 名稱
3. `ParsedPart.category: str | None` — 原材料/半成品（segment 0）
4. `ParsedPart.sub_type: str | None` — 重命名原 category（segment 1）
5. `ParsedPart.model_number: str | None` — 型號（外購件）
6. `ParsedPart.brand: str | None` — 品牌（外購件）
7. `ParsedPart.spec: str | None` — 規格（外購件）
8. `ParsedPart.quotation_source: str` — 報價來源
9. `ParsedPart.is_quotable: bool` — 是否為報價目標（加工件）
10. `ParsedPart.is_matched: bool` — 是否已匹配 DWG
11. `BomSheet.matched_parts: list[ParsedPart]` — 已匹配零件
12. `BomSheet.machined_count: int` — 加工件計數
13. `BomSheet.electrical_count: int` — 電控外購件計數
14. `BomSheet.mechanical_count: int` — 機構外購件計數

---

*本文件為 Phase 2.0 產出。Phase 2.1-2.4 將據此實現。*

---

## 八、BOM 定位修正（2026-08-01 更新）

### 8.1 核心修正

**BOM 不是未來報價流程的必要輸入。**

實際使用場景中，客戶通常只提供：
- PDF 圖紙
- DWG 圖紙

不會提供 BOM Excel。

### 8.2 BOM 的新定位

BOM 的定位為：

> **「歷史報價知識庫建立來源」**

```
BOM 的用途：
  ✅ 建立 HistoricalFeature 知識庫
  ✅ 提供 20 件回歸測試基準（真實價格 vs 系統報價）
  ✅ 驗證規則引擎計算結果
  ❌ 不是正式報價的必要輸入
```

### 8.3 雙流程設計

#### 流程 A：知識庫建立（離線，一次性/批次）

```
BOM Excel + DWG 圖紙 + PDF 圖紙
        │
        ▼
   BomReader (Phase 2.1)
        │
        ▼
   Description Parser (Phase 2.2)
        │
        ▼
   DWG/BOM Cross-Match (Phase 2.3)
        │
        ▼
   ParsedPart + Feature
        │
        ▼
   HistoricalFeature 合併
        │
        ▼
   quotation_history.db (SQLite)
```

#### 流程 B：實際報價（線上，客戶使用）

```
客戶提供: PDF 或 DWG
        │
        ▼
   Drawing Parser (Phase 3)
        │
        ▼
   Feature Extractor (Phase 3)
        │
        ▼
   Feature Model
        │
        ├──────────────────────────┐
        ▼                          ▼
   Similarity Search        Rule Engine
   (quotation_history.db)   (quotation-rules.yaml)
        │                          │
        │ source = H               │ source = C
        │                          │
        └──────────┬───────────────┘
                   ▼
              Quote Model
                   │
                   ▼
              Excel 輸出
```

### 8.4 HistoricalFeature 與 ParsedPart 的關係

| 模型 | 用途 | 存儲 | 階段 |
|---|---|---|---|
| `ParsedPart` | BOM 解析中間產物 | 暫存（內存） | Phase 2 |
| `HistoricalFeature` | 歷史知識庫存儲單元 | 持久化（SQLite） | Phase 2 |
| `Feature` | CAD 提取的零件特徵 | 暫存（內存） | Phase 3 |
| `Quote` | 最終報價 | 暫存/輸出 | Phase 4 |

轉換關係：

```
ParsedPart ──→ HistoricalFeature ←── Feature (CAD)
                   │
                   ▼
            quotation_history.db
                   │
                   ▼ (Phase 4)
            Similarity Search
                   │
                   ▼
              Quote (H source)
```

### 8.5 Phase 2 修正後範圍

| 原規劃 | 修正後 |
|---|---|
| Phase 2.2: Description Parser → ParsedPart | ✅ 保持，但目標改為填入 HistoricalFeature |
| Phase 2.3: DWG/BOM 交叉匹配 | ✅ 保持 |
| Phase 2.4: 20件回歸測試 | ✅ 保持，增加 HistoricalFeature 導入驗證 |
| **新增**: HistoricalFeature 模型 | domain/historical.py |
| **新增**: SQLite 資料庫 | quotation_history.db + repository.py |
| **新增**: BOM→HistoricalFeature 導入器 | infrastructure/excel/history_importer.py |
