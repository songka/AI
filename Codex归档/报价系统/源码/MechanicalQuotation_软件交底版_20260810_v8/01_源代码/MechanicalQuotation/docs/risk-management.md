# 機構2D自動報價系統 — 風險管理計劃 (Risk Management)

日期：2026-08-01
版本：V1.0

---

## 風險分級定義

| 級別 | 含義 | 行動 |
|---|---|---|
| **P0** | 阻斷性風險 — 不解決則系統無法運行 | 必須在 Phase 0 解決 |
| **P1** | 功能性風險 — 影響核心報價準確性 | Phase 1 設計中預留，Phase 4 前解決 |
| **P2** | 完整性風險 — 影響部分零件報價 | Phase 2-3 中逐步解決 |
| **P3** | 優化性風險 — 不影響基本功能 | 後續版本解決 |

---

## 一、P0 風險：DWG 二進制格式 — CAD 解析阻斷

### 1.1 問題描述

- AutoCAD DWG 為專有二進制格式，ezdxf 庫**僅支持 DXF 文本格式**
- 29 件樣本全部為 DWG 格式（magic bytes: `AC1032`）
- 無 DWG→DXF 轉換器，CAD 解析模塊無法開發

### 1.2 影響範圍

- Phase 3（CAD 解析）**完全受阻**
- Phase 4（特徵提取）無法驗證
- 回歸測試無法使用真實 DWG

### 1.3 候選方案

#### 方案 A：ODA File Converter（推薦 ✅）

| 項目 | 說明 |
|---|---|
| 提供方 | Open Design Alliance |
| 授權 | 免費（非商業用途）/ 商業授權 |
| 平台 | Windows / Linux / macOS |
| 方式 | 命令行批量轉換 DWG → DXF |
| 優點 | 官方級別兼容性，支持所有 DWG 版本 |
| 缺點 | 需單獨安裝，商業使用需購買授權 |
| 下載 | https://www.opendesign.com/guestfiles/oda_file_converter |

集成方式：
```bash
ODAFileConverter.exe /i input_dir /o output_dir /in "DWG" /out "DXF" /ver 2018 /f
```

然後使用 ezdxf 讀取生成的 DXF。

#### 方案 B：LibreDWG

| 項目 | 說明 |
|---|---|
| 提供方 | GNU 開源項目 |
| 授權 | GPLv3 |
| 方式 | `dwg2dxf` 命令行工具 |
| 優點 | 開源免費 |
| 缺點 | Windows 編譯困難，兼容性不如 ODA |

#### 方案 C：QCAD Professional

| 項目 | 說明 |
|---|---|
| 提供方 | RibbonSoft |
| 授權 | 商業（約 €39） |
| 方式 | 命令行 `dwg2dxf` |

### 1.4 推薦處理方案

**採用方案 A（ODA File Converter）**，設計三階段流程：

```
DWG (原始格式)
    │
    ▼
[ODA File Converter]    ← 外部工具，命令行調用
    │
    ▼
DXF (標準交換格式)
    │
    ▼
[ezdxf Parser]          ← Python 庫，程序內讀取
    │
    ▼
Drawing Model
```

### 1.5 程序設計

```python
# infrastructure/dxf/converter.py (Phase 3)
class DwgToDxfConverter:
    """Convert DWG to DXF using external ODA File Converter."""

    def convert(self, dwg_path: Path, output_dir: Path) -> Path:
        """Convert a single DWG file to DXF format."""
        ...

    def batch_convert(self, dwg_dir: Path, output_dir: Path) -> list[Path]:
        """Convert all DWG files in a directory."""
        ...

    def is_converter_available(self) -> bool:
        """Check if ODA File Converter is installed."""
        ...
```

### 1.6 臨時方案（Phase 0-2）

在 DWG 轉換器安裝之前：
- Phase 1（數據模型）：不依賴 DWG
- Phase 2（歷史報價庫）：使用 BOM Excel 數據
- 所有測試使用手動構造的 DXF 或 ezdxf 生成的測試 DXF

---

## 二、P1 風險：SPCC 材料規則缺失

### 2.1 問題描述

BOM 中有 **19 件 SPCC（冷軋鋼板）** 零件，但 `quotation-rules.yaml` 中無 SPCC 規則。

### 2.2 影響範圍

- F 系列（底板）全部無法報價
- J 系列部分無法報價
- W 系列部分無法報價

### 2.3 處理方案

**禁止硬編碼價格**。採用佔位規則 + 人工確認模式：

```yaml
# rules/quotation-rules.yaml 增加：
material:
  SPCC:
    price: 0             # 佔位：待用戶提供
    unit: kg
    density: 7.85        # g/cm³（已知值）
    loss_rate: 0.05
    status: "PENDING"    # 標記為待確認
    note: "冷軋鋼板，價格待採購部門確認"
```

程序行為：
- 讀取到 `status: PENDING` 的材料時，將該報價項目標記為 **U（未知）**
- 在 Excel 輸出的「未知項」Sheet 中列出
- 記錄到日誌：`WARNING: SPCC price not configured, item XXX marked as U`

