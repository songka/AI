# Windows 可攜式展示包指南

## 啟動

1. 解壓或複製完整 `MechanicalQuotation` 目錄，不能只複製 EXE。
2. 可直接雙擊 `MechanicalQuotation.exe` 啟動 UI；無參數啟動即為 UI 模式。
3. 執行 `run_self_check.bat`，確認 HTML 報告全部通過。
4. 執行 `start_all.bat` 同時啟動 FastAPI 與 UI；Swagger 位於
   `http://127.0.0.1:8000/docs`。
5. 結束 API 時執行 `stop_api.bat`。

目前交付包預設使用本機 Python Software Foundation 簽章的 Python runtime 作為啟動器，
因 Trend Micro Apex One 會隔離未簽章的 PyInstaller bootloader。PyInstaller 後端仍可用於
具公司代碼簽章或 IT allow-list 的環境。請保留整個目錄，不能只拿走 EXE。
無主控台的 `MechanicalQuotation.exe` 負責 UI；同樣具 PSF 簽章的
`MechanicalQuotationConsole.exe` 由批次檔負責 API、自檢與 smoke。

## DeepSeek Key

Key 只可放在 `runtime/secrets/deepseek_api_key.txt`，一行純文字；此檔是 sidecar，
不在 EXE、Git、manifest 或設定檔中。沒有 Key 時 UI、規則報價、FastAPI 與 Excel 仍可運行，
只有 AI 功能顯示未設定。

## DWG 轉換器與中望 CAD

ODA File Converter 和中望 CAD 2011 均為外部第三方軟體，未包含在可攜包內。
如已取得合適授權，將本機 `ODAFileConverter.exe` 絕對路徑填入
`config/user_settings.json` 的 `dwg_converter_path`。中望 CAD 用於人工開圖核對，
不作自動化轉換依賴。本機以 administrative image 安裝在
`%LOCALAPPDATA%\MechanicalQuotation\ODAFileConverter-*\` 時，程式也會安全自動偵測。

批量掃描會把同圖號 DWG 與 PDF 配成一個任務：DWG 提供幾何，PDF 提供文字標註輔助；
PDF-only 任務不會臆測幾何。若任務失敗，表格「提示」欄會顯示第一條實際錯誤。

扫描 PDF 会先由 PyMuPDF 在本机渲染，再由 RapidOCR/ONNX Runtime 在本机识别文字；
模型随程序包提供，图纸不会因 OCR 上传到外部服务。矢量 PDF 仍优先直接提取文字。

## 自檢與 Smoke

- `run_self_check.bat`：檢查目錄、正式價、SHA256、UI、API、sidecar 與第三方隔離。
- `run_demo_smoke.bat`：執行一張示例 DXF 報價、17% 稅務及批量 Excel。
- 中文 HTML/JSON 報告輸出於 `runtime/reports/`，Smoke Excel 輸出於 `exports/`。
