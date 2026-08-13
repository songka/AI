# 給 Claude Code：直接匯入規則包

不要再重新解析原始Excel。請以本資料夾內：

- `pricing-rules-excel-r01-v1.0.yaml` 為主要來源
- `pricing-rules-excel-r01-v1.0.json` 作為精確資料校驗
- `pricing-rules-excel-r01-v1.0.schema.json` 作為基本結構校驗

執行 Phase 4.6.3 — Source-aware Pricing Rules Import。

## 1. 匯入方式

- 使用 IMPORT_OVERLAY，不得覆蓋或刪除目前已發布的C規則。
- `active_company_rules` 保留現有規則。
- `pricing_source_records` 匯入供應商/內部價格來源庫。
- `supplier_master` 匯入供應商主檔。
- `legacy_rate_records`、`legacy_formula_rules`、`tax_profiles` 只作歷史追溯。

## 2. 價格來源

完整保留：C / H / E / S / AI-WEB / AI-EST / AI-HYBRID / M / U。

- S：供應商報價
- H：歷史/內部價格簿
- E：估算或內部費率簿
- C：管理員審核後發布的公司價格

禁止把S/H/E自動升級為C。

## 3. 價格選擇

預設：COMPANY_DEFAULT。
沒有公司預設時：MANUAL。
不得在未配置策略時自動取最低價或平均價。

每次選價必須保存候選記錄、選中記錄、供應商、策略、原因、生效日期、稅務狀態與來源單元格。

## 4. 稅

- 工作表2來源：tax_inclusion_status=UNKNOWN。
- 工作表1兩張材料表：EXCLUDED。
- Excel歷史17%只作LEGACY_REFERENCE_ONLY。
- 現有13%保持disabled，等待管理員確認。
- Quote分開保存 subtotal_excluding_tax、tax_amount、total_including_tax。
- 稅務狀態UNKNOWN時不得自動加稅或假設未稅。

## 5. 必須阻止發布的記錄

- CONFLICT
- UNIT_CONFLICT
- UNKNOWN_PRICE
- AMBIGUOUS_MATERIAL_SPEC
- 無effective_from
- tax_inclusion_status=UNKNOWN且公司政策未決定

## 6. 供應商管理

實作或對接：

- SupplierRepository
- SupplierPriceRepository
- SupplierPriceImportService
- SupplierPriceValidationService
- PriceSelectionService
- PricePublicationService
- SupplierChangeRequestService

SMB只保存版本快照與append-only change log；本地SQLite作Cache；不得多人共享寫中央SQLite。

## 7. 未知價格

`amount=None/null`，不得使用0.00表示未知。未知項不加入可支付合計，但Quote必須標記INCOMPLETE。

## 8. 測試

至少驗證：

1. YAML與JSON均能載入，記錄數為96。
2. 供應商主檔為6個；富裕昌價格記錄為0。
3. A6061-T6三家價格28/35/25完整保留。
4. PC=60，來源工作表2 L7。
5. 鈹銅180/130/220/170完整保留。
6. 亞克力30/28/25完整保留。
7. 30x30鋁型材=30/m；40x40=48/m；20x30未知。
8. SUJ2通瑞兩筆為CONFLICT。
9. 隔熱板為UNIT_CONFLICT。
10. 捷密達S50C/S45C為AMBIGUOUS_MATERIAL_SPEC。
11. 工作表2稅務狀態為UNKNOWN；工作表1未稅表為EXCLUDED。
12. 未審批S不能轉C。
13. 17%與13%稅務設定不互相覆蓋。
14. 未知金額使用None/null而不是0。
15. 現有512項回歸測試及新增匯入測試全部通過。

## 9. 完成後輸出

- 實際修改文件清單
- 匯入記錄數與各狀態數
- 供應商主檔與價格記錄統計
- 新增測試數與總測試數
- 尚待管理員確認項目

本階段不要重跑20件報價Validation，也不要發布新Price Version。先完成資料庫/檔案匯入與測試，等待管理員選定公司C價格。
