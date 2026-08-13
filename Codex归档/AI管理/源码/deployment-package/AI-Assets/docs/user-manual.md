# 使用者操作说明书

## 1. 谁可以查看和拉取

已经成功登录 SMB 的管理员、审核者、发布者、使用者都可以：

- 查看 Hub 中已经正式发布的 Skill、CLI、Agent。
- 查看同一资产的全部可用版本、通道、依赖和中文更新说明。
- 拉取指定版本；系统自动先拉取必需依赖。
- 在本机多个已安装版本之间切换。

未发布草稿不会出现在公共正式版本列表中。草稿仍会自动备份到当前 SMB 身份专属的
两个 Git 仓库。

## 2. 登录

通常先自动使用当前 Windows SMB 会话。无法访问时，AI 只会显示独立登录入口：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<管理Skill>\scripts\secure-login.ps1"
```

只在弹出的 Windows 窗口输入凭据。账号未写域时自动补 `GETACAD\`。不要把账号或
密码发送到 AI 对话。

## 3. 查看正式资产

```powershell
$hubEntry = "C:\Users\<用户名>\.codex\skills\ai-assets-manager\scripts\hub.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry view
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry view skill/ai-assets-manager
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry view cli/codex
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry view agent/my-agent
```

也可以用 Chrome 打开：

```text
\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\014-AI\AI-Assets-Hub\index.html
```

网页显示正式资产、版本、Owner、发布通道、依赖和中文更新说明，不显示账号、密码或
用户草稿内容。

## 4. 拉取和激活

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry pull skill/ai-assets-manager@1.0.6 --activate
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry pull cli/codex@1.3.0 --activate
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry pull agent/my-agent@1.2.0 --activate
```

默认只拉取 `stable`。试点版本必须明确指定：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry pull cli/codex@1.4.0 --channel preview --activate
```

处理顺序：

1. 合并目标和全部下游依赖的版本约束。
2. 选择满足约束的版本。
3. 按依赖优先顺序下载。
4. 校验每个制品 SHA-256。
5. 全部成功后激活目标版本。

任一依赖冲突、文件缺失或摘要错误都会停止，不会激活半套环境。

## 5. 切换已有版本

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File $hubEntry activate skill/ai-assets-manager@1.0.6
```

切换只改变本机当前版本指针，不删除其他已安装版本。

## 6. 本地开发和自动草稿备份

```powershell
python "<管理Skill>\scripts\ai_assets_skill.py" init `
  --path "D:\work\my-skill" --type skill --name my-skill --version 0.1.0

python "<管理Skill>\scripts\ai_assets_skill.py" status --path "D:\work\my-skill"
```

`init`、`status`、`bump`、`package` 都会自动生成 Git commit，并把同一个 commit
推送到公共槽和备份槽。用户不需要另外说“备份”。

## 7. 打包和更新说明

```powershell
python "<管理Skill>\scripts\ai_assets_skill.py" package `
  --path "D:\work\my-skill" --output "D:\packages"
```

系统根据相对上次打包的新增、修改、删除文件自动生成中文更新说明草稿。请检查说明。
需要业务背景时可指定：

```powershell
python "<管理Skill>\scripts\ai_assets_skill.py" package `
  --path "D:\work\my-skill" --output "D:\packages" `
  --release-notes "新增 PLC 程序差异检查，并修正异常输入提示。"
```

## 8. 常见问题

| 现象 | 处理 |
|---|---|
| 只看到登录提示 | 在独立窗口登录 SMB，然后重新发起原请求 |
| 找不到资产 | 确认它已经正式发布；草稿不会出现在 `view` |
| 没有满足约束的版本 | 联系资产 Owner 调整依赖或发布兼容版本 |
| SHA-256 不匹配 | 停止使用，通知管理员检查 SMB 是否被修改 |
| 草稿 push 被拒绝 | 远端 Git 历史可能被人工修改或存在并发分叉，通知管理员 |
| 新 Skill 未生效 | 关闭并重新打开当前 Code/Agent 会话 |
