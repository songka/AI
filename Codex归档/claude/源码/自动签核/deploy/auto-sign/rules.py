# -*- coding: utf-8 -*-
"""规则引擎 — 多维条件匹配，支持 AND/OR 组合。

rules.json 格式:
{
  "auto_approve": [{
    "name": "规则名称",
    "conditions": [{"field": "申请人", "op": "contains", "value": "张三"}],
    "logic": "AND"  // 或 "OR"
  }],
  "auto_reject": [...],
  "notify": [...]
}

支持的操作符:
  equals, contains, starts_with, starts_with_any,
  regex, has_cn, is_empty,
  in_list, not_in_list, in_whitelist, in_blacklist
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

# ========================================================================
#  简体字检测：只检测有独立简体写法的汉字
#  如果某个字简繁体写法相同（如 半、成、品、中、文、人），不算简体字
#  只有那些简化后与繁体形态不同的字才算（如 体≠體, 软≠軟, 电≠電）
# ========================================================================

# 常见有独立简体写法的汉字 → 对应繁体
# 来源：简化字总表，覆盖日常高频简化字
_SIMPLIFIED_CHARS: set[str] = set()

# 偏旁类推简化
_RADICAL_SIMPLE_MAP = {
    "讠": "言", "饣": "飠", "纟": "糹", "绉": "糹", "钅": "釒",
    "门": "門", "车": "車", "长": "長", "风": "風", "飞": "飛",
    "马": "馬", "鱼": "魚", "鸟": "鳥", "龙": "龍", "页": "頁",
    "齐": "齊", "齿": "齒", "龟": "龜", "韦": "韋", "见": "見",
    "贝": "貝", "仑": "侖", "仓": "倉", "卢": "盧", "卤": "鹵",
    "尧": "堯", "仑": "侖", "仓": "倉", "卢": "盧",
}

# 独立简化字（最常用的一批）
_SIMPLE_CHARS_LIST = [
    # 第一表 不作偏旁的简化字
    "碍礙", "肮骯", "袄襖", "坝壩", "板闆", "办辦", "帮幫", "宝寶", "报報",
    "币幣", "毙斃", "标標", "表錶", "别彆", "卜蔔", "补補", "才纔",
    "蚕蠶", "灿燦", "层層", "搀攙", "谗讒", "馋饞", "缠纏", "忏懺",
    "偿償", "厂廠", "彻徹", "尘塵", "衬襯", "称稱", "惩懲", "迟遲",
    "冲衝", "丑醜", "出齣", "础礎", "处處", "触觸", "辞辭", "聪聰",
    "丛叢", "担擔", "胆膽", "导導", "灯燈", "邓鄧", "敌敵", "籴糴",
    "递遞", "点點", "淀澱", "电電", "冬鼕", "动動", "冻凍", "栋棟",
    "都覩", "独獨", "吨噸", "夺奪", "堕墮", "儿兒", "矾礬", "范範",
    "飞飛", "坟墳", "奋奮", "粪糞", "凤鳳", "肤膚", "妇婦", "复復複",
    "盖蓋", "干幹", "赶趕", "个個", "巩鞏", "沟溝", "构構", "购購",
    "谷穀", "顾顧", "刮颳", "关關", "观觀", "柜櫃", "汉漢", "号號",
    "合閤", "轰轟", "后後", "胡鬍", "壶壺", "沪滬", "护護", "划劃",
    "怀懷", "坏壞", "欢歡", "环環", "还還", "回迴", "伙夥", "获獲穫",
    "击擊", "鸡鷄", "积積", "极極", "际際", "继繼", "家傢", "价價",
    "艰艱", "歼殲", "茧繭", "拣揀", "硷鹼", "舰艦", "姜薑", "浆漿",
    "桨槳", "奖奬", "讲講", "酱醬", "胶膠", "阶階", "疖癤", "洁潔",
    "借藉", "仅僅", "惊驚", "竞競", "旧舊", "剧劇", "据據", "惧懼",
    "卷捲", "开開", "克剋", "垦墾", "恳懇", "夸誇", "块塊", "亏虧",
    "困睏", "腊臘", "蜡蠟", "兰蘭", "拦攔", "栏欄", "烂爛", "累纍",
    "垒壘", "类類", "里裏", "礼禮", "隶隸", "帘簾", "联聯", "怜憐",
    "炼煉", "练練", "粮糧", "疗療", "辽遼", "了瞭", "猎獵", "临臨",
    "邻鄰", "岭嶺", "庐廬", "芦蘆", "炉爐", "陆陸", "驴驢", "乱亂",
    "么麽", "霉黴", "蒙矇濛懞", "梦夢", "面麵", "庙廟", "灭滅", "蔑衊",
    "亩畝", "恼惱", "脑腦", "拟擬", "酿釀", "疟瘧", "盘盤", "辟闢",
    "苹蘋", "凭憑", "扑撲", "仆僕", "朴樸", "启啓", "签籤", "千韆",
    "牵牽", "纤縴纖", "窍竅", "窃竊", "寝寢", "庆慶", "琼瓊", "秋鞦",
    "曲麯", "权權", "劝勸", "确確", "让讓", "扰擾", "热熱", "认認",
    "洒灑", "伞傘", "丧喪", "扫掃", "涩澀", "晒曬", "伤傷", "舍捨",
    "沈瀋", "声聲", "胜勝", "湿濕", "实實", "适適", "势勢", "兽獸",
    "书書", "术術", "树樹", "帅帥", "松鬆", "苏蘇", "虽雖", "随隨",
    "岁歲", "孙孫", "态態", "坛壇罎", "叹嘆", "誊謄", "体體", "粜糶",
    "铁鐵", "听聽", "厅廳", "头頭", "图圖", "涂塗", "团團糰", "椭橢",
    "洼窪", "袜襪", "网網", "卫衛", "稳穩", "务務", "雾霧", "牺犧",
    "习習", "系係繫", "戏戲", "虾蝦", "吓嚇", "咸鹹", "显顯", "宪憲",
    "县縣", "响響", "向嚮", "协協", "胁脅", "亵褻", "衅釁", "兴興",
    "须鬚", "悬懸", "选選", "旋鏇", "压壓", "盐鹽", "阳陽", "养養",
    "痒癢", "样樣", "钥鑰", "药藥", "爷爺", "叶葉", "医醫", "亿億",
    "忆憶", "应應", "痈癰", "拥擁", "佣傭", "踊踴", "忧憂", "优優",
    "邮郵", "余餘", "御禦", "吁籲", "郁鬱", "誉譽", "渊淵", "园園",
    "远遠", "愿願", "跃躍", "运運", "酝醞", "杂雜", "赃贜", "脏臟髒",
    "凿鑿", "枣棘", "灶竈", "斋齋", "毡氈", "战戰", "赵趙", "折摺",
    "这這", "征徵", "症癥", "证證", "只隻衹", "致緻", "制製", "钟鐘鍾",
    "肿腫", "种種", "众衆", "昼晝", "朱硃", "烛燭", "筑築", "庄莊",
    "桩樁", "妆妝", "装裝", "壮壯", "状狀", "准準", "浊濁", "总總",
    "纵縱", "钻鑽",
]

# 构建简体字集合
for entry in _SIMPLE_CHARS_LIST:
    simp = entry[0]  # 简体字是每项第一个字符
    _SIMPLIFIED_CHARS.add(simp)

# 排除简繁体共用的字（这些字原本就存在于繁体中文中，不应算简体）
_SHARED_CHARS = set(
    "系后里干面表制征余云松斗谷范曲沈郁御吁才霉"
    "舍伙只致准卷克借困夸累么千秋涂咸向旋叶"
    "朱筑辟仆朴确扎折致种"
)
_SIMPLIFIED_CHARS -= _SHARED_CHARS

# 偏旁类推：含这些偏旁的字也算简体
_SIMPLE_RADICALS = set(_RADICAL_SIMPLE_MAP.keys())


def _has_simplified_chinese(text: str) -> bool:
    """检测文本是否包含纯简体字（简繁体共用的字不算）。

    使用 zhconv 将文本转为繁体，如果结果不同则说明含简体字。
    排除繁体中合法使用的共用字（如 台/臺 在繁体都可用）。
    """
    try:
        from zhconv import convert
        converted = convert(text, "zh-hant")
        if converted == text:
            return False

        # 逐字比较，排除繁体中合法存在的共用字
        _shared_in_traditional = set("台")
        for i, (orig, conv) in enumerate(zip(text, converted)):
            if orig in _shared_in_traditional:
                continue
            if orig != conv:
                return True
        return False
    except ImportError:
        pass

    # 回退：用内置简体字集合检测
    for ch in text:
        if ch in _SIMPLIFIED_CHARS:
            return True
        for radical in _SIMPLE_RADICALS:
            if radical in ch:
                return True
    return False


# 操作符实现
def _op_equals(item_val: str, rule_val: str) -> bool:
    return item_val.lower().strip() == rule_val.lower().strip()


def _op_contains(item_val: str, rule_val: str) -> bool:
    return rule_val.lower() in item_val.lower()


def _op_starts_with(item_val: str, rule_val: str) -> bool:
    return item_val.lower().startswith(rule_val.lower())


def _op_regex(item_val: str, rule_val: str) -> bool:
    try:
        return bool(re.search(rule_val, item_val, re.IGNORECASE))
    except re.error:
        return False


def _op_in_list(item_val: str, rule_val: str) -> bool:
    allowed = {v.strip().lower() for v in rule_val.split(",") if v.strip()}
    return item_val.lower().strip() in allowed


def _op_not_in_list(item_val: str, rule_val: str) -> bool:
    return not _op_in_list(item_val, rule_val)


def _op_in_whitelist(item_val: str, _rule_val: str, *, word_list: list[str] | None = None) -> bool:
    if word_list is None:
        return False
    return any(w and w in item_val.lower() for w in word_list)


def _op_in_blacklist(item_val: str, _rule_val: str, *, word_list: list[str] | None = None) -> bool:
    return _op_in_whitelist(item_val, _rule_val, word_list=word_list)


def _op_has_cn(item_val: str, _rule_val: str) -> bool:
    """检测文本是否包含纯简体字（简繁体共用的字不算）。"""
    return _has_simplified_chinese(item_val)


def _op_starts_with_content_wl(item_val: str, _rule_val: str, *, word_list: list[str] | None = None) -> bool:
    """检测文本是否以 content_whitelist 中任一项开头。"""
    if word_list is None:
        return False
    target = item_val.lower()
    return any(w and target.startswith(w) for w in word_list)


def _op_not_starts_with(item_val: str, rule_val: str) -> bool:
    """检测文本是否不以指定前缀开头。"""
    return not item_val.lower().startswith(rule_val.lower())


def _op_not_equals(item_val: str, rule_val: str) -> bool:
    return not _op_equals(item_val, rule_val)


def _op_not_regex(item_val: str, rule_val: str) -> bool:
    return not _op_regex(item_val, rule_val)


def _op_is_empty(item_val: str, _rule_val: str) -> bool:
    """检测文本是否为空（去除空白后）。"""
    return not item_val.strip()


def _op_starts_with_any(item_val: str, rule_val: str) -> bool:
    """检测文本是否以任一逗号分隔的前缀开头。"""
    prefixes = [v.strip().lower() for v in rule_val.split(",") if v.strip()]
    target = item_val.lower()
    return any(target.startswith(p) for p in prefixes)


OPERATORS = {
    "equals": _op_equals,
    "contains": _op_contains,
    "starts_with": _op_starts_with,
    "starts_with_any": _op_starts_with_any,
    "not_starts_with": _op_not_starts_with,
    "regex": _op_regex,
    "has_cn": _op_has_cn,
    "is_empty": _op_is_empty,
    "not_equals": _op_not_equals,
    "not_regex": _op_not_regex,
    "in_list": _op_in_list,
    "not_in_list": _op_not_in_list,
    "in_whitelist": _op_in_whitelist,
    "in_blacklist": _op_in_blacklist,
    "starts_with_content_wl": _op_starts_with_content_wl,
}

# 字段名 → item dict key 映射
FIELD_MAP = {
    "申请人": "applicant",
    "申请单号": "no",
    "编号": "no",
    "no": "no",
    "描述": "description",
    "物料描述": "description",
    "description": "description",
    "单位": "uom",
    "uom": "uom",
    "类别": "item_type",
    "item type": "item_type",
    "item_type": "item_type",
}


def _get_field_value(item: dict, field: str) -> str:
    key = FIELD_MAP.get(field.lower(), field.lower())
    return str(item.get(key, ""))


def _check_condition(condition: dict, item: dict, word_lists: dict[str, list[str]]) -> bool:
    """检查单个条件是否匹配。"""
    field = condition.get("field", "")
    op = condition.get("op", "contains")
    value = condition.get("value", "")

    item_val = _get_field_value(item, field)
    op_func = OPERATORS.get(op)
    if op_func is None:
        return False

    # 需要外挂词表的操作符
    if op in ("in_whitelist", "in_blacklist"):
        list_name = "whitelist" if op == "in_whitelist" else "blacklist"
        return op_func(item_val, value, word_list=word_lists.get(list_name, []))
    if op == "starts_with_content_wl":
        return op_func(item_val, value, word_list=word_lists.get("content_whitelist", []))

    return op_func(item_val, value)


def _match_rule_group(rule: dict, item: dict, word_lists: dict[str, list[str]]) -> bool:
    """检查一个规则组是否匹配（内部 AND 或 OR 组合）。"""
    conditions = rule.get("conditions", [])
    logic = rule.get("logic", "AND").upper()

    if not conditions:
        return False

    results = [_check_condition(c, item, word_lists) for c in conditions]

    if logic == "OR":
        return any(results)
    else:  # AND
        return all(results)


def match_rules(
    item: dict,
    rules: dict,
    word_lists: dict[str, list[str]] | None = None,
) -> tuple[str, str]:
    """对单个项目应用规则，返回 (action, matched_rule_name)。

    action 取值: "approve", "reject", "notify", ""（无匹配）
    """
    if word_lists is None:
        word_lists = {}

    # auto_reject 优先
    for rule in rules.get("auto_reject", []):
        if _match_rule_group(rule, item, word_lists):
            return "reject", rule.get("name", "")

    # auto_approve
    for rule in rules.get("auto_approve", []):
        if _match_rule_group(rule, item, word_lists):
            return "approve", rule.get("name", "")

    # notify
    for rule in rules.get("notify", []):
        if _match_rule_group(rule, item, word_lists):
            return "notify", rule.get("name", "")

    return "", ""


def load_rules(path: str = "rules.json") -> dict:
    """加载规则文件，不存在则返回空规则。"""
    p = Path(path)
    if not p.exists():
        return {}
    try:
        with p.open("r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def load_word_lists(base_dir: str = ".", rules: dict | None = None) -> dict[str, list[str]]:
    """加载白名单和黑名单。优先 rules.json 内联 > 文件。

    rules.json 可包含 "whitelist" 和 "content_whitelist" 数组。
    """
    cwd = Path.cwd()
    skill = Path(base_dir)
    lists: dict[str, list[str]] = {}

    if rules:
        for key in ("whitelist", "content_whitelist"):
            if key in rules:
                lists[key] = [str(v).lower() for v in rules[key]]

    for list_name, filename in [("whitelist", "whitelist.txt"), ("blacklist", "name_blacklist.txt"), ("content_whitelist", "content_whitelist.txt")]:
        if list_name in lists:
            continue
        loaded = False
        for base in (cwd, skill):
            path = base / filename
            if path.exists():
                try:
                    with path.open("r", encoding="utf-8-sig") as f:
                        lists[list_name] = [line.strip().lower() for line in f if line.strip()]
                    loaded = True
                    break
                except UnicodeDecodeError:
                    try:
                        with path.open("r", encoding="gbk") as f:
                            lists[list_name] = [line.strip().lower() for line in f if line.strip()]
                        loaded = True
                        break
                    except UnicodeDecodeError:
                        continue
        if not loaded:
            lists[list_name] = []

    return lists
