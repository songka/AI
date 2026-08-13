# -*- coding: utf-8 -*-
"""飞书中文输入的简繁兼容与回复文字风格。"""

from __future__ import annotations

import re


_HAN_RE = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")
_TRADITIONAL_TO_SIMPLIFIED_CHARS = {
    "查": "查", "詢": "询", "簽": "签", "內": "内", "為": "为",
    "麼": "么", "自": "自", "動": "动", "執": "执", "規": "规",
    "則": "则", "設": "设", "幫": "帮", "狀": "状", "態": "态",
    "帳": "账", "號": "号", "碼": "码", "統": "统", "計": "计",
    "組": "组", "暫": "暂", "啟": "启", "開": "开", "關": "关",
    "閉": "闭", "測": "测", "試": "试", "預": "预", "覽": "览",
    "選": "选", "擇": "择", "員": "员", "通": "通", "知": "知",
    "預": "预", "發": "发", "確": "确", "認": "认", "絕": "绝",
    "駁": "驳", "過": "过", "資": "资", "錯": "错", "誤": "误",
    "異": "异", "常": "常", "訊": "讯", "識": "识", "別": "别",
    "這": "这", "話": "话", "沒": "没", "個": "个", "請": "请",
    "發": "发", "送": "送", "檢": "检", "說": "说", "語": "语",
    "後": "后", "當": "当", "輪": "轮", "現": "现", "僅": "仅",
    "項": "项", "復": "复", "與": "与", "屬": "属", "頁": "页",
    "網": "网", "應": "应", "該": "该", "用": "用", "戶": "户",
    "類": "类", "別": "别", "單": "单", "據": "据", "無": "无",
    "實": "实", "體": "体", "從": "从", "裡": "里", "裡": "里",
}
_TRADITIONAL_TO_SIMPLIFIED = str.maketrans(
    _TRADITIONAL_TO_SIMPLIFIED_CHARS
)
_SIMPLIFIED_TO_TRADITIONAL = str.maketrans({
    simplified: traditional
    for traditional, simplified in _TRADITIONAL_TO_SIMPLIFIED_CHARS.items()
    if simplified != traditional
})


def _convert(text: str, target: str) -> str:
    try:
        from zhconv import convert
        return convert(str(text or ""), target)
    except (ImportError, TypeError, ValueError):
        value = str(text or "")
        if target in ("zh-hans", "zh-cn"):
            return value.translate(_TRADITIONAL_TO_SIMPLIFIED)
        if target in ("zh-hant", "zh-tw"):
            return value.translate(_SIMPLIFIED_TO_TRADITIONAL)
        return value


def to_simplified(text: str) -> str:
    """只用于命令/意图比较；不要用它改写用户规则值。"""
    return _convert(text, "zh-hans")


def to_traditional(text: str) -> str:
    """把网页或本地提示转换为繁体；业务存储值不得调用此函数改写。"""
    return _convert(text, "zh-hant")


def contains_han(text: str) -> bool:
    return bool(_HAN_RE.search(str(text or "")))


def prefers_traditional(text: str) -> bool:
    """有明确繁体特征且没有简体特征时，视为全繁体输入。

    “你好”这类简繁字形完全相同的文本无法判断，沿用系统默认简体。
    简繁混用也按非全繁体处理，但命令识别仍会统一转简体比较。
    """
    value = str(text or "")
    if not _HAN_RE.search(value):
        return False
    simplified = _convert(value, "zh-hans")
    traditional = _convert(value, "zh-hant")
    has_traditional_marker = simplified != value
    has_simplified_marker = traditional != value
    return has_traditional_marker and not has_simplified_marker


def reply_in_user_script(message: str, user_text: str) -> str:
    """全繁体输入使用繁体回复；其他输入保持原回复。"""
    if prefers_traditional(user_text):
        return to_traditional(message)
    return str(message or "")


def ai_script_instruction(user_text: str) -> str:
    """给 AI 的文字体系指令，不改变安全协议前缀。"""
    if prefers_traditional(user_text):
        return (
            "用户本次输入为繁體中文。REPLY: 后的自然语言、指令说明与建议必须"
            "使用繁體中文；DO:/SUGGEST:/RULE:/REPLY: 协议前缀保持原样。"
        )
    return (
        "用户可能使用简体、繁體或简繁混用，必须正确理解，不能因为字形不同拒绝"
        "或误判；自然语言回复尽量沿用用户的主要文字风格，协议前缀保持原样。"
    )
