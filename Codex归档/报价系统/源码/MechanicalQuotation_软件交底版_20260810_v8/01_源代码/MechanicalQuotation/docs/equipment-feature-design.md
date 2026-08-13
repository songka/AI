# 機構2D自動報價系統 — 非標設備特徵設計

日期：2026-08-01
版本：V1.0

---

## 一、定位修正

系統從「加工零件報價」擴展為「**非標設備機構報價**」。

20 件歷史資料包含：

| 類型 | 範例 | 件數 |
|---|---|---|
| 機加工零件 | J003/J005/J006/J007 (S50C 鋼板) | ~12 |
| 鈑金件 | F001/F002/F003 (SPCC) | ~5 |
| 結構框架 | W001 (鋁型材+門組件) | 1 |
| 外購組件 | W001 附屬件 | ~2 |

---

## 二、重要分類原則

### BOM 分類 ≠ CAD 報價分類

BOM 中的「機構外購件」、「電控外購件」只是歷史 ERP 分類。

CAD Feature Extractor 必須根據圖紙結構判斷零件類別。

### 結構附件 ≠ 獨立外購件

合頁、把手、磁吸、角碼等若屬於防護門/機架結構，應歸類為「結構附件」，併入母組件報價。

**禁止新增 PurchasedComponentFeature**。結構附件通過 StructureAssemblyFeature.component_list 管理。

---

## 三、新增 Feature 類型

### 3.1 StructureAssemblyFeature

設備結構模組（防護罩、機架、門模組等）。

```python
class StructureAssemblyFeature(BaseModel):
    assembly_id: str
    assembly_type: str              # "GUARD" | "DOOR" | "FRAME" | "ENCLOSURE"
    name: str                       # "防護圍欄"
    component_list: list[str]       # 子零件 item 列表
    quantity: int = 1
    source_entities: list[str] = []
    confidence: float = 0.0
```

報價影響：作為整體報價單元，子零件不單獨報價。

### 3.2 FrameFeature

型材框架。

```python
class FrameFeature(BaseModel):
    frame_id: str
    profile_type: str | None        # "鋁型材" | "方通" | "角鋼"
    material: str | None            # "鋁型材6063"
    total_length_mm: float = 0.0    # 型材總長
    joint_count: int = 0            # 連接點數量
    connection_type: str | None     # "角碼" | "焊接" | "螺栓"
    source_entities: list[str] = []
    confidence: float = 0.0
```

報價影響：型材費 = 長度 × 單價 + 連接件費。

### 3.3 SheetMetalFeature

鈑金結構。

```python
class SheetMetalFeature(BaseModel):
    sheet_id: str
    material: str | None            # "SPCC"
    thickness_mm: float = 0.0
    bend_count: int = 0
    cutting_length_mm: float = 0.0
    surface_treatment: str | None   # "噴塗RAL9003"
    source_entities: list[str] = []
    confidence: float = 0.0
```

報價影響：雷切費 + 折彎費(每彎) + 焊接費 + 表面處理。

### 3.4 AcrylicFeature

透明/亞克力件。

```python
class AcrylicFeature(BaseModel):
    acrylic_id: str
    material: str | None            # "亞克力" | "PC"
    thickness_mm: float = 0.0
    area_mm2: float = 0.0
    color: str | None               # "白色透明"
    source_entities: list[str] = []
    confidence: float = 0.0
```

報價影響：材料費 = 面積 × 厚度 × 單價。

### 3.5 StructureAccessoryFeature

結構附件（不獨立報價）。

```python
class StructureAccessoryFeature(BaseModel):
    accessory_id: str
    category: str                   # "DOOR_HARDWARE" | "FASTENER" | "BRACKET"
    items: list[str]                # ["合頁", "磁吸", "把手"]
    quantity: int = 1
    belongs_to_assembly: str | None # 歸屬的 assembly_id
    source_entities: list[str] = []
    confidence: float = 0.0
```

### 3.6 WeldingFeature

焊接結構。

```python
class WeldingFeature(BaseModel):
    weld_id: str
    weld_length_mm: float = 0.0
    joint_count: int = 0
    weld_type: str | None           # "fillet" | "butt" | "spot"
    source_entities: list[str] = []
    confidence: float = 0.0
```

報價影響：焊接費 = 長度 × 單價 或 每點單價。

---

## 四、ManufacturingFeatures 擴展

```python
class ManufacturingFeatures(BaseModel):
    # Existing (Phase 3.1)
    holes: list[HoleFeature]
    threads: list[ThreadFeature]
    material: MaterialFeature | None
    surface_treatment: SurfaceTreatmentFeature | None

    # New (Phase 3.3)
    structure_assemblies: list[StructureAssemblyFeature] = []
    frames: list[FrameFeature] = []
    sheet_metal_parts: list[SheetMetalFeature] = []
    acrylic_parts: list[AcrylicFeature] = []
    structure_accessories: list[StructureAccessoryFeature] = []
    welds: list[WeldingFeature] = []

    bounding_box_mm: BoundingBox | None
```

---

## 五、Golden Dataset 案例：W001

### UC2020083221-W001 (鋁型材框架防護罩)

```json
{
  "structure_assemblies": [
    {
      "assembly_type": "GUARD",
      "name": "防護圍欄",
      "components": ["鋁型材框架", "亞克力門", "五金附件"]
    },
    {
      "assembly_type": "DOOR",
      "name": "門組件",
      "components": ["鋁型材門框", "白色透明亞克力"]
    }
  ],
  "frames": [
    {
      "profile_type": "鋁型材",
      "material": "鋁型材6063",
      "total_length_mm": 9800,
      "joint_count": 20,
      "connection_type": "角碼"
    }
  ],
  "acrylic_parts": [
    {
      "material": "亞克力",
      "area_mm2": 1292200,
      "color": "白色透明"
    }
  ],
  "structure_accessories": [
    {
      "category": "DOOR_HARDWARE",
      "items": ["合頁", "磁吸", "把手"]
    }
  ],
  "welds": [
    {
      "weld_type": "spot",
      "joint_count": 4,
      "note": "加強筋焊接"
    }
  ]
}
```

---

## 六、識別規則（從 TextCluster）

| Feature | 觸發關鍵詞 |
|---|---|
| FrameFeature | "型材"、"鋁型材"、"鋁擠型"、"方通"、"角鋼" |
| SheetMetalFeature | "SPCC"、"鈑金"、"板金"、"折彎"、"焊接" |
| AcrylicFeature | "亞克力"、"壓克力"、"PC板"、"透明" |
| StructureAccessoryFeature | "合頁"、"鉸鏈"、"磁吸"、"把手"、"角碼"、"門鎖" |
| WeldingFeature | "焊接"、"點焊"、"滿焊"、"加強筋" |
| StructureAssemblyFeature | "防護"、"圍欄"、"機架"、"門"、"罩" |

---

*本文件為 Phase 3.3 設計。*
