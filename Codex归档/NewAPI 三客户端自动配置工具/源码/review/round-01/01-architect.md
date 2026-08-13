# 架构与正确性审核报告

## 结论
**NEEDS_FIX** — 未发现 P0（崩溃/数据损坏）级别问题，但存在 2 个 P1 级风险（`async void` 未受保护异常路径、子进程管道死锁挂起）及若干 P2 改进项。

**构建说明**：本 agent 沙箱为只读，实际尝试执行了 `dotnet build dotnet\NewAPIClientConfigurator.sln --no-restore`——`Core` 项目编译通过，`App` 在 `MarkupCompilePass1` 写 `obj\...\MarkupCompile.cache` 时因 `UnauthorizedAccessException` 失败，属沙箱禁止写盘所致而非代码错误。因此按约定声明：**构建未在 agent 内完整执行**（环境不允许写盘）。

## 发现的问题

### [P1] async void 事件处理器存在未受保护的异常路径，可能直接崩溃进程
- 文件: `dotnet/src/NewAPIClientConfigurator.App/MainWindow.xaml.cs:157`、`MainWindow.xaml.cs:168`
- 问题: `OnApplyClick` 中 `AppPaths.SaveToken(TokenBox.Password)`（DPAPI + 文件写）与 `OnRestoreClick` 中 `AppPaths.ListBackups()`（目录枚举）都位于 `RunBusyAsync` 的 try/catch 之外。这两处 IO/DPAPI 调用一旦抛异常（磁盘权限、配置文件损坏、DPAPI 不可用等），异常会从 `async void` 处理器逃逸，WPF 默认终止整个进程。项目其他路径都刻意用 `RunBusyAsync` 包裹，此处属于不一致且后果最严重（进程崩溃）。
- 建议: 把这两处调用也移入 `RunBusyAsync`（或在 `App` 挂 `DispatcherUnhandledException` 兜底），保证所有 `async void` 处理器内无未捕获异常。

### [P1] `VerifyOpenCodeAsync` 顺序读取 stdout 再读 stderr，存在管道死锁且无超时
- 文件: `dotnet/src/NewAPIClientConfigurator.Core/Service/Configurator.cs:275-277`
- 问题: `ReadToEndAsync(stdout)` 完成后才读 `stderr`。若 `opencode debug config` 向 stderr 输出超过匿名管道缓冲（Windows 默认约 4KB–64KB），子进程会阻塞在写 stderr 上、永不关闭 stdout，`ReadToEndAsync(stdout)` 永不完成；而调用方传入的是 `CancellationToken.None`（MainWindow.xaml.cs:160），无超时无取消，操作会无限挂起（按钮永久禁用）。恰好在"配置出错需要验证"的场景下 stderr 最可能输出大量错误，触发概率并非可以忽略。
- 建议: 用 `Task.WhenAll(ReadToEndAsync(stdout), ReadToEndAsync(stderr))` 并行读两个流，或先 `WaitForExitAsync` 再读；并给整个验证加 `CancellationTokenSource.CancelAfter` 超时。

### [P2] `MetadataResolver` 为每个模型重复下载整个 models.dev api.json，无缓存
- 文件: `dotnet/src/NewAPIClientConfigurator.Core/Service/GatewayClient.cs:121-135`（调用处 `Service/ModelScanner.cs:80`）
- 问题: `ScanOneAsync` 对每个模型都调用 `ResolveAsync`，每次都新建 `HttpClient` 全量拉取 `https://models.dev/api.json`（数 MB），并发扫描时最多 8 路同时下载；同一批模型、每次重新扫描都会重复拉取。数据是相对静态的公共元数据，浪费带宽并拖慢探测。
- 建议: 增加进程内（或跨运行）缓存，只下载一次并复用；`HttpClient` 建议用静态共享实例 + 短超时。

### [P2] `DetectOpenCodeAdapter` 同步阻塞 UI 线程（最长 5 秒）
- 文件: `dotnet/src/NewAPIClientConfigurator.Core/Service/Configurator.cs:222-243`
- 问题: `WriteOpenCodeAsync` 的第一个 await 之前同步执行 `Process.Start` + `StandardOutput.ReadToEnd()` + `WaitForExit(5000)`。该方法在 `RunBusyAsync` 的 UI 线程上下文中执行，因此整个 `opencode --version` 探测期间 UI 冻结；若 opencode 卡住，最长冻结 5 秒。
- 建议: 将版本探测改为 `Task.Run` 或异步读取，超时用 `WaitForExitAsync(ct)`；`WaitForExit(5000)` 的超时结果目前也未被处理（进程未退出时仍按 V1 处理，逻辑可接受但应显式）。

