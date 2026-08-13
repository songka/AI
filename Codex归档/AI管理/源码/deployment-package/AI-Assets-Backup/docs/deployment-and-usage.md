# 完整部署与使用说明

## 1. 前置条件

- Windows 客户端、Python 3.11+、Git。
- 两个已存在的 SMB 目录；当前账户至少能够创建自己的 `drafts` 内容。
- 将 `deployment-package/AI-Assets` 放入公共槽，将
  `deployment-package/AI-Assets-Backup` 放入备份槽。
- 无法修改 SMB ACL 时，接受“不能阻止人工改文件，只能校验、拒绝和恢复”的边界。

## 2. 客户端一次性安装

将 `skills/ai-assets-manager` 整个目录复制到目标 Code 工具的 skills 目录。重启
客户端，使其重新发现 Skill。所有电脑使用同一版本，不复制角色专用变体。

## 3. 登录

第一次调用时，Skill 运行 `gate`。若公共槽不可访问或无法通过
`Get-SmbConnection` 确认身份，只显示：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<skill>\scripts\secure-login.ps1"
```

账号没有域时脚本补 `GETACAD\`。账号与密码仅在独立 PowerShell/Windows 凭据
窗口输入，不应发送到 AI 对话。需要临时账号时也运行同一脚本。

## 4. 本地开发与自动草稿备份

```powershell
python "<skill>\scripts\ai_assets_skill.py" init `
  --path "D:\work\my-agent" --type agent --name my-agent --version 0.1.0 `
  --dependency skill/common@^1.0.0
```

每次 `init`、`status`、`bump`、`package` 都自动执行草稿 Git 备份：

```text
公共槽\drafts\<SMB身份>\<类型>\<名称>.git
备份槽\drafts\<SMB身份>\<类型>\<名称>.git
```

两边推送同一个 commit，禁止 force push。历史分叉会停止并报警。草稿不进入正式
`registry.json`，其他用户不能把它当正式版本安装。`.env`、私钥、凭据文件等会
阻止上传。

## 5. 打包、提交、审核和发布

```powershell
python "<skill>\scripts\ai_assets_skill.py" package --path "D:\work\my-agent" --output "D:\packages"
python "<公共槽>\client\asset_hub.py" submit "<submission.json>" --artifact "<zip>"
python "<公共槽>\client\asset_hub.py" review "<candidate.json>" --decision reviewed
python "<公共槽>\client\asset_hub.py" publish "<candidate.json>"
python "<公共槽>\client\asset_hub.py" mirror
```

使用者可提交；审核者可审核但不能发布；发布者只能发布已审核候选；管理员还可分配
角色和恢复仓库。特权命令必须匹配实际 SMB 连接身份。

## 6. 安装和依赖

```powershell
python "<公共槽>\client\asset_hub.py" install "agent/my-agent@1.2.0" --activate
```

解析器合并全部版本约束，按依赖优先顺序下载 Skill、CLI、Agent，逐项校验
SHA-256，再切换本地激活版本。任一依赖冲突或摘要不符都不会激活半成品。

## 7. 管理 Skill 更新

`self-check` 仅检查。用户同意后运行 `self-update`。成功后向用户报告旧版、新版、
备份目录，并要求重启 Code/Agent 会话。最多保留三代用户原副本。使用
`self-backups` 查看，使用 `self-rollback` 恢复。

## 8. 验收

- 未登录时只有登录指引。
- 四类账户得到正确提示和命令权限。
- 三类资产均可建立版本和依赖。
- 本地修改自动产生相同的双 SMB Git commit。
- 人工制造远端分叉后自动备份拒绝覆盖。
- 安装会自动下载依赖并校验哈希。
- 管理 Skill 更新保留三代、重启生效、可回滚。
