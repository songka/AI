---
name: auto-sign
description: 自动签核系统 — 定时抓取、Excel 决策、批量签核/拒签。支持 AND/OR 多维条件规则。
---

# 自动签核工具箱

## 快速开始

```bash
pip install -r requirements.txt
cp config.example.json ../../config.json
py cli.py login                    # 首次需输入账号密码
py cli.py list                     # 查看待签（表格: # | 申请人 | 描述）
py cli.py fetch --dry-run          # 测试规则匹配
py cli.py fetch                    # 生成决策 Excel
py cli.py process                  # 批量执行
```

## CLI 命令

| 命令 | 功能 |
|------|------|
| `login` | 登录验证 |
| `list` | 待签列表（简洁表格：**# / 申请人 / 描述** + 分类统计） |
| `show <id>` | 单项完整详情 |
| `fetch` | 抓取 → 生成决策 Excel |
| `fetch --dry-run` | 测试模式：逐项显示规则匹配 |
| `process` | 读取 Excel → 批量签核/拒签 |
| `process --dry-run` | 测试模式：预览不提交 |
| `run` | 一条龙：fetch → 编辑 → process |
| `notify` | 发送通知（console/webhook） |
| `approve <ids>` | 在线签核 |
| `reject <ids>` | 在线拒签 |

## 当前规则

```
拒签优先: 含简体字 / 空描述
         + 半成品;軟體 & (单位≠ST | 类别≠PH | 无R\d{3})
         + 原材料;電控外購件 & (单位∉{M,EA} | 类别≠P)

签核: content_whitelist 开头 + whitelist 白名单
```

## 规则配置 (rules.json)

```json
{
  "auto_reject":  [{"name":"..", "conditions":[{"field":"..","op":"..","value":".."}], "logic":"AND|OR"}],
  "auto_approve": [...],
  "notify": [...]
}
```

操作符: `equals, not_equals, contains, starts_with, starts_with_any, starts_with_content_wl, not_starts_with, has_cn, is_empty, regex, not_regex, in_list, not_in_list, in_whitelist, in_blacklist`

字段: `申请人, 描述, 类别, 单位, 申请单号`

## 可编辑文件

| 文件 | 作用 |
|------|------|
| `rules.json` | 自动判断规则 |
| `whitelist.txt` | 申请人白名单（每行一个姓名） |
| `content_whitelist.txt` | 描述前缀白名单（每行一个前缀） |
| `name_blacklist.txt` | 申请人黑名单 |

## 通知

```bash
py cli.py notify                                    # 控制台通知
py cli.py notify -c webhook --webhook-url "..."     # Webhook
```

扩展: 在 `notify.py` 的 `NOTIFIERS` 字典中注册新函数。

## 执行指南

| 用户意图 | 命令 |
|----------|------|
| 查看待签 | `py cli.py list` |
| 测试规则 | `py cli.py fetch --dry-run` |
| 抓取导出 | `py cli.py fetch` |
| 预览执行 | `py cli.py process --dry-run` |
| 正式执行 | `py cli.py process` |
| 在线签核 | `py cli.py approve <ids>` |
| 在线拒签 | `py cli.py reject <ids>` |
