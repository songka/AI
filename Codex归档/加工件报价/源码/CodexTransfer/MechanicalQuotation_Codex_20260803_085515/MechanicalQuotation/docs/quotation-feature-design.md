# 機構2D自動報價系統 — Quotation Feature 設計

日期：2026-08-01
版本：V1.0

---

## 一、定位

**QuotationFeature 不包含價格。只描述「需要計算什麼成本」。**

價格由 Rule Engine (Phase 4) 根據規則計算。

---

## 二、架構

```
ManufacturingFeature (Layer 3)
    Hole, Thread, Material, Surface,
    Frame, SheetMetal, Acrylic, Accessory, Weld, Assembly
        │
        ▼ QuotationMapper (Phase 3.4)
QuotationFeature (Layer 4)
    MachiningQuotation, FrameQuotation,
    SheetMetalQuotation, AssemblyQuotation
        │
        ▼ Rule Engine (Phase 4)
Price
```

---

## 三、QuotationFeature 類型

### 3.1 MachiningQuotationFeature

加工件報價計算描述。

```python
class MachiningQuotationFeature(BaseModel):
    feature_id: str
    source_part: str             # BOM item

    # Material
    material: str | None
    weight_kg: float = 0.0       # 需要計算：材料費 = weight × unit_price
    material_loss_rate: float = 0.05

    # Machining
    process_hints: list[str]     # ["CNC", "車床", "磨床"]
    hole_count: int = 0
    thread_count: int = 0
    tolerance_grade: str | None  # "IT7"
    setup_count: int = 1         # 裝夾次數

    # Surface
    surface_treatment: str | None
    surface_area_mm2: float = 0.0
    surface_mode: str = "by_weight"  # by_weight | by_area

    source: str = "MANUFACTURING_FEATURE"
    confidence: float = 0.0
```

Rule Engine 需要計算：
- 材料費 = weight_kg × material_unit_price × (1 + loss_rate)
- 加工費 = Σ(process_rate × estimated_hours)
- 表面處理費 = weight_kg × surface_price 或 area × surface_price

### 3.2 FrameQuotationFeature

型材結構報價計算描述。

```python
class FrameQuotationFeature(BaseModel):
    feature_id: str
    source_assembly: str | None

    profile_type: str | None     # "鋁型材"
    profile_length_mm: float = 0.0
    joint_count: int = 0
    connection_type: str | None  # "角碼"

    # Assembly overhead
    assembly_factor: float = 1.15  # 組裝係數

    source: str = "MANUFACTURING_FEATURE"
    confidence: float = 0.0
```

Rule Engine 需要計算：
- 型材費 = profile_length × unit_price_per_m
- 連接件費 = joint_count × unit_price_per_joint
- 組裝費 = (型材費 + 連接件費) × (assembly_factor - 1)

### 3.3 SheetMetalQuotationFeature

鈑金件報價計算描述。

```python
class SheetMetalQuotationFeature(BaseModel):
    feature_id: str
    source_part: str | None

    material: str | None
    thickness_mm: float = 0.0
    cutting_length_mm: float = 0.0
    bend_count: int = 0
    welding_length_mm: float = 0.0
    surface_area_mm2: float = 0.0
    surface_treatment: str | None

    source: str = "MANUFACTURING_FEATURE"
    confidence: float = 0.0
```

Rule Engine 需要計算：
- 材料費 = area × thickness × density × unit_price
- 雷切費 = cutting_length × rate_per_mm
- 折彎費 = bend_count × rate_per_bend
- 焊接費 = welding_length × rate_per_mm
- 表面處理費 = surface_area × rate_per_area

### 3.4 AssemblyQuotationFeature

組裝/人工計算描述。

```python
class AssemblyQuotationFeature(BaseModel):
    feature_id: str
    source_assembly: str | None

    assembly_type: str           # "GUARD" | "DOOR" | "FRAME"
    component_count: int = 0     # 子件數量
    operation: str | None        # "組裝" | "調試" | "安裝"
    labor_factor: float = 1.0    # 人工工時係數
    estimated_hours: float = 0.0

    source: str = "MANUFACTURING_FEATURE"
    confidence: float = 0.0
```

Rule Engine 需要計算：
- 人工費 = estimated_hours × labor_rate
- 輔料費 = component_count × auxiliary_rate


## 四、QuotationFeatures 聚合

```python
class QuotationFeatures(BaseModel):
    machining: list[MachiningQuotationFeature] = []
    frames: list[FrameQuotationFeature] = []
    sheet_metal: list[SheetMetalQuotationFeature] = []
    assemblies: list[AssemblyQuotationFeature] = []

    # Convenience
    def all_features(self) -> list:
        return self.machining + self.frames + self.sheet_metal + self.assemblies
```

---

## 五、Mapping 邏輯

```
ManufacturingFeature              QuotationFeature
─────────────────────            ──────────────────
HoleFeature + Material          → MachiningQuotation
  + SurfaceTreatment               (material + weight + holes + surface)

FrameFeature                    → FrameQuotation
                                    (profile + joints + assembly_factor)

SheetMetalFeature               → SheetMetalQuotation
                                    (cutting + bend + welding + surface)

StructureAssembly               → AssemblyQuotation
                                    (type + components + labor)
```

---

## 六、Golden Case 驗證

### J003 (S50C 機加工件)

```
ManufacturingFeature:
  material: S50C, weight: 86.9kg
  holes: 4×M6 through
  surface: 鍍鉻
  ↓
MachiningQuotationFeature:
  material: S50C, weight_kg: 86.9
  process_hints: ["CNC", "熱處理"]
  hole_count: 4, thread_count: 4
  surface_treatment: 鍍鉻
```

### W001 (鋁型材防護罩)

```
ManufacturingFeature:
  Frame: 鋁型材40×40
  Acrylic: 白色透明
  Accessory: 合頁+磁吸+把手+角碼
  Weld: 加強筋
  Assembly: GUARD + DOOR
  ↓
FrameQuotationFeature:
  profile_type: 鋁型材, joint_count: 20

SheetMetalQuotationFeature: (none — W001 is frame, not sheet metal)

AssemblyQuotationFeature:
  type: GUARD + DOOR, components: 6, labor: 組裝
```

---

*本文件為 Phase 3.4 設計。*
