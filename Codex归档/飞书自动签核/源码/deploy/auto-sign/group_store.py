# -*- coding: utf-8 -*-
"""每个飞书用户独立的用户组、内容组存储与旧名单兼容。"""

from __future__ import annotations

import json
import os
from pathlib import Path

from user_manager import ensure_user_dir, get_user_dir, get_user_rules, save_user_rules


DEFAULT_USER_GROUP = "默认用户组"
RESTRICTED_USER_GROUP = "限制用户组"
DEFAULT_CONTENT_GROUP = "默认内容组"
GROUP_TYPES = ("user_groups", "content_groups")
GROUP_SCHEMA_VERSION = 2

LEGACY_GROUP_SOURCES = {
    "whitelist": ("user_groups", DEFAULT_USER_GROUP, "whitelist.txt"),
    "blacklist": ("user_groups", RESTRICTED_USER_GROUP, "name_blacklist.txt"),
    "content_whitelist": ("content_groups", DEFAULT_CONTENT_GROUP, "content_whitelist.txt"),
}

GROUP_OPERATORS = {
    "user_groups": {"in_user_group", "not_in_user_group"},
    "content_groups": {
        "starts_with_content_group",
        "not_starts_with_content_group",
        "ends_with_content_group",
        "not_ends_with_content_group",
        "contains_content_group",
        "not_contains_content_group",
    },
}


def _empty_groups() -> dict:
    return {
        "version": GROUP_SCHEMA_VERSION,
        "user_groups": {},
        "content_groups": {},
        "legacy_migrations": {},
    }


def _clean_items(values) -> list[str]:
    if not isinstance(values, (list, tuple, set)):
        return []
    result = []
    seen = set()
    for value in values:
        item = str(value or "").strip()
        folded = item.casefold()
        if item and folded not in seen:
            seen.add(folded)
            result.append(item)
    return result


def _normalize_groups(data) -> dict:
    result = _empty_groups()
    if not isinstance(data, dict):
        return result
    for group_type in GROUP_TYPES:
        raw_groups = data.get(group_type, {})
        if not isinstance(raw_groups, dict):
            continue
        for name, values in raw_groups.items():
            clean_name = str(name or "").strip()
            if clean_name:
                result[group_type][clean_name] = _clean_items(values)
    migrations = data.get("legacy_migrations", {})
    if isinstance(migrations, dict):
        result["legacy_migrations"] = {
            key: True
            for key, value in migrations.items()
            if key in LEGACY_GROUP_SOURCES and value is True
        }
    return result


def _read_json(path: Path):
    try:
        with path.open("r", encoding="utf-8-sig") as stream:
            return json.load(stream)
    except (OSError, json.JSONDecodeError, TypeError):
        return {}


def _read_legacy_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    for encoding in ("utf-8-sig", "gbk"):
        try:
            return _clean_items(path.read_text(encoding=encoding).splitlines())
        except (OSError, UnicodeDecodeError):
            continue
    return []


def _legacy_values(open_id: str, rules: dict | None = None) -> dict[str, list[str]]:
    current = rules if isinstance(rules, dict) else get_user_rules(open_id)
    user_dir = get_user_dir(open_id)

    def values(key: str, filename: str) -> list[str]:
        inline = _clean_items(current.get(key, []))
        return inline if inline else _read_legacy_file(user_dir / filename)

    return {
        DEFAULT_USER_GROUP: values("whitelist", "whitelist.txt"),
        RESTRICTED_USER_GROUP: values("blacklist", "name_blacklist.txt"),
        DEFAULT_CONTENT_GROUP: values("content_whitelist", "content_whitelist.txt"),
    }


def _legacy_source_for_group(group_type: str, group_name: str) -> str:
    for source, (source_type, source_name, _filename) in LEGACY_GROUP_SOURCES.items():
        if source_type == group_type and source_name == group_name:
            return source
    return ""


def _same_group_values(left, right) -> bool:
    return {
        str(value or "").strip().casefold()
        for value in left
        if str(value or "").strip()
    } == {
        str(value or "").strip().casefold()
        for value in right
        if str(value or "").strip()
    }


