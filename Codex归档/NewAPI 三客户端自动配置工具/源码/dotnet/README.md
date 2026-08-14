# NewAPI Client Configurator (.NET)

这是 Windows 桌面重写版（WPF），替代原 WinForms 工程。

## 工程结构

- `src/NewAPIClientConfigurator.Core` — 核心逻辑：模型扫描、协议探测、配置生成、备份恢复（UI 无关）
- `src/NewAPIClientConfigurator.App` — WPF 界面：主窗口、预览对话框、备份选择对话框、展示模型

## Build

```powershell
cd dotnet
C:\Program Files\dotnet\dotnet.exe build
```

## Publish a single-file exe for Windows 10

```powershell
cd dotnet
C:\Program Files\dotnet\dotnet.exe publish src\NewAPIClientConfigurator.App\NewAPIClientConfigurator.App.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true
```

The published executable will be under the `bin\Release\net8.0-windows\win-x64\publish` folder.

## 审核评估

`../review/` 存放多 agent 审核 prompt 与轮次运行脚本。外部 codex CLI 子进程环境不稳定时，
可在主对话内按多角色（架构/安全/WPF UX/QA）完成审核-修复迭代。
