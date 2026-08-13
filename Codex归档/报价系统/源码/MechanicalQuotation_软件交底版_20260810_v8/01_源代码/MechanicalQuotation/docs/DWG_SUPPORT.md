# DWG 支援與轉換器配置

系統不直接解析 DWG 二進位格式，也不會自動下載第三方工具。DWG 報價流程固定為：

```text
原始 DWG（唯讀） → 外部轉換器 → runtime/cache/dwg/*.dxf → 既有 DXF Parser → 報價管線
```

## 配置優先順序

1. 環境變數 `MECHANICAL_QUOTATION_DWG_CONVERTER`
2. `runtime/config/user_settings.json` 的 `dwg_converter_path`
3. Windows 常見 ODA File Converter 安裝位置
4. `PATH` 中的 `ODAFileConverter`

`runtime/config/user_settings.json` 範例：

```json
{
  "dwg_converter_path": "C:\\Program Files\\ODA\\ODAFileConverter\\ODAFileConverter.exe"
}
```

也可複製 `config/user_settings.example.json` 到 `runtime/config/user_settings.json` 後修改。

## 健康檢查

啟動 API 後請求：

```text
GET /api/v1/dwg/health
```

回應只包含是否配置、是否可用、adapter 名稱、配置來源與快取目錄，不會執行轉換器。

## 安全與授權

- 原始 DWG 不會傳給外部 adapter；系統先建立隔離副本，避免第三方工具修改原檔。
- 轉換結果按原檔內容與 adapter identity 建立 SHA-256 快取。
- 單一轉換失敗、超時、取消或產生空 DXF 時，只標記該任務失敗，不中斷整批。
- ODA 或其他第三方二進位必須由使用者自行合法安裝；本專案不下載也不打包它。

## SOLIDWORKS 原生文件边界

- 当前扫描器已接受 `.SLDDRW/.SLDPRT`。本机安装并合法激活 SOLIDWORKS 后，系统会通过
  Windows COM 自动化接口静默打开原文件、另存为隔离缓存 DXF，再进入同一报价管线。
- ODA File Converter 是 DWG/DXF 转换器，不负责把 SOLIDWORKS 原生文件转换为 DXF。
- 本机目前未检测到 SOLIDWORKS 安装或对应 COM 注册，因此代码链已接通，但此电脑尚不能
  实际转换原生文件；中望 CAD 2011 不能替代 SOLIDWORKS 原生几何转换链。
- 现阶段请从 SOLIDWORKS 将 `.SLDDRW` 导出为 `.DXF/.DWG`，并同时导出 `.PDF` 保留标题栏、
  材料和工艺备注；`.SLDPRT` 应先生成工程图或导出可验证的二维 DXF。文件名如
  `零件.SLDPRT.PDF` 可以作为 PDF 辅助资料读取，但不是直接解析 SLDPRT。
- 适配器不会修改原文件，转换结果按文件内容缓存；转换失败会明确提示安装/注册状态。正式
  宣布现场可用前，仍必须在安装 SOLIDWORKS 的电脑上用真实 `.SLDDRW/.SLDPRT` 做验收。
