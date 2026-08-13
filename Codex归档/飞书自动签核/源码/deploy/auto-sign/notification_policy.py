# -*- coding: utf-8 -*-
"""签核结果的群通知决策，和 approve/reject 决策相互独立。"""

from __future__ import annotations

from rules import _match_rule_group


LEGACY_REJECTION_REASON_KEYS = (
    "reason",
    "reject_reason",
    "rejectReason",
    "拒签理由",
    "拒签原因",
)


def rule_rejection_reason(rule) -> str:
    """读取拒签规则理由；兼容无字段和旧字段名。"""
    if not isinstance(rule, dict):
        return ""
    for key in LEGACY_REJECTION_REASON_KEYS:
        value = rule.get(key)
        if isinstance(value, list):
            value = "；".join(str(part).strip() for part in value if str(part).strip())
        reason = str(value or "").strip()
        if reason:
            return reason
    return ""


def set_rule_rejection_reason(rule: dict, reason: str) -> dict:
    """以标准 reason 字段写回理由，并清理已识别的旧别名。"""
    updated = dict(rule or {})
    for key in LEGACY_REJECTION_REASON_KEYS:
        updated.pop(key, None)
    normalized = str(reason or "").strip()
    if normalized:
        updated["reason"] = normalized
    return updated


def cycle_action_rule_notification(rule: dict):
    """循环动作规则的通知设置：跟随策略 → 发群 → 不发群 → 跟随策略。"""
    updated = dict(rule)
    if "group_notify" not in updated:
        updated["group_notify"] = True
        return updated, "发群"
    if updated.get("group_notify") is True:
        updated["group_notify"] = False
        return updated, "不发群"
    updated.pop("group_notify", None)
    return updated, "跟随通知策略"


def notification_decision(item: dict, rules: dict, word_lists: dict, action_rule=None,
                          manual_override=None, default_notify: bool = False):
    """返回 (是否发群, 原因)，优先级遵循用户确认的策略。"""
    if manual_override is not None:
        return bool(manual_override), "手动明确指定"

    notification_rules = list(rules.get("notification_rules", []))
    # 兼容旧 notify 规则：旧规则视为“匹配后发送”。
    notification_rules.extend(rules.get("notify", []))
    for rule in notification_rules:
        if _match_rule_group(rule, item, word_lists):
            return bool(rule.get("notify", True)), rule.get("name", "通知规则")

    if action_rule and "group_notify" in action_rule:
        return bool(action_rule.get("group_notify")), action_rule.get("name", "动作规则")

    return bool(default_notify), "用户默认设置"


def rejection_reason(manual_reason: str, action_rule=None) -> str:
    """人工拒签原因可选；没有填写时使用命中拒签规则的理由。"""
    reason = str(manual_reason or "").strip()
    if reason:
        return reason
    if action_rule:
        return rule_rejection_reason(action_rule) or str(
            action_rule.get("name") or "命中拒签规则"
        )
    return "人工拒签（未填写原因）"
