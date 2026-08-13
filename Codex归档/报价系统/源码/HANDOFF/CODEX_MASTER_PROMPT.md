# MechanicalQuotation — Codex完整接管任務

你現在接管「機械加工件智能報價系統」的完整開發工作，不是只修一個DWG問題。

## 0. 先恢復基準

先讀取：

- `docs/CURRENT_HANDOFF.md`
- `HANDOFF/TRANSFER_INFO.md`（若存在）
- `git status --short`
- `git log -15 --oneline`
- `pyproject.toml`
- `.gitignore`
- `src/quotation/`
- `tests/`
- `rules/`
- `data/current-version-pointer.json`
- Published Pricebook snapshot
- `runtime/config/`

先完成：

1. 重建`.venv`並安裝依賴。
2. 執行全部測試。
3. 實際啟動UI。
4. 啟動FastAPI並檢查health及Swagger。
5. 確認DeepSeek key被Git忽略。
6. 確認工作目錄乾淨。

目前基準約為：

```text
656 passed, 2 skipped
```

若基準不同，先處理搬遷、依賴、路徑或環境問題，不要為了變綠而修改業務測試預期。

## 1. 敏感資訊

DeepSeek配置：

```text
Base URL: http://10.97.144.27:3000/v1
Model: deepseek-v4-flash
Key: runtime/secrets/deepseek_api_key.txt
```

此Key是報價軟體的DeepSeek key，不是Codex登入憑證。

禁止：

- 顯示或打印Key
- 把Key寫入程式、YAML、JSON、日誌、Exception、Swagger、Excel或API回應
- 把Key提交Git
- 在pytest中真實消耗DeepSeek token
- 保存或展示`reasoning_content`

自動測試全部使用Mock；只有人工整合驗證可真實調用一次。

## 2. 已完成能力

- Published Company Pricebook與來源追溯
- 所有公司價格為未稅價
- 17%稅務
- Quote cost completion
- Tkinter UI
- 外部文件掃描與配對基礎
- 批量報價UI
- 單件及批量Excel
- FastAPI及Swagger
- DeepSeekClient及UTF-8中文
- Secret相對路徑
- SQLite報價記錄基礎
- 系統自檢與Smoke Test
- 中文使用者顯示名稱

UI：

```powershell
.\.venv\Scripts\python.exe -m quotation.ui.demo_app
```

API：

```powershell
.\.venv\Scripts\python.exe -m uvicorn quotation.api.main:app --host 127.0.0.1 --port 8000
```

## 3. 核心規則

所有材料、加工、表面處理價格均為未稅價：

```text
price_basis=EXCLUDING_TAX
```

稅率：

```text
17%
```

公式：

```text
tax_amount = subtotal_excluding_tax * Decimal("0.17")
total_including_tax = subtotal_excluding_tax * Decimal("1.17")
```

未知價格不能顯示為0。

普通UI不得顯示`C/U/AI-EST/COMPLETE/PUBLISHED_COMPANY_PRICEBOOK`等內部代碼，必須顯示中文名稱。

DeepSeek只做圖紙文字、材料、表面處理、熱處理、厚度、圖號及缺失資訊建議。它不得決定正式價格、覆蓋公司價格、修改Pricebook，且AI建議預設`accepted=false`。

## 4. 開發紀律

- 一次只做一個原子任務。
- 每項先確認失敗測試，再最小修改。
- 每項執行相關測試和全部測試。
- 每項更新`docs/CURRENT_HANDOFF.md`。
- 每項建立獨立本地Commit。
- 不執行`git reset --hard`、`git clean`、大量刪除、強制checkout/restore或推送遠端。
- 單一外部文件失敗不得阻斷整批。
- 不得修改既有測試預期掩蓋Bug。

# 5. 完整剩餘路線

按順序執行，每個Milestone完成後建立Checkpoint Commit。

## Milestone 1：DWG正式支援

目前DWG可掃描和配對，但顯示「暫不支持此文件格式」。

正確架構：

```text
DWG -> 可插拔外部轉換器 -> 暫存DXF -> 現有DXF Parser -> 現有Quotation Pipeline
```

禁止自行實作完整DWG二進制解析器。

建立：

- `DwgConverter`
- `DwgConversionService`
- ODA或其他可配置Adapter
- health check
- 快取
- UI中文狀態
- `/api/v1/dwg/health`
- Excel轉換Trace

轉換器尋找：

