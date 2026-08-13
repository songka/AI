# 签核自动工具箱 — 交付文档

## 概述

无浏览器依赖的 HTTP 自动签核系统，用于 GSC 签核平台。
支持：定时抓取、规则自动判断、Excel 离线决策、批量签核/拒签、通知。

## 目录结构

```
.claude/auto-sign/          ← 技能包（复制给他人即可用）
  cli.py                    ← CLI 入口（所有命令）
  auto_sign.py              ← 核心：HTTP 登录、页面解析、Excel 生成、批量提交
  rules.py                  ← 规则引擎：AND/OR 多维条件匹配
  notify.py                 ← 通知模块：可插拔通知渠道
  skill.md                  ← 技能说明
  config.example.json       ← 配置模板（无凭证）
  rules.example.json        ← 规则模板
  requirements.txt          ← Python 依赖
  whitelist.txt             ← 申请人白名单（内置默认）
  content_whitelist.txt     ← 描述前缀白名单（内置默认）
  name_blacklist.txt        ← 姓名黑名单

项目根目录（用户运行目录）：
  config.json               ← 用户配置
  auth.json                 ← 账号密码（自动生成）
  rules.json                ← 用户规则（可手动编辑）
  whitelist.txt             ← 用户白名单（优先于内置）
  content_whitelist.txt     ← 用户描述白名单
  pending_signs.xlsx        ← fetch 产出的决策 Excel
  sign_records.xlsx         ← 签核记录
```

## 快速开始

```bash
# 1. 安装依赖
cd .claude/auto-sign && pip install -r requirements.txt

# 2. 首次登录（输入账号密码，自动保存到 auth.json）
py cli.py login

# 3. 测试规则匹配
py cli.py fetch --dry-run

# 4. 生成决策 Excel
py cli.py fetch

# 5. 编辑 Excel 的「操作」列，然后执行
py cli.py process --dry-run     # 先预览
py cli.py process               # 正式执行
```

## CLI 命令

| 命令 | 功能 | 关键参数 |
|------|------|----------|
| `login` | 登录验证 | `--config` |
| `list` | 在线查看待签列表+统计 | `--config` |
| `show <id>` | 查看单项详情 | |
| `fetch` | 抓取→生成决策 Excel | `-o` 输出路径, `-r` 规则文件, `--dry-run` |
| `process` | 读取 Excel→批量执行 | `-i` 输入路径, `--dry-run` |
| `run` | 一条龙: fetch→编辑→process | `-y` 跳过确认 |
| `notify` | 发送通知 | `-c` 渠道, `--webhook-url` |
| `approve <ids>` | 在线签核 | `--dry-run` |
| `reject <ids>` | 在线拒签 | `--dry-run` |
| `approve-all` | 全部签核 | `--dry-run` |
| `reject-all` | 全部拒签 | `--dry-run` |

所有写操作支持 `--dry-run`（只预览不提交）。

## 规则系统 (rules.json)

### 结构

```json
{
  "auto_reject":  [{ "name": "...", "conditions": [...], "logic": "AND|OR" }],
  "auto_approve": [{ "name": "...", "conditions": [...], "logic": "AND|OR" }],
  "notify":       [{ "name": "...", "conditions": [...], "logic": "AND|OR" }]
}
```

- **auto_reject**: 最高优先级，命中直接拒签
- **auto_approve**: 第二优先级，命中直接签核
- **notify**: 第三优先级，标记需通知/确认（不自动处理）

每个规则组是一个条件列表 + AND/OR 逻辑。`auto_reject` 和 `auto_approve` 内多个规则按顺序匹配，首个命中即返回。

### 当前规则逻辑

```
1. 拒签: 描述含简体字 OR 描述为空
    + 半成品;軟體 且 (单位≠ST OR 类别≠PH OR 无R\d{3})
    + 原材料;電控外購件 且 (单位不在{M,EA} OR 类别≠P)

2. 签核: 描述以 content_whitelist 开头 AND 申请人在 whitelist

3. 通知: (未启用)
4. 都不匹配: Excel 操作列留空，手动填写
```

### 操作符

