# 凭据安全

只要用户把密码输入 AI 对话，密码就已经进入模型请求边界，任何提示词都无法事后
保证“没有发送”。因此本系统只允许在独立 Windows 凭据窗口输入密码。

禁止：

- 在聊天中发送账号密码。
- 把密码作为 CLI 参数、环境变量、日志或 JSON/YAML 字段。
- 使用 `/savecred`、`cmdkey /pass`。
- 把 `SecureString` 转明文或序列化 `PSCredential`。
- 将 `.env`、私钥或凭据文件自动备份到 SMB。

允许：

- 当前 Windows/SMB 会话自动复用。
- `Get-Credential` 生成的内存 `PSCredential`。
- 账号不含域时本地补 `GETACAD\`。
- 临时账号只在外部窗口输入，会话结束后释放凭据对象。

`scripts/check-secret-boundary.ps1` 用于静态检查这些禁用模式。