1. `MECHANICAL_QUOTATION_DWG_CONVERTER`
2. `runtime/config/user_settings.json`
3. Windows常見安裝位置

不得自動下載第三方工具，也不得在未確認授權時打包第三方二進制。

測試：成功、未配置、不可用、超時、失敗、空DXF、中文/空格路徑、單件失敗不影響整批、快取、API、UI、Excel Trace、原DWG不修改。

Commit：

```text
feat: add pluggable DWG to DXF conversion workflow
```

## Milestone 2：真實外部圖紙閉環

至少驗證：

- 2個外部DWG或DXF
- 2個外部PDF
- 1個多圖紙資料夾

完成掃描、配對、批量解析、AI建議、正式報價、完整/待確認分類、17%稅務、批量Excel、Swagger上傳和中文錯誤原因。

Commit：

```text
test: validate external drawing quotation workflow
```

## Milestone 3：報價準確度

每項獨立Commit。

### 3A W002

修正SPCC被強制2mm、0.35mm變0、過早四捨五入。使用Decimal並追蹤面積、厚度、體積、密度、重量、單價、金額。

```text
fix: preserve sheet metal thickness and material precision
```

### 3B W001

將`40*40/40×40/40X40/40x40`統一為`40x40`。Published價48 CNY/m；5.2m為249.60。

```text
fix: normalize and price aluminum profiles
```

### 3C J029

無孔薄板不得因CNC base hours產生40元；按SHEET_METAL路由，沒有加工證據不得加CNC費。

```text
fix: avoid unsupported CNC charges for sheet metal parts
```

### 3D J001

不得將整個Bounding Box當實心重量。無法從2D可靠分解時重量未知，狀態需人工審核。

```text
fix: require review for unresolved weldment structure weight
```

## Milestone 4：價格發布品質

### 4A origin_supplier_id

修復admin review到publication時供應商ID遺失。不得在Resolver硬編碼供應商。

```text
fix: preserve supplier provenance during price publication
```

### 4B RAL9003

通過正式發布流程加入25 CNY/m²未稅公司價；Draft不得當正式價。

```text
feat: publish RAL9003 company surface price
```

### 4C TAP Draft

保持「舊版草稿規則，需人工確認」警告；未審核前不得偽裝成公司價格。

## Milestone 5：管理與人工審核

完善：

- 報價記錄搜尋、篩選、明細及重新匯出
- Published Pricebook唯讀查詢
- 供應商報價唯讀查詢
- Pending不能用於正式Resolver
- 人工審核工作台
- 材料、厚度、尺寸、表面處理、加工方式與人工價格補充
- 人工價格來源`M`，UI顯示「人工確認價格」
- 人工價格只對當前Quote/Job生效，不寫入Pricebook
- 保留修改前後、原因、操作者、時間與Quote版本

Commit：

```text
feat: complete quotation management and manual review workflow
```

## Milestone 6：Windows可攜式包

PyInstaller `--onedir`，Key保持sidecar secret，不嵌入EXE。

目標：

```text
dist/MechanicalQuotation/
  MechanicalQuotation.exe
  runtime/secrets/deepseek_api_key.txt
  config/
  exports/
  start_ui.bat
  start_api.bat
  start_all.bat
  stop_api.bat
```

建立打包工具、系統自檢、Demo smoke、中文HTML報告、展示指南與Checklist。第三方DWG轉換器不得在未確認授權時打包。

```text
feat: build portable Windows quotation demo package
```

## Milestone 7：全量驗證

執行全部測試、20個Golden Dataset、外部圖紙、UI/API/AI、批量Excel、Secret檢查、敏感資訊掃描與可攜式包Smoke。

報告包含：

- 測試總數
- Quote Ready、Review Required、Parse Failed
- WAPE、MAE、Median absolute deviation
- <=10%、<=20%、<=30%、>30%
- 各案例偏差原因
- 價格/規則版本
- Snapshot SHA256
- 外部圖紙統計
- 未稅/含稅驗證
- UI/API/AI狀態
- 未解決風險

```text
docs: finalize quotation system validation and handoff
```

## 6. 每個Milestone回報

只回報：

1. 目標或根因
2. 修改文件
3. 新增測試
4. 全部測試結果
5. 真實文件驗證
6. UI/API/Excel結果
7. Commit hash
8. git status
9. 尚未完成事項

詳細內容寫入`docs/CURRENT_HANDOFF.md`。完成全部Milestone後停止，不推送遠端。
