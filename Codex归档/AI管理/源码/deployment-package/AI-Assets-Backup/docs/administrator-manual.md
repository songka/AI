# 管理员操作说明书

## 1. 管理员职责

管理员负责：

- 初始化公共槽、备份权威槽和静态网页。
- 分配管理员、审核者、发布者、使用者账户。
- 验证正式索引、制品哈希和双槽状态。
- 监督候选审核、正式发布、镜像和恢复。
- 处理 Git 草稿分叉、SMB 人工修改和客户端故障。

管理员也拥有普通使用者的 `view`、`pull`、`activate`、提交和自动草稿备份功能。

## 2. 首次安全部署

运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass `
  -File "C:\Users\lfaf-test\Documents\AI管理\scripts\deploy-secure-launch.ps1"
```

脚本打开独立窗口获取 SMB 凭据，账号没有域时自动加 `GETACAD\`。部署前同时检查
以下三处目标均为空，任何一处非空都拒绝覆盖：

```text
...\014-AI\data\AI-Assets
...\014-AI\data\AI-Assets-Backup
...\014-AI\AI-Assets-Hub
```

部署脚本通过 Windows SMB 会话读取实际账户，并把它设置为首位管理员；不会再使用
本机名或部署包中的占位账户。若实际 SMB 身份无法确认，部署会失败关闭，避免生成
没有可用管理员的 Hub。

部署完成后用 Chrome 打开 `AI-Assets-Hub\index.html`。

## 3. 管理员身份验证

特权操作先使用 `Get-SmbConnection` 读取实际连接账号；在非域电脑未返回连接时，
使用 Windows `WNetGetUser` 查询实际 UNC 会话作为可信后备。两种方法都无法确认时
继续拒绝特权操作。修改
`AI_ASSET_ACTOR`、Windows 用户名或在 AI 中声明“我是管理员”都不能取得权限。

如果早期部署版本只留下 `GETACAD\lfaf-test` 和 `lfaf-test\lfaf-test` 两个占位
管理员，可由最初部署者运行 `scripts\recover-initial-admin.ps1`。该脚本只接受这
一精确的旧状态，只能执行一次，并为公共槽、备份槽保存原始角色文件、SHA-256、
完成标记和审计记录；其他状态一律拒绝恢复。

推荐始终使用管理 Skill 自带入口，不依赖当前 PowerShell 是否定义 `$hub`：

```powershell
$hubEntry = "C:\Users\<用户名>\.codex\skills\ai-assets-manager\scripts\hub.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry view
```

如果直接执行 `python $hub accounts list`，但当前窗口没有先定义 `$hub`，PowerShell
会把命令变成 `python accounts list`，因此出现“找不到
`C:\Windows\System32\accounts`”。这不是 Hub 权限错误。

如果无法确认实际 SMB 身份，管理员命令必须失败关闭。

## 4. 账户和角色管理

查看分配：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry accounts list
```

分配角色：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry accounts assign --account "GETACAD\zhangsan" --role user
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry accounts assign --account "GETACAD\review01" --role reviewer
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry accounts assign --account "GETACAD\publish01" --role publisher
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry accounts assign --account "GETACAD\admin02" --role administrator
```

移除显式角色：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry accounts remove --account "GETACAD\zhangsan"
```

移除后账户回到默认 `user`。系统拒绝移除最后一名管理员。账户比较不区分大小写。

## 5. 角色权限矩阵

| 动作 | 使用者 | 审核者 | 发布者 | 管理员 |
|---|---:|---:|---:|---:|
| 查看正式资产 `view` | ✓ | ✓ | ✓ | ✓ |
| 拉取/激活 `pull`、`activate` | ✓ | ✓ | ✓ | ✓ |
| 自动双槽 Git 草稿备份 | ✓ | ✓ | ✓ | ✓ |
| 提交候选 | ✓ | ✓ | ✓ | ✓ |
| 审核/驳回 | — | ✓ | — | ✓ |
| 发布已审核候选 | — | — | ✓ | ✓ |
| 备份槽镜像到公共槽 | — | — | ✓ | ✓ |
| 分配账户、恢复与管理 | — | — | — | ✓ |