| 操作符 | 说明 | 示例 value |
|--------|------|------------|
| `equals` | 精确匹配 | `"ST"` |
| `not_equals` | 不等于 | `"PH"` |
| `contains` | 包含子串 | `"软件"` |
| `starts_with` | 以...开头 | `"半成品;軟體"` |
| `starts_with_any` | 以任一前缀开头 | `"半成品,原材料"` |
| `starts_with_content_wl` | 以 content_whitelist 中任一行开头 | `""` |
| `not_starts_with` | 不以...开头 | `"半成品;軟體"` |
| `has_cn` | 含简体字（zhconv 检测） | `""` |
| `is_empty` | 为空 | `""` |
| `regex` | 正则匹配 | `"R\\d{3}"` |
| `not_regex` | 正则不匹配 | `"R\\d{3}"` |
| `in_list` | 在逗号分隔列表中 | `"M,EA"` |
| `not_in_list` | 不在列表中 | `"PH,ST"` |
| `in_whitelist` | 命中 whitelist.txt | `""` |
| `in_blacklist` | 命中 name_blacklist.txt | `""` |

### 可用字段

`申请人`, `描述`, `类别`, `单位`, `申请单号`

### 添加新规则

编辑 `rules.json`，按优先级排列规则组。AI 可直接修改此文件：

```json
// 例：新增拒签规则 — 某类别+非白名单人员直接拒签
{
  "name": "SEMI类非白名单拒签",
  "conditions": [
    {"field": "类别", "op": "equals", "value": "SEMI"},
    {"field": "申请人", "op": "in_whitelist", "value": ""}
  ],
  "logic": "AND"
}
```

## 通知系统 (notify.py)

### 架构

`notify.py` 提供可插拔的通知渠道。通知接收一个摘要字典和项目列表，发送到指定渠道。

### 内置渠道

| 渠道 | 说明 | 配置 |
|------|------|------|
| `console` | 控制台输出（默认） | 无 |
| `webhook` | HTTP POST JSON | `--webhook-url` + 可选 `--webhook-token` |

### 通知数据结构

```json
{
  "title": "签核待办提醒",
  "summary": {"total": 5, "approve": 2, "reject": 1, "notify": 1, "manual": 1},
  "items": [
    {"no": "892906", "applicant": "汪永恒", "desc": "...", "action": "notify", "rule": "需确认规则名"}
  ]
}
```

### CLI 使用

```bash
# 控制台通知
py cli.py notify

# Webhook 通知（企业微信/钉钉/飞书等）
py cli.py notify -c webhook --webhook-url "https://hook.example.com/notify"

# 多渠道
py cli.py notify -c "console,webhook" --webhook-url "https://..."
```

### 扩展新渠道

在 `notify.py` 中添加函数并注册到 `NOTIFIERS` 字典：

```python
def notify_email(summary, items, config):
    # 发送邮件逻辑
    return True

NOTIFIERS["email"] = notify_email
```

## 可编辑文件清单

| 文件 | 位置 | 作用 | 格式 |
|------|------|------|------|
| `config.json` | 根目录 | URL、超时、SSL等 | JSON |
| `auth.json` | 根目录 | 账号密码（自动生成） | JSON |
| `rules.json` | 根目录 | 自动判断规则 | JSON |
| `whitelist.txt` | 根目录 | 申请人白名单 | 每行一个名字 |
| `content_whitelist.txt` | 根目录 | 描述前缀白名单 | 每行一个前缀 |
| `name_blacklist.txt` | 根目录 | 申请人黑名单 | 每行一个名字 |

## 定时任务

Windows 任务计划（已配置每30分钟）：
```powershell
Get-ScheduledTask AutoSignFetch     # 查看
Start-ScheduledTask AutoSignFetch   # 手动触发
Disable-ScheduledTask AutoSignFetch # 暂停
```

Linux cron：
```bash
*/30 * * * * cd /path && python .claude/auto-sign/cli.py fetch
```

## 工作流总结

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│ 定时 fetch    │ ──→ │ 编辑 Excel   │ ──→ │ process 执行  │
│ 规则预匹配    │     │ 补填操作列   │     │ 签核/拒签     │
└──────────────┘     └──────────────┘     └──────────────┘
       │                                        │
       │  notify 发送通知                        │  记录到
       │  (webhook/console)                     │  sign_records.xlsx
       └────────────────────────────────────────┘
```

## 依赖

```
beautifulsoup4>=4.12
openpyxl>=3.1
requests>=2.31
zhconv>=1.4        # 简繁体检测
```