**在用戶提供真實 SPCC 價格之前，系統對 SPCC 零件只計算材料重量，不計算材料費。**

### 2.4 數據模型設計

```python
# domain/material.py
class MaterialRule:
    material_id: str
    material_name: str
    density: float | None        # g/cm³
    unit_price: float
    unit: str                    # "kg"
    loss_rate: float
    status: str                  # "ACTIVE" | "PENDING" | "DEPRECATED"
    note: str | None
```

---

## 三、P1 風險：材料密度缺失

### 3.1 問題描述

材料費計算公式：

```
材料費 = 長(mm) × 寬(mm) × 高(mm) × 密度(g/cm³) ÷ 1000 × 單價(元/kg)
       = 體積(cm³) × 密度(g/cm³) ÷ 1000 × 單價(元/kg)
       = 重量(kg) × 單價(元/kg)
```

無密度則無法從尺寸計算重量，材料費計算鏈斷裂。

### 3.2 處理方案

建立獨立的 `material-density.yaml` 物理屬性文件：

```yaml
# rules/material-density.yaml
# 材料物理屬性 — 密度數據來自材料手冊，不涉及價格

version: "1.0"
source: "工程材料手冊（常用值）"
note: "密度為理論值，實際可能有 ±2% 偏差"

materials:
  A6061-T6:
    density: 2.70        # g/cm³
    category: "鋁合金"
    grade: "6061-T6"

  S50C:
    density: 7.85        # g/cm³
    category: "碳素鋼"
    grade: "S50C"

  SUS304:
    density: 7.93        # g/cm³
    category: "不鏽鋼"
    grade: "SUS304"

  SKD11:
    density: 7.85        # g/cm³
    category: "工具鋼"
    grade: "SKD11"

  SKD61:
    density: 7.85        # g/cm³
    category: "熱作模具鋼"
    grade: "SKD61"

  SPCC:
    density: 7.85        # g/cm³
    category: "冷軋鋼板"
    grade: "SPCC"

  普通鋼:
    density: 7.85        # g/cm³
    category: "普通碳鋼"
    note: "通用值，用於未標明具體牌號的鋼件"
```

### 3.3 數據模型設計

```python
# domain/material.py
class MaterialProperties:
    """Physical properties (separated from pricing)."""
    name: str
    density: float              # g/cm³, required
    category: str
    grade: str
    source: str                 # "material-density.yaml"
```

### 3.4 設計原則

| 原則 | 說明 |
|---|---|
| **物理屬性與價格分離** | 密度屬於材料物理屬性，不隨市場波動；價格屬於商業規則，會變動 |
| **獨立文件管理** | `material-density.yaml` 只包含密度/類別，不含價格 |
| **密度為必填** | 無密度的材料報價時標記為 U |
| **可覆蓋** | BOM 或圖紙中可手動指定密度覆蓋默認值 |

---

## 四、P1 風險：表面處理計價方式不完整

### 4.1 問題描述

現有規則只有單一 `price/kg` 模式：

```yaml
surface:
  陽極:
    price: 20
    unit: kg
```

但實際表面處理計價方式多樣：

| 表面處理 | 真實計價方式 | 現有規則 |
|---|---|---|
| 陽極氧化 | 按**面積** (元/dm²) 或按重量 | ❌ 只有 kg |
| 噴塗 (RAL9003) | 按**面積** (元/m²) | ❌ 無規則 |
| 熱處理 | 按**重量** (元/kg) | ✅ 正確 |
| 發黑 | 按**重量** (元/kg) | ✅ 正確 |
| 鍍鉻 | 按**面積** (元/dm²) | ❌ 只有 kg |

### 4.2 處理方案

擴展表面處理規則，支持**多模式計價**：

```yaml
# rules/quotation-rules.yaml 表面處理規則（擴展版）

surface:
  熱處理:
    pricing_mode: "by_weight"     # 按重量計價
    unit_price: 11
    unit: "kg"
    min_charge: 50                # 最低消費 50 元
    applicable_materials: ["S50C", "SKD11", "SKD61"]

  陽極氧化:
    pricing_mode: "by_area"       # 按面積計價
    unit_price: 0.15              # 元/dm²
    unit: "dm2"
    min_charge: 30
    applicable_materials: ["A6061-T6"]
    note: "銀色陽極氧化"

  噴塗:
    pricing_mode: "by_area"       # 按面積計價
    unit_price: 0.35              # 元/dm²
    unit: "dm2"
    min_charge: 50
    applicable_materials: ["SPCC", "普通鋼"]
    note: "顏色: RAL9003 皺紋白"

  發黑:
    pricing_mode: "by_weight"
    unit_price: 2.5
    unit: "kg"
    min_charge: 20
    applicable_materials: ["S50C", "SPCC", "普通鋼"]

  鍍鉻:
    pricing_mode: "by_area"
    unit_price: 0.50
    unit: "dm2"
    min_charge: 100
    applicable_materials: ["S50C", "SKD11"]
```

### 4.3 計價模式枚舉

