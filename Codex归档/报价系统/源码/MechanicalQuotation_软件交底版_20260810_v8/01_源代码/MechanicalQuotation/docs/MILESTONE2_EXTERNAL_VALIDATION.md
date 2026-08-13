# Milestone 2：真實外部圖紙閉環驗證

驗證日期：2026-08-03（Asia/Shanghai）

## 驗證結論

Milestone 2 通過。兩組真實 DWG/PDF 由資料夾掃描正確配對，經 ODA 轉換、DXF
解析、PDF 文字抽取、正式報價、17% 稅務與批量 Excel 匯出完成閉環；相同檔案也經
實際 FastAPI 服務按 Swagger 的 `multipart/form-data` 規格上傳成功。

## 第三方轉換器

- 來源：ODA 官方下載頁的 `ODAFileConverter_QT6_vc16_amd64dll_27.1.msi`
- MSI SHA-256：`3D5961F510CF95F398B8E2920899DC8E8C51ADECDAF5B20A40B3D1A29269DE81`
- Authenticode：Valid；簽署者 `OPEN DESIGN ALLIANCE`
- 版本：27.1；本機每使用者路徑：
  `C:\Users\lfaf-test\AppData\Local\MechanicalQuotation\ODAFileConverter-27.1`
- 原 MSI 固定為全機器安裝且本帳號無管理員權限（Error 1925）；改用 Windows Installer
  administrative image 部署至 LocalAppData，不寫全機器安裝登錄。
- 執行檔路徑只寫入 ignored 的 `runtime/config/user_settings.json`；第三方二進位、下載包、
  快取及 DeepSeek Key 均未加入 Git。
- ODA 免費工具的非會員授權限制需由公司確認；本次只作本機技術驗證，不納入 Windows
  發布包，也不代表已取得商業散布或使用授權。
- 另偵測到使用者安裝的中望 CAD 2011（11.0.0.1125），位於
  `C:\Program Files (x86)\ZWCAD 2011 Chs\ZWCAD.EXE`。此舊版 GUI 執行檔未具
  Authenticode 簽章，現階段只作人工開圖備援，不取代已通過自動化實測的 ODA adapter。

## 真實資料矩陣

| 圖號 | 幾何圖 | 輔助圖 | 配對 | PDF 文字區塊 | 結果 | 未稅 | 17% 稅額 | 含稅 |
|---|---|---|---|---:|---|---:|---:|---:|
| UC1000005854-J003 | DWG | PDF | MATCHED | 195 | COMPLETE | 1046.42 | 177.89 | 1224.31 |
| UC1000005855-J005 | DWG | PDF | MATCHED | 94 | COMPLETE | 323.91 | 55.06 | 378.97 |

- 兩份 DWG 均轉出非空 DXF，專案 health 為 `configured=true, available=true`。
- 來源檔案轉換前後 SHA-256 全部相同；服務只處理隔離副本與快取。
- 多圖紙資料夾包含 2 DWG + 2 PDF，掃描結果精確為 2 個 bundle，沒有混入歷史上傳。
- 批量 Excel 含 Summary、Quote Details、Review Required、Source Files、Trace 及
  DWG Conversion Trace 工作表。

## AI、待確認與中文錯誤

- J003/J005 的必需欄位已由圖紙完整識別，因此 AI 路徑正確地不生成臆測建議。
- 另以真實 `UC2020083221-W001.DWG/.pdf` 及可重現、無網路的 AI stub 驗證：缺少
  material 時產生候選與「需人工審核，不自動套價」警告；建議只記錄，不直接改價。
- DeepSeek 的一次真實健康與結構化抽取已在接管基準完成，本 Milestone 不重複消耗 API，
  且全程未輸出 Key 或 reasoning content。
- PDF-only Swagger 批次返回 `UNSUPPORTED`，中文原因為：
  `找不到可用的DWG或DXF幾何圖紙`。

## Swagger / FastAPI 實測

- 實際啟動 Uvicorn，`/openapi.json` 確認 batch-upload request body 為
  `multipart/form-data`。
- 上傳四個檔案後回應：`total=2, complete=2, failed=0`。
- `/api/v1/jobs/{batch_id}` 保留原檔名與正確 DWG/PDF 配對。
- `/api/v1/jobs/{batch_id}/excel` 成功下載非空 Excel（11,268 bytes）。

可重跑的 live API 驗證客戶端：`tools/validate_external_api.py`。運行產物保存在 ignored 的
`runtime/validation/`。

## 自動測試

```text
677 passed, 1 warning in 51.17s
```

warning 為 Starlette TestClient 對 `httpx` 的上游棄用提示，無測試失敗。
