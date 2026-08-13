# SMB 登录与临时账户

管理 Skill 先自动复用当前 Windows SMB 会话，并通过 `Get-SmbConnection` 取得实际
账户。共享根目录不可访问或身份不可确认时，只显示独立登录入口，停止其他动作。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<skill>\scripts\secure-login.ps1"
```

> 从 `1.0.6` 起，身份确认先使用 `Get-SmbConnection`。如果非域电脑没有显示
> 有效连接，再由 Windows 网络提供程序 `WNetGetUser` 查询
> `\\10.97.0.210\lfaf_Engineer` 当前实际绑定的账号。两种方式都不读取聊天、
> 环境变量或用户自报账号；两者都无法确认时，特权操作继续拒绝执行。

- 输入 `zhangsan` 时自动改为 `GETACAD\zhangsan`。
- 已包含 `域\账户` 或 UPN 的输入保持不变。
- 临时使用其他账户也运行该脚本，账号与密码只在独立窗口输入。
- 登录脚本使用 `net use ... * /persistent:no`：密码由独立控制台隐藏读取，连接保留
  在当前 Windows 用户会话，但不会在下次登录时自动恢复。
- 不使用 `New-PSDrive`，因为它只在启动它的 PowerShell 进程内有效，窗口关闭后
  AI 的后续进程无法复用。
- 不要把凭据发给 AI，也不要把密码写在命令行。
- 若 Windows 报告同一服务器已有其他账户连接，应先关闭相关资源管理器窗口并清理
  冲突连接，再在独立窗口登录。

草稿自动备份不检查 Hub 角色，但 SMB 文件服务必须允许当前连接账户创建对应文件。

若共享根目录可访问，但 `AI-Assets\registry.json` 尚不存在，Skill 应返回
`setup_required`，明确提示管理员初始化 Hub，而不是再次要求用户登录。

`hub.ps1` 在自己的 PowerShell 进程里再次检查 `Get-SmbConnection`。如果只能读取
共享文件、却没有可验证的 SMB 用户名，它会在当前本地窗口调用安全登录；确认实际
账户后才执行 `accounts`、`review`、`publish` 等特权命令。

若 Windows 报告“不允许一个用户使用一个以上用户名与服务器建立多重连接”，说明
当前登录会话已经用其他身份访问 `10.97.0.210`。安全登录脚本会在本地询问；只有
用户输入 `Y`，才断开指向该服务器的连接并重试。它不会断开其他文件服务器，也不会
自动确认。

删除候选连接时，某个共享返回“找不到网络连接”属于正常情况，脚本会检查退出码并
继续处理同服务器的其他连接，不应因此终止整个登录流程。

交互式 `net use` 会在控制台输出密码提示和“命令成功完成”。脚本通过
`Start-Process -NoNewWindow -PassThru` 读取唯一的整数退出码，不能把控制台提示
文字混入函数返回值，否则会把成功的退出码 `0` 误判为失败。
