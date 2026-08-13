# MechanicalQuotation Excel R01 規則匯入包 V1.0

## 主要文件

- `pricing-rules-excel-r01-v1.0.yaml`：Claude/程式使用的主要規則與來源資料。
- `pricing-rules-excel-r01-v1.0.json`：與YAML等價，適合程式精確解析。
- `supplier-master-r01-v1.0.json`：6個供應商主檔（富裕昌保留主檔但不虛構價格）。
- `validation-summary.json`：數量與阻塞問題。
- `CLAUDE_IMPORT_INSTRUCTIONS.md`：直接交給Claude Code的任務說明。

## 原始來源

- 文件：`3.0報價表-R01（機構預估價格）(3).xlsx`
- SHA256：`2b9ee60926da63ef74a1a044c1e78d02928ee115173f484034bbcce9eda6d950`
- 選定價格表逐格記錄：96筆
- 工作表1歷史費率：18筆

## 使用原則

1. 本包採 `IMPORT_OVERLAY`，不得直接覆蓋目前的公司正式C規則。
2. 供應商價格使用 `S`，內部歷史價格使用 `H`，工作表2加工/表處候選費率使用 `E`。
3. 所有新來源價格均未提供生效日期；工作表2亦未說明含稅狀態，所以目前可發布數量為0。
4. 稅金與成本分離。Excel的17%僅保存為歷史規則；目前13%保持停用並要求管理員確認。
5. 未知價格在程式中應使用 `None/null`，不可用0元偽裝已定價。