def _merge_unconsumed_legacy_groups(groups: dict, legacy: dict[str, list[str]]) -> dict:
    """只映射尚未被改名/删除的旧名单，兼容修复前已产生的重复组。"""
    migrations = groups.setdefault("legacy_migrations", {})
    for source, (group_type, group_name, _filename) in LEGACY_GROUP_SOURCES.items():
        values = legacy.get(group_name, [])
        if not values or migrations.get(source) is True:
            continue
        if group_name in groups[group_type]:
            # 修复旧版本已把“默认组 + 改名组”同时写入 groups.json 的状态。
            if any(
                existing_name != group_name
                and _same_group_values(existing_values, values)
                for existing_name, existing_values in groups[group_type].items()
            ):
                groups[group_type].pop(group_name)
                migrations[source] = True
            continue
        # 旧版本改名后没有保存迁移标记；若已有同内容组，视为已完成改名。
        if any(
            _same_group_values(existing_values, values)
            for existing_values in groups[group_type].values()
        ):
            migrations[source] = True
            continue
        groups[group_type][group_name] = values
    return groups


def get_user_groups(open_id: str, include_legacy: bool = True) -> dict:
    """读取组；旧名单只在内存中映射，不主动改写旧规则。"""
    ensure_user_dir(open_id)
    groups = _normalize_groups(_read_json(get_user_dir(open_id) / "groups.json"))
    if not include_legacy:
        return groups

    return _merge_unconsumed_legacy_groups(groups, _legacy_values(open_id))


def save_user_groups(open_id: str, groups: dict) -> dict:
    """原子写入 groups.json；不删除任何旧名单文件或旧字段。"""
    normalized = _normalize_groups(groups)
    directory = ensure_user_dir(open_id)
    target = directory / "groups.json"
    temporary = directory / "groups.json.tmp"
    with temporary.open("w", encoding="utf-8") as stream:
        json.dump(normalized, stream, indent=2, ensure_ascii=False)
    os.replace(str(temporary), str(target))
    return normalized


def validate_group_name(name: str) -> str:
    clean_name = str(name or "").strip()
    if not clean_name:
        raise ValueError("组名不能为空")
    if len(clean_name) > 40:
        raise ValueError("组名不能超过 40 个字符")
    if any(char in clean_name for char in ("\n", "\r", "|")):
        raise ValueError("组名不能包含换行或 |")
    return clean_name


def parse_group_items(value) -> list[str]:
    """卡片中一行一项；文字备用入口也可用 | 分隔。"""
    if isinstance(value, (list, tuple, set)):
        items = value
    else:
        text = str(value or "").replace("\r\n", "\n").replace("\r", "\n")
        items = []
        for line in text.split("\n"):
            items.extend(line.split("|"))
    cleaned = _clean_items(items)
    if len(cleaned) > 500:
        raise ValueError("每个组最多 500 项")
    if any(len(item) > 200 for item in cleaned):
        raise ValueError("每项内容不能超过 200 个字符")
    return cleaned


def create_group(open_id: str, group_type: str, name: str) -> dict:
    if group_type not in GROUP_TYPES:
        raise ValueError("组类型无效")
    clean_name = validate_group_name(name)
    groups = get_user_groups(open_id)
    if any(existing.casefold() == clean_name.casefold() for existing in groups[group_type]):
        raise ValueError("同类型中已存在这个组名")
    groups[group_type][clean_name] = []
    return save_user_groups(open_id, groups)


def _legacy_condition_matches(group_type: str, group_name: str, operator: str) -> bool:
    return (
        (group_type == "user_groups" and group_name == DEFAULT_USER_GROUP and operator == "in_whitelist")
        or (group_type == "user_groups" and group_name == RESTRICTED_USER_GROUP and operator == "in_blacklist")
        or (
            group_type == "content_groups"
            and group_name == DEFAULT_CONTENT_GROUP
            and operator == "starts_with_content_wl"
        )
    )


