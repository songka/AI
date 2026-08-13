# Windows x64 可执行版本

`AICodingSessionManager-win-x64-self-contained.zip` 包含 Windows x64 自包含单文件版本，目标电脑无需单独安装 .NET 8 Runtime。

解压后运行 `AICodingSessionManager.exe`。

SHA-256：`BCAA55B0D4BEDC8C1AFF5B8A13553E7CCF5C5D0CDF79DE815FF6677742ADF1C0`

本文件由以下命令从通过测试的源码生成：

```powershell
dotnet publish .\src\AICodingSessionManager.UI\AICodingSessionManager.UI.csproj `
  -c Release -r win-x64 --self-contained true --no-restore `
  -p:PublishSingleFile=true `
  -p:IncludeNativeLibrariesForSelfExtract=true `
  -p:DebugType=None `
  -o .\release\win-x64
```

`release/win-x64/` 是本地临时发布目录，不纳入源码仓库。
