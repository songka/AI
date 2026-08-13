# 供应商与原始报价维护说明

版本：1.0（2026-08-04）

## 1. 数据边界

- 供应商主档保存于 SMB `suppliers/suppliers.json`，支持新增、查询、编辑、停用和删除。
- 原始供应商报价保存于 `suppliers/prices/{供应商编号}/PR-*.json`，每笔独立文件、只允许新增，不允许覆盖。
- 已发布公司价格仍位于 `prices/published`，本页面和本接口不会直接修改正式公司价。
- 新录入的有效价格状态为“待审核”；未知价格必须留空保存为 `null`，禁止用 0 冒充价格。
- 有历史报价的供应商不能删除，只能停用；停用或黑名单供应商不能新增报价。

供应商 S 来源要进入正式 C 价格，必须经过下一里程碑的变更申请、管理员审批和版本发布。

## 2. 桌面操作

使用工程师或管理员账号登录，打开“供应商管理”。页面提供：

- 新增供应商；
- 编辑联系人、电话、质量等级和备注；
- 停用或删除无历史报价的供应商；
- 逐笔新增材料、型材、工序或表面处理报价；
- 导入供应商报价 Excel；
- 用表格查看供应商的不可覆写报价记录。

业务和查看者没有价格维护权限，界面不会显示写入按钮。

## 3. Excel 导入模板

第一行使用以下中文或英文列名：

| 必填 | 列名 | 示例 |
|---|---|---|
| 是 | 供应商编号 / supplier_id | SUP-TONGRUI |
| 是 | 价格类型 / target_type | MATERIAL |
| 依类型 | 材料代码 / material_code | SUS304 |
| 否 | 规格 / material_spec | 3mm |
| 依类型 | 工序代码 / process_code | CNC |
| 依类型 | 表面处理代码 / surface_code | RAL9003 |
| 是（未知可空） | 未税单价 / unit_price | 28.5 |
| 是 | 单位 / unit | kg |
| 否 | 生效日期 / effective_from | 2026-08-04 |
| 否 | 供应商报价单号 / quote_number | QT-20260804-01 |
| 否 | 是否含税 / tax_included | 否 |
| 否 | 税率 / tax_rate | 0.13 |

系统逐行导入，错误行不会阻断其他正确行；结果显示成功数、失败数和中文错误明细。每笔记录保存来源文件、工作表和价格单元格位置。

## 4. FastAPI

- `GET/POST /api/v1/admin/suppliers`
- `PATCH/DELETE /api/v1/admin/suppliers/{supplier_id}`
- `GET/POST /api/v1/admin/maintained-supplier-prices`
- `POST /api/v1/admin/maintained-supplier-prices/import`

查询要求 `price.view_cost`，写入要求 `price.modify`。接口在用户库尚未初始化时拒绝资料维护，不会创建无归属的本地资料。

## 5. 初始迁移

安全迁移工具：

```powershell
.\.venv\Scripts\python.exe tools\bootstrap_supplier_data.py
```

工具从现有已审计价格来源包迁移供应商主档；如果 `suppliers.json` 已存在则直接跳过，不覆盖用户维护资料，也不修改 Published Pricebook。
