# 账户角色配置

管理员通过 Hub 命令分配角色，不让用户直接编辑 `roles.json`：

```powershell
python "<公共槽>\client\asset_hub.py" accounts list
python "<公共槽>\client\asset_hub.py" accounts assign --account "GETACAD\zhangsan" --role reviewer
python "<公共槽>\client\asset_hub.py" accounts remove --account "GETACAD\zhangsan"
```

角色值为 `administrator`、`reviewer`、`publisher`、`user`。未分配账户使用默认
`user`。账户比较不区分大小写。系统拒绝移除最后一名管理员。特权命令必须从实际
SMB 连接获取身份，不能仅相信 AI 或环境变量声称的用户名。

草稿自动双备份不依赖这些角色；只要 SMB 登录和文件写入成功就执行。