def group_rule_references(open_id: str, group_type: str, group_name: str) -> list[str]:
    references = []
    rules = get_user_rules(open_id)
    for rule_type in ("auto_reject", "auto_approve", "notification_rules"):
        for index, rule in enumerate(rules.get(rule_type, [])):
            for condition in rule.get("conditions", []):
                operator = str(condition.get("op", ""))
                value = str(condition.get("value", "")).strip()
                if (
                    operator in GROUP_OPERATORS.get(group_type, set())
                    and value.casefold() == group_name.casefold()
                ) or _legacy_condition_matches(group_type, group_name, operator):
                    references.append(
                        f"{rule_type}[{index}] {rule.get('name', '未命名规则')}"
                    )
                    break
    return references


def _rename_rule_references(
    open_id: str,
    group_type: str,
    old_name: str,
    new_name: str,
) -> None:
    rules = get_user_rules(open_id)
    changed = False
    for rule_type in ("auto_reject", "auto_approve", "notification_rules"):
        for rule in rules.get(rule_type, []):
            for condition in rule.get("conditions", []):
                operator = str(condition.get("op", ""))
                value = str(condition.get("value", "")).strip()
                if (
                    operator in GROUP_OPERATORS.get(group_type, set())
                    and value.casefold() == old_name.casefold()
                ):
                    condition["value"] = new_name
                    changed = True
                elif _legacy_condition_matches(group_type, old_name, operator):
                    condition["op"] = (
                        "in_user_group"
                        if group_type == "user_groups"
                        else "starts_with_content_group"
                    )
                    condition["value"] = new_name
                    changed = True
    if changed:
        save_user_rules(open_id, rules)


def update_group(
    open_id: str,
    group_type: str,
    old_name: str,
    new_name: str,
    items,
) -> dict:
    if group_type not in GROUP_TYPES:
        raise ValueError("组类型无效")
    original = validate_group_name(old_name)
    renamed = validate_group_name(new_name)
    values = parse_group_items(items)
    groups = get_user_groups(open_id)
    if original not in groups[group_type]:
        raise ValueError("组不存在或已经删除")
    if renamed.casefold() != original.casefold() and any(
        existing.casefold() == renamed.casefold()
        for existing in groups[group_type]
    ):
        raise ValueError("同类型中已存在这个组名")

    updated_type = dict(groups[group_type])
    updated_type.pop(original)
    updated_type[renamed] = values
    groups[group_type] = updated_type
    legacy_source = _legacy_source_for_group(group_type, original)
    if legacy_source:
        groups.setdefault("legacy_migrations", {})[legacy_source] = True
    save_user_groups(open_id, groups)
    # 即使组名未变化，首次从卡片保存兼容组时也把对应旧操作符转成新组操作符。
    _rename_rule_references(open_id, group_type, original, renamed)
    return get_user_groups(open_id)


def delete_group(open_id: str, group_type: str, name: str) -> dict:
    if group_type not in GROUP_TYPES:
        raise ValueError("组类型无效")
    clean_name = validate_group_name(name)
    references = group_rule_references(open_id, group_type, clean_name)
    if references:
        preview = "；".join(references[:3])
        suffix = "…" if len(references) > 3 else ""
        raise ValueError(f"该组正被规则引用，请先修改规则：{preview}{suffix}")
    groups = get_user_groups(open_id)
    if clean_name not in groups[group_type]:
        raise ValueError("组不存在或已经删除")
    groups[group_type].pop(clean_name)
    legacy_source = _legacy_source_for_group(group_type, clean_name)
    if legacy_source:
        groups.setdefault("legacy_migrations", {})[legacy_source] = True
    return save_user_groups(open_id, groups)


def group_values_for_rules(base_dir: str | Path, rules: dict | None = None) -> dict:
    """供规则引擎读取，不依赖飞书 open_id。"""
    base = Path(base_dir)
    groups = _normalize_groups(_read_json(base / "groups.json"))
    current_rules = rules if isinstance(rules, dict) else {}

    legacy = {}
    for source, (_group_type, group_name, filename) in LEGACY_GROUP_SOURCES.items():
        legacy[group_name] = (
            _clean_items(current_rules.get(source, []))
            or _read_legacy_file(base / filename)
        )
    return _merge_unconsumed_legacy_groups(groups, legacy)
