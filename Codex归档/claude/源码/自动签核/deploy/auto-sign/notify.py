# -*- coding: utf-8 -*-
"""通知模块 — 可插拔的通知接口。

支持的通知渠道:
  - console : 控制台输出（默认）
  - webhook : HTTP POST 到指定 URL

扩展方式:
  在 NOTIFIERS 字典中注册新的通知器函数，签名:
    def my_notifier(summary: dict, items: list[dict], config: dict) -> bool
"""

from __future__ import annotations

import json
from typing import Any


def notify_console(summary: dict, items: list[dict], config: dict) -> bool:
    """控制台通知：打印待处理项目摘要。"""
    print()
    print("=" * 55)
    print("  [通知] 签核待办提醒")
    print("=" * 55)
    print(f"  总计: {summary.get('total', 0)} 项")
    print(f"  自动签核: {summary.get('approve', 0)}  自动拒签: {summary.get('reject', 0)}")
    print(f"  需确认:   {summary.get('notify', 0)}  待手动:   {summary.get('manual', 0)}")

    notify_items = [i for i in items if i.get("action") == "notify"]
    manual_items = [i for i in items if not i.get("action")]

    if notify_items:
        print(f"\n  --- 需确认的项目 ({len(notify_items)} 项) ---")
        for item in notify_items:
            print(f"  # {item.get('no', '?')} | {item.get('applicant', '?')} | {item.get('desc', '')[:50]}")

    if manual_items:
        print(f"\n  --- 待手动处理 ({len(manual_items)} 项) ---")
        for item in manual_items:
            print(f"  # {item.get('no', '?')} | {item.get('applicant', '?')} | {item.get('desc', '')[:50]}")

    print()
    return True


def notify_webhook(summary: dict, items: list[dict], config: dict) -> bool:
    """Webhook 通知：POST JSON 到指定 URL。"""
    import requests as _requests

    url = config.get("webhook_url", "")
    if not url:
        print("  [警告] webhook_url 未配置，跳过 webhook 通知")
        return False

    payload = {
        "title": "签核待办提醒",
        "summary": summary,
        "items": items,
    }

    try:
        headers = {}
        if config.get("webhook_token"):
            headers["Authorization"] = f"Bearer {config['webhook_token']}"
        resp = _requests.post(url, json=payload, headers=headers, timeout=15)
        if resp.status_code < 400:
            print(f"  [OK] Webhook 通知已发送 ({resp.status_code})")
            return True
        else:
            print(f"  [警告] Webhook 返回 {resp.status_code}: {resp.text[:200]}")
            return False
    except Exception as exc:
        print(f"  [警告] Webhook 发送失败: {exc}")
        return False


# 注册表：名称 → 函数
NOTIFIERS: dict[str, Any] = {
    "console": notify_console,
    "webhook": notify_webhook,
}


def send_notification(
    summary: dict,
    items: list[dict],
    channels: list[str] | None = None,
    notify_config: dict | None = None,
) -> dict[str, bool]:
    """发送通知到指定渠道。

    Args:
        summary: {"total": N, "approve": N, "reject": N, "notify": N, "manual": N}
        items: [{"no": "", "applicant": "", "desc": "", "action": "", "rule": ""}, ...]
        channels: 渠道列表，默认 ["console"]
        notify_config: 通知配置（webhook_url 等）

    Returns:
        {channel_name: success}
    """
    if channels is None:
        channels = ["console"]
    if notify_config is None:
        notify_config = {}

    results = {}
    for channel in channels:
        notifier = NOTIFIERS.get(channel)
        if notifier:
            results[channel] = notifier(summary, items, notify_config)
        else:
            print(f"  [警告] 未知通知渠道: {channel}")
            results[channel] = False

    return results


def build_summary(items: list[dict]) -> dict:
    """从项目列表构建统计摘要。"""
    summary = {"total": len(items), "approve": 0, "reject": 0, "notify": 0, "manual": 0}
    for item in items:
        action = item.get("action", "")
        if action == "approve":
            summary["approve"] += 1
        elif action == "reject":
            summary["reject"] += 1
        elif action == "notify":
            summary["notify"] += 1
        else:
            summary["manual"] += 1
    return summary