| 模式 | 計算公式 | 適用場景 |
|---|---|---|
| `by_weight` | 單價 × 零件重量(kg) | 熱處理、發黑 |
| `by_area` | 單價 × 表面積(dm²) | 陽極、噴塗、鍍鉻 |
| `by_piece` | 單價 × 數量 | 小零件批次處理 |
| `by_length` | 單價 × 長度(m) | 線材處理 |

### 4.4 數據模型

```python
# domain/rule.py
class SurfacePricingMode(Enum):
    BY_WEIGHT = "by_weight"
    BY_AREA = "by_area"
    BY_PIECE = "by_piece"
    BY_LENGTH = "by_length"

class SurfaceRule:
    surface_id: str
    surface_name: str
    pricing_mode: SurfacePricingMode
    unit_price: float
    unit: str
    min_charge: float | None
    applicable_materials: list[str]
    note: str | None
```

---

## 五、P2 風險匯總

| 風險 | 說明 | 計劃 |
|---|---|---|
| Z 系列 9 件無 BOM | 可能是新零件或特殊件 | Phase 2 標記為 U，人工確認後補充 |
| PDF 無對應 DWG | 少數只有 PDF | PDF 僅作視覺參考，不能自動解析 |
| 精雕機/夾頭價格缺失 | 規則中標記「待補」 | Phase 4 保留佔位 |
| 非標設備報價規則 | BOM 中有模組級別報價 | Phase 4+ 考慮 |

---

## 六、風險處置時間線

```
Phase 0（當前）
├── ✅ P0: 確認 DWG 轉換方案 (ODA File Converter)
├── ✅ P1: 設計 SPCC 佔位規則
├── ✅ P1: 設計 material-density.yaml
├── ✅ P1: 設計表面處理多模式計價
└── ⏳ P0: 安裝 ODA File Converter（用戶操作）

Phase 1（數據模型）
├── 實現 MaterialProperties（含密度）
├── 實現 SurfacePricingMode 枚舉
├── 實現 PENDING 狀態材料處理
└── 為所有 P1 風險預留數據接口

Phase 2（歷史報價庫）
├── 導入 BOM Excel 數據
├── 建立 20 件回歸測試基準
└── 驗證 SPCC 價格佔位行為

Phase 3（CAD 解析）
├── 使用 ODA 轉換 DWG→DXF
└── 從 DXF 提取尺寸驗證 BOM 數據

Phase 4（規則引擎）
├── 加載 material-density.yaml
├── 實現多模式表面處理計算
├── 價格版本自動選擇 (quote_date → effective version)
└── 與 20 件真實價格交叉驗證

Phase 4+（定價管理）
├── 價格 Excel 匯入 + 版本歸檔
├── 價格趨勢分析
└── 歷史報價曲線
```

---

## 七、P1 風險：價格版本管理（新增）

### 7.1 問題描述

- 材料價格隨市場波動（如 A6061 從 36→38 元/kg）
- 加工費率可能調整
- 如果報價不記錄使用的價格版本，無法追溯

### 7.2 處理方案

已設計完整版本管理（詳見 `pricing-version-design.md`）：
- 每次價格變更產生新 `PriceVersion`
- 舊版本歸檔到 `rules/archive/`，不可覆蓋
- Quote 記錄所有使用的價格版本 ID
- 根據 `quote_date` 自動選擇當時有效價格

### 7.3 驗證方式

```python
def test_version_selection():
    # 2025-03-15 的報價應使用 2025-01-01 生效的價格
    version = resolve_active_version("material", "2025-03-15", versions)
    assert version.version_id == "MAT-2025-01-01-v1"

def test_old_version_preserved():
    # 歸檔的價格版本不應被修改
    archived = load_archived_version("MAT-2024-06-01-v1")
    assert archived["A6061-T6"].unit_price == 36.0  # 原始價格
```

---

## 八、P2 風險：工時規則不精確

### 8.1 問題描述

工時是估算值，與實際加工時間可能有偏差。

### 8.2 處理方案

- 支持多種工時估算模式（fixed/per_hole/per_volume）
- 從 BOM 真實價格反推工時（差距過大時標記 Issue）
- 預留人工調整工時接口

---

## 九、風險處置時間線（更新版）

```
Phase 0（當前）
├── ✅ P0: 確認 DWG 轉換方案
├── ✅ P1: 設計 SPCC 佔位規則
├── ✅ P1: 設計 material-density.yaml
├── ✅ P1: 設計表面處理多模式計價
├── ✅ P1: 設計價格版本管理
└── ⏳ P0: 安裝 ODA File Converter（用戶操作）

Phase 1（已完成）
├── ✅ 所有 Domain 模型
├── ✅ MaterialProperties（含密度）
├── ✅ SurfacePricingMode 枚舉
└── ✅ PENDING 狀態材料處理

Phase 2（歷史知識庫）
├── BOM Reader ✅
├── HistoricalFeature 模型
├── SQLite 資料庫
└── 20 件回歸基準

Phase 4（規則引擎+定價）
├── 價格版本管理實現
├── 自動版本選擇 (quote_date)
├── 價格分析/趨勢
└── 多模式表面處理計算
```

---

*本文件隨風險發現持續更新。*