### [P2] Codex TOML 写入未转义 `base_url`
- 文件: `dotnet/src/NewAPIClientConfigurator.Core/Service/Configurator.cs:217`
- 问题: `$"base_url = \"{gatewayUrl}/v1\""` 直接把用户输入的 URL 内插进 TOML 基本字符串。若 URL 含 `"` 或 `\`，会生成非法 TOML 并覆盖用户真实的 `~/.codex/config.toml`，导致 Codex 配置损坏。`ValidateConnection` 只检查非空，不校验 URL。
- 建议: 写前校验（`Uri.TryCreate` 且不含引号/反斜杠），或对 TOML 字符串做转义。

### [P2] 与 README 的 eligibility 描述不一致
- 文件: `dotnet/src/NewAPIClientConfigurator.Core/Core/Models.cs:73-88` 与根 `README.md:20-21`
- 问题: README 声称"模型只有在目标客户端所需协议通过 text、streaming、tool-call 探测后才合格"，但实现中 `ClaudeCompatible` 只要求 Messages 的 text+streaming，`OpenCodeCompatible` 只要求 Chat/Responses 的 text+streaming，二者均不检查 `Tools`（只有 `CodexCompatible` 检查 Tools）。`Configurator.Preview` 内的条件文案与实现自洽，但与根 README 的表述不符。
- 建议: 统一两者——要么对 Claude/OpenCode 也要求工具调用探测通过，要么更新 README 说明"工具调用仅 Codex 必需"。

### [P2] 重复代码与死字段
- 文件: `dotnet/src/NewAPIClientConfigurator.App/MainWindow.xaml.cs:293`（与 `Core/Service/ModelScanner.cs:602` 的 `DisplayName` 实现完全重复）；`MainWindow.xaml.cs:14/274` 的 `_busy` 只写不读
- 问题: `DisplayName` 的字符串格式化逻辑在两处各实现一份，后续改动易分叉；`_busy` 字段是死代码。
- 建议: 提取到 Core 共享静态方法；删除 `_busy`（`SetBusy` 内部无需该字段）。

### [P2] XAML 硬编码默认网关地址
- 文件: `dotnet/src/NewAPIClientConfigurator.App/MainWindow.xaml:37`
- 问题: 默认值 `http://10.97.144.27:3000` 是具体内网 IP，硬编码在 XAML 中，与仓库/环境耦合，且随分发泄露内网拓扑信息。
- 建议: 默认留空或占位符；`OnLoaded` 时用缓存/上次值回填。

### [P2] 细节观察（非缺陷，建议改善）
- 文件: `dotnet/src/NewAPIClientConfigurator.Core/Service/ModelScanner.cs:223-258`、`:25`
- 问题: `ProbeContextAsync` 在内层 `foreach` 结束后紧跟 `return;`，实际只会对"第一条 text 确认的路由"做上下文探测（responses 优先）。结果语义正确（ContextVerifiedMin 是模型级指标），但 `return` 位置容易让人误以为三条路由都会测，建议加注释或改写为显式 `break` + `return`；`SemaphoreSlim gate` 是局部对象未 `Dispose`（无实际资源泄漏，建议 `using` 保持整洁）。

## 优点
- **分层清晰**：Core 完全不含 WPF/UI 依赖（仅 `System.Drawing` 用于生成探测图片，属探测载荷的一部分），App 通过 `InternalsVisibleTo`（`Core.csproj` 对 `NewAPIClientConfigurator` 程序集）访问 internal 类型，程序集名与 App 的 `AssemblyName` 匹配，配置正确；未发现 UI 逻辑泄漏进 Core。对双项目桌面应用而言，用 IVT 而非公开 API 是合理取舍。
- **异步/线程安全整体正确**：网络与扫描全程 `async/await` + `ConfigureAwait(false)`，无 UI 线程上的 `.Result/.Wait()` 阻塞（唯一例外是已列为 P2 的 `DetectOpenCodeAdapter`）；`RunBusyAsync` 统一处理按钮禁用、异常捕获与恢复；`Log` 通过 `Dispatcher.BeginInvoke` 回写，扫描回调跨线程安全；扫描失败单模型降级（写入 Error 并继续），不拖垮整体。
- **资源管理良好**：`NewApiGateway`（`await using` 释放 `HttpClient`）、各 `JsonDocument`/`JsonNode`/`StreamReader`/`response` 均正确释放；token 与备份密钥用 DPAPI `CurrentUser` 加密落盘，不落明文。
- **备份/恢复完整且对称**：`CreateBackup` 覆盖 3 个客户端配置文件 + 6 个相关用户环境变量（密钥类加密存储），`RestoreBackup` 按 manifest 还原文件（含"原先不存在则删除"的语义）与全部环境变量，与 `Configurator` 各 `WriteXxx` 的设置面一致。
- **正确性细节到位**：探测先于写入、写入前强制备份、预览（`Preview`）与落盘（`ApplyAsync`）共用同一 `Eligible` 判定避免不一致；缓存加载 + 24 小时过期提醒；`ModelFilters` 与 `ModelCapability.IsExcluded` 双层过滤 `codex-auto-review`；`ConcurrencyBox` 并发值被钳制在 1–8。
- **可维护性亮点**：`OpenCodeAdapter` 用 record + RootKey 抽象 V1/V2 差异，`Body` 工厂方法按协议封装探测载荷，职责单一，命名清晰。