自动草稿备份不检查 Hub 角色，但仍需要 SMB 文件服务允许当前连接账户写入。

## 6. 审核候选

审核前确认：

- 资产 ID 为 `skill/name`、`cli/name` 或 `agent/name`。
- SemVer 未重复。
- 中文更新说明真实、完整，不虚构测试或兼容结论。
- 制品 SHA-256 与实际文件一致。
- 必需依赖存在，范围合理，无循环。
- 在试点电脑完成安装、启动和回滚。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry review "skill__my-skill@1.2.0.json" `
  --decision reviewed --note "依赖、哈希和试点验证通过"
```

拒绝：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry review "skill__my-skill@1.2.0.json" `
  --decision rejected --note "更新说明不完整，且依赖范围过宽"
```

## 7. 发布与镜像

发布只接受 `reviewed`：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry publish "skill__my-skill@1.2.0.json"
```

发布写入备份权威槽。随后执行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry mirror
```

`mirror` 校验备份槽 registry 和制品，把正式代次单向同步到公共槽，并自动更新静态
网页数据。禁止从公共槽反向覆盖备份槽。

## 8. 网页维护

正常发布后的 `mirror` 会自动更新网页。如只需重新导出：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry web-export
```

网页位于：

```text
\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\AI-Assets-Hub\index.html
```

网页每 60 秒重新加载 `hub-data.js`，不需要服务器。

## 9. 管理 Skill 更新

管理 Skill 的资产 ID 是 `skill/ai-assets-manager`。

`1.0.1` 把登录连接改为 Windows 用户会话级，并将“尚未部署 Hub”区分为
`setup_required`。`1.0.2` 进一步让 `hub.ps1` 在当前命令进程中验证实际 SMB
身份；缺少身份时先执行本地安全登录，再继续特权命令。
`1.0.3` 处理 Windows 1219 多账户连接冲突：由用户本地确认后，只断开
`10.97.0.210` 的旧连接，再重新登录。
`1.0.4` 修复清理候选连接时“找不到网络连接”被误判为致命错误的问题。
`1.0.5` 修复交互式 `net use` 的提示文字混入函数返回值，导致退出码 `0` 被误判为
失败的问题。

1. 正常开发、自动草稿双备份、打包、审核和发布。
2. 客户端运行 `self-check`。
3. 用户同意后执行 `self-update`。
4. 更新器校验 SHA-256 和 Skill 结构。
5. 保留用户旧副本，最多三代。
6. 提示用户重启 Code/Agent 会话。
7. 异常时运行 `self-rollback`。

不要在 Git 开发源目录运行自更新。

## 10. 恢复和事件处理

### 公共槽被修改

1. 停止新的发布。
2. 校验备份槽 `registry.json` 和全部正式制品。
3. 确认备份槽正常后执行 `mirror` 恢复公共槽。
4. 重新生成网页数据。
5. 记录异常文件、发现时间和实际 SMB 连接身份。

### 草稿 Git 分叉

1. 不要 force push。
2. 分别克隆公共槽和备份槽的草稿库。
3. 比较 `main` commit、作者、时间和文件差异。
4. 与资产 Owner 确认可信分支。
5. 保存证据后，由管理员在维护窗口修复远端。

### 备份槽异常

不要用公共槽自动反向覆盖。应从文件服务器快照或离线备份恢复权威槽，再执行完整
校验和单向镜像。

## 11. 定期检查

- 每次发布：校验候选、中文说明、依赖、哈希、试点和回滚。
- 每周：检查失败提交、Git 分叉和网页更新时间。
- 每月：执行一次备份槽恢复演练和随机制品哈希抽检。
- 人员变更当天：更新角色分配，确保至少保留两名管理员。
