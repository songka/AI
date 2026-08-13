# 機構2D自動報價系統 — CAD 匯入設計

日期：2026-08-01
版本：V1.0

---

## 一、支援格式

| 格式 | 方法 | 優先級 |
|---|---|---|
| **DWG** | ODA File Converter → DXF → ezdxf | P0 |
| **DXF** | ezdxf 直接讀取 | P0 |
| **PDF (向量)** | pdf2image + 向量提取 | P1 |
| **PDF (掃描)** | OCR 文字提取（僅文字，不做圖形辨識） | P2 |

---

## 二、DWG 處理流程

```
DWG 文件
    │
    ▼
[格式檢測]
    ├── DWG version 檢查 (AC1032 = R2018)
    ├── 文件大小檢查 (max 50MB)
    └── 完整性檢查 (magic bytes)
    │
    ▼
[ODA File Converter]
    DWG → DXF (R2018 ASCII)
    │
    ├── 成功 → DXF 文件
    │
    └── 失敗 → 錯誤分類
         ├── 版本不支持 → ERROR + 提示安裝新版 ODA
         ├── 文件損壞 → ERROR + 記錄
         └── ODA 未安裝 → FATAL + 安裝指引
    │
    ▼
[ezdxf Parser]
    DXF → Drawing Model
    │
    ├── 支援 Entity: LINE, CIRCLE, ARC, POLYLINE, LWPOLYLINE, TEXT, MTEXT, DIMENSION
    ├── 不支援: 3DSOLID, REGION, SURFACE, XREF
    └── 不支援 Entity → WARNING + 跳過
    │
    ▼
Drawing Model
```

### 2.1 錯誤處理矩陣

| 錯誤類型 | 級別 | Drawing.parse_status | 行為 |
|---|---|---|---|
| DWG 版本 >= R2013 | OK | success | 正常轉換 |
| DWG 版本 < R2013 | WARNING | partial | 嘗試轉換，可能遺失數據 |
| DWG 版本未知 | ERROR | failed | 無法處理 |
| 文件大小 > 50MB | WARNING | partial | 嘗試轉換 |
| 文件損壞 (CRC) | ERROR | failed | 記錄錯誤 |
| ODA 未安裝 | FATAL | failed | 終止，提示安裝 |
| ODA 轉換超時 (>60s) | ERROR | failed | 記錄並跳過 |
| 部分 Entity 不支援 | WARNING | partial | 跳過不支援類型，繼續 |
| 全部 Entity 不支援 | ERROR | failed | 記錄 |
| TEXT 編碼異常 | WARNING | partial | 嘗試多編碼 |

### 2.2 ODA 轉換命令

```bash
ODAFileConverter.exe \
    /i "input_dir" \
    /o "output_dir" \
    /in "DWG" \
    /out "DXF" \
    /ver 2018 \
    /f
```

### 2.3 轉換配置

```yaml
# config/cad-import.yaml
cad_import:
  dwg:
    converter: "ODAFileConverter"
    converter_path: "C:\\Program Files\\ODA\\ODAFileConverter\\ODAFileConverter.exe"
    target_format: "DXF"
    target_version: "2018"
    timeout_seconds: 60
    max_file_size_mb: 50

  supported_entities:
    - LINE
    - CIRCLE
    - ARC
    - POLYLINE
    - LWPOLYLINE
    - TEXT
    - MTEXT
    - DIMENSION
    - INSERT     # Block reference
    - HATCH      # Hatch pattern

  ignored_entities:
    - 3DSOLID
    - REGION
    - SURFACE
    - XREF
    - VIEWPORT
```

---

## 三、PDF 處理

### 3.1 向量 PDF

| 步驟 | 工具 | 說明 |
|---|---|---|
| 頁面轉圖片 | pdf2image (poppler) | PDF → PNG (300 DPI) |
| 文字提取 | pdfminer / PyMuPDF | 直接提取文字圖層 |
| 尺寸參考 | 手動標註 | 不做自動尺寸提取 |

### 3.2 掃描 PDF (OCR)

| 步驟 | 工具 | 說明 |
|---|---|---|
| 圖片預處理 | PIL/OpenCV | 去噪、二值化 |
| OCR 文字 | Tesseract (中文+英文) | 提取標註文字 |
| 結構化 | AI 輔助 (Phase 5) | 識別材料/技術要求 |

### 3.3 PDF Confidence

```python
class PdfConfidence(str, Enum):
    HIGH = "high"          # 向量 PDF，文字可直接提取
    MEDIUM = "medium"      # 混合 PDF（部分向量+部分圖片）
    LOW = "low"            # 掃描 PDF，OCR 結果
    UNUSABLE = "unusable"  # 無法處理（加密/損壞/純圖片無文字）
```

### 3.4 PDF 限制

| 限制 | 說明 |
|---|---|
| **不做圖形辨識** | PDF 僅提取文字，不從圖片中提取幾何 |
| **不做自動尺寸測量** | 尺寸需從 DWG/DXF 獲取 |
| **OCR 僅作輔助** | OCR 結果標記 source=AI，需人工確認 |

---

## 四、導入結果模型

```python
# domain/drawing.py (擴展)

class ImportResult(BaseModel):
    """Result of importing a CAD file."""

    source_file: str
    source_format: str         # "DWG" | "DXF" | "PDF"
    import_status: str         # "success" | "partial" | "failed"

    # Converted file (for DWG)
    converted_file: str | None = None  # Path to generated DXF

    # Drawing
    drawing: Drawing | None = None

    # Issues
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)

    # Timing
    import_duration_ms: float = 0.0
    conversion_duration_ms: float = 0.0

    # PDF-specific
    pdf_confidence: str | None = None
    ocr_text: str | None = None
```

---

## 五、Entity 支援範圍 (Phase 3)

### Phase 3.0 (第一版)

| Entity | 支援 | 提取內容 |
|---|---|---|
| LINE | ✅ | 端點座標 → 外形邊界 |
| CIRCLE | ✅ | 圓心 + 半徑 → 孔 |
| ARC | ✅ | 圓心 + 半徑 + 角度 → 圓角 |
| POLYLINE | ✅ | 頂點列表 → 外形/槽 |
| LWPOLYLINE | ✅ | 頂點列表 → 外形/槽 |
| TEXT | ✅ | 文字內容 + 位置 → 材料/技術要求 |
| MTEXT | ✅ | 文字內容 + 位置 → 材料/技術要求 |

### Phase 3.1 (後續)

| Entity | 支援 | 提取內容 |
|---|---|---|
| DIMENSION | ✅ | 標註文字 (參考) |
| INSERT | ✅ | Block 名稱 + 位置 |
| HATCH | ✅ | 剖面線區域 (材料識別) |

---

*本文件為 Phase 3 設計。實作在 Phase 3.0 完成。*
