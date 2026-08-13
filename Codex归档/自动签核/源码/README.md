# auto_sign

自动签核系统。当前版本使用 HTTP 会话直接登录、读取签核页面、提交表单，不再依赖 Selenium、Chrome 或 ChromeDriver。

## 使用

1. 安装依赖：

   ```powershell
   pip install -r requirements.txt
   ```

2. 复制 `config.example.json` 为 `config.json`，填写账号密码。

3. 先试跑判断结果：

   ```powershell
   python auto_sign.py --dry-run
   ```

4. 确认判断无误后执行：

   ```powershell
   python auto_sign.py
   ```

## exe 版本

打包后的 `auto_sign.exe` 会从 exe 所在目录读取 `config.json`、`whitelist.txt`、`content_whitelist.txt`、`name_blacklist.txt`、`description_new_list.txt`，并把 `sign_records.xlsx` 写在同一目录。

命令行试跑：

```powershell
.\auto_sign.exe --dry-run
```

确认后执行：

```powershell
.\auto_sign.exe
```

## 配置

- `url`: 签核页面地址，默认 `https://gsc.getac.com/signs/l1/W`
- `verify_ssl`: 是否校验证书。旧版浏览器脚本忽略证书错误，所以默认 `false`
- `dry_run`: 只输出判断，不提交
- `submit_when_no_approvals`: 没有符合条件项目时是否仍提交表单，默认 `false`
