# -*- coding: utf-8 -*-
"""飞书文本的安全意图预判。

这里只识别高确定性的非 AI 意图。任何可能改变签核状态的模糊表达都只生成
指令建议，不在本模块中执行。
"""

from __future__ import annotations

import re

from language_style import to_simplified


PREVIEW_WORDS = ("模拟", "測試", "测试", "試跑", "试跑", "预览", "預覽", "演练", "演練")
META_WORDS = ("为什么", "為什麼", "怎么", "怎麼", "如何", "说明", "說明", "解释", "解釋", "不是应该", "不是應該")
RULE_WORDS = (
    "规则", "規則", "白名单", "白名單", "黑名单", "黑名單",
    "用户组", "使用者群組", "内容组", "內容組", "通知规则", "通知規則",
)


def normalize_text(text: str) -> str:
    return re.sub(
        r"[\s，,。.!！?？、：:；;~～]",
        "",
        to_simplified(str(text)),
    ).casefold()


def is_preview_request(text: str) -> bool:
    value = normalize_text(text)
    return any(word in value for word in PREVIEW_WORDS) and any(
        word in value for word in ("签核", "簽核", "自动", "自動", "规则", "規則")
    )


def is_meta_question(text: str) -> bool:
    value = normalize_text(text)
    return any(word in value for word in META_WORDS)


def is_rule_request(text: str) -> bool:
    value = normalize_text(text)
    if is_preview_request(value) or is_meta_question(value):
        return False
    change_words = ("加", "添加", "新增", "建立", "创建", "設定", "设置", "修改", "删除", "刪除", "多条", "多條")
    standard_request = any(word in value for word in RULE_WORDS) and any(
        word in value for word in change_words
    )
    group_reference = any(
        word in value for word in ("用户组", "使用者群組", "内容组", "內容組")
    ) or (
        "组" in value
        and any(field in value for field in ("申请人", "申請人", "描述", "内容", "內容", "料号", "料號"))
    )
    group_rule_phrase = group_reference and any(
        word in value for word in ("签核", "簽核", "拒签", "拒簽", "通知", "发群", "發群")
    )
    return standard_request or group_rule_phrase


def is_query_request(text: str) -> bool:
    """仅识别明确查询；排除规则、模拟和解释类句子。"""
    value = normalize_text(text)
    if not value or is_preview_request(value) or is_meta_question(value) or is_rule_request(value):
        return False

    direct = (
        "查询", "查詢", "待签", "待簽", "待办", "待辦", "我的待办", "我的待辦",
        "查一下", "帮我查一下", "幫我查一下", "看看待签", "看看待簽",
        "有什么要签", "有什麼要簽", "有哪些要签", "有哪些要簽", "有没有要签的", "有沒有要簽的",
        "我有要签核的吗", "我有要簽核的嗎", "我有需要签核的吗", "我有需要簽核的嗎",
        "有没有料号", "有沒有料號", "有什么料号", "有什麼料號", "现在要签什么", "現在要簽什麼",
    )
    if value in direct or any(phrase in value for phrase in direct[10:]):
        return True

    query_starts = ("查询", "查詢", "查一下", "查看", "列出", "显示", "顯示", "看看")
    targets = ("待签", "待簽", "待办", "待辦", "料号", "料號", "签核内容", "簽核內容")
    return value.startswith(query_starts) and any(target in value for target in targets)


def ai_mutation_hint(result: str) -> str:
    """把 AI 的任何签核建议转换为安全的显式指令提示。"""
    value = str(result or "").strip()
    mappings = (
        ("DO:approve_all", "我理解你可能想全部签核。请明确发送「全签」，随后还需要二次确认。"),
        ("DO:reject_all", "我理解你可能想全部拒签。请明确发送「全拒」，随后还需要二次确认。"),
        ("DO:approve ", "我理解你可能想签核指定项目。请明确发送「签核 编号」，例如「签核 1 3」。"),
        ("DO:reject ", "我理解你可能想拒签指定项目。请明确发送「拒签 编号」，例如「拒签 2 原因:资料不完整」。"),
        ("SUGGEST:approve_all", "请明确发送「全签」，随后还需要二次确认。"),
        ("SUGGEST:reject_all", "请明确发送「全拒」，随后还需要二次确认。"),
        ("SUGGEST:approve", "请明确发送「签核 编号」，例如「签核 1 3」。"),
        ("SUGGEST:reject", "请明确发送「拒签 编号」，例如「拒签 2 原因:资料不完整」。"),
    )
    for prefix, message in mappings:
        if value.startswith(prefix):
            return message
    return ""
