# 機構2D自動報價系統 — 飛書通知設計

日期：2026-08-01
版本：V1.1（修正：飛書僅通知不簽核）

---

## 〇、角色定位

| 說明 |
|---|
| **飛書僅單向通知**。因無公網 IP / 無外部 Web 服務，飛書無法回調到內網。 |
| **審批在軟件內完成**。管理員登入報價軟件 → 審批中心 → 批准/拒絕。 |
| 詳細審批流程見 `change-request-workflow.md`。 |

---

## 一、觸發事件

| 事件 | 通知對象 | 優先級 |
|---|---|---|
| 價格修改請求提交 | Admin | 高 |
| 規則修改請求提交 | Admin | 高 |
| 修改請求審核通過 | 提交者 + Admin | 中 |
| 修改請求退回 | 提交者 | 中 |
| 規則/價格發布 | 所有人 | 中 |
| 報價完成 | 報價者 | 低 |
| 系統異常/錯誤 | Admin | 高 |
| 帳號鎖定 | Admin | 高 |
| Cache 同步失敗 | Admin | 中 |

---

## 二、飛書卡片格式

### 價格修改通知

```json
{
  "msg_type": "interactive",
  "card": {
    "header": {
      "title": {
        "tag": "plain_text",
        "content": "📊 報價規則更新通知"
      },
      "template": "blue"
    },
    "elements": [
      {
        "tag": "div",
        "fields": [
          {"is_short": true, "text": {"tag": "lark_md", "content": "**修改人**\n張三"}},
          {"is_short": true, "text": {"tag": "lark_md", "content": "**修改項**\nA6061 材料價格"}},
          {"is_short": true, "text": {"tag": "lark_md", "content": "**舊值**\n38.00 元/kg"}},
          {"is_short": true, "text": {"tag": "lark_md", "content": "**新值**\n45.00 元/kg"}},
          {"is_short": true, "text": {"tag": "lark_md", "content": "**原因**\n供應商調價"}},
          {"is_short": true, "text": {"tag": "lark_md", "content": "**時間**\n2026-08-01 10:30"}}
        ]
      },
      {
        "tag": "hr"
      },
      {
        "tag": "div",
        "text": {
          "tag": "lark_md",
          "content": "⚠️ 請登入報價軟件 → 審批中心 進行審批"
        }
      }
    ]
  }
}
```

### 異常通知

```json
{
  "header": {
    "title": {"content": "⚠️ 系統異常通知", "tag": "plain_text"},
    "template": "red"
  },
  "elements": [
    {"tag": "div", "text": {"tag": "lark_md", "content": "**異常**: SMB 連線中斷\n**時間**: 2026-08-01 10:30\n**影響**: Cache 同步暫停\n**狀態**: 等待自動重連"}}
  ]
}
```

---

## 三、Notification Service

```python
# infrastructure/notification/feishu.py

class FeishuNotifier:
    """Send notifications via Feishu webhook."""

    def __init__(self, webhook_url: str): ...

    def send_card(self, card: dict) -> bool:
        """Send an interactive card message."""
        ...

    def notify_price_change(
        self,
        user_name: str,
        item: str,
        old_value: str,
        new_value: str,
        reason: str,
        change_request_id: str,
    ) -> bool: ...

    def notify_review_result(
        self,
        change_request_id: str,
        approved: bool,
        reviewer: str,
        comment: str,
    ) -> bool: ...

    def notify_error(self, error_message: str, severity: str) -> bool: ...


class NotificationConfig(BaseModel):
    """Notification configuration."""
    feishu_webhook_url: str | None = None
    enable_price_change_notify: bool = True
    enable_rule_change_notify: bool = True
    enable_error_notify: bool = True
    enable_quote_complete_notify: bool = False  # 可能過多
```

---

## 四、配置

```yaml
# config/notification.yaml
notifications:
  feishu:
    webhook_url: ""  # 由 Admin 在系統中設定
    enabled: true

  events:
    price_change:        { enabled: true, notify_roles: [admin] }
    rule_published:      { enabled: true, notify_roles: [admin, engineer, sales] }
    review_required:     { enabled: true, notify_roles: [admin] }
    system_error:        { enabled: true, notify_roles: [admin] }
    quote_completed:     { enabled: false }
```

---

## 五、消息隊列（非同步發送）

### 設計原則

飛書 Webhook 可能失敗（網路抖動、限流）。核心審批流程**不能**因通知失敗而中斷。

### 通知消息模型

```python
class NotifyStatus(str, Enum):
    PENDING = "PENDING"
    SENT = "SENT"
    FAILED = "FAILED"

class NotificationMessage(BaseModel):
    msg_id: str                      # UUID
    event_type: str                  # "cr_submitted" | "cr_approved" | ...
    target_users: list[str]
    card_payload: dict               # Feishu card JSON
    status: NotifyStatus = NotifyStatus.PENDING
    created_at: str
    sent_at: str | None = None
    retry_count: int = 0
    max_retries: int = 3
    last_error: str | None = None
```

### 隊列流程

```
核心操作（審批/發布）完成
    │
    ▼
enqueue() → 保存到本地隊列 → 核心操作返回
    │
    ▼
後台線程 process_queue()
    ├── PENDING → HTTP POST Webhook
    │     ├── 200 → SENT, 清除本地文件
    │     └── 失敗 → retry_count++ (10s/30s/60s 退避)
    │           └── >3次 → FAILED, 記錄錯誤
    └── 隊列目錄: C:\ProgramData\MechanicalQuotation\notification_queue\
```

### 隊列配置

```yaml
notification:
  queue:
    max_retries: 3
    retry_backoff: [10, 30, 60]   # seconds
    cleanup_sent: true             # Delete local file after sent
    failed_alert: true             # Alert admin when messages fail
```

---

*本文件為 Phase 5 協作流程的一部分。*
