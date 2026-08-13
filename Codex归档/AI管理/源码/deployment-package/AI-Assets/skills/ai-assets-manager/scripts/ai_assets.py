#!/usr/bin/env python3
"""Dependency-aware catalog manager for shared AI Skills, CLIs, and Agents."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict, deque
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog.json"
LOCK = ROOT / "ai-assets.lock.json"
SEMVER = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")
ASSET_ID = re.compile(r"^(skill|cli|agent)/[a-z0-9][a-z0-9._-]*$")


def version_tuple(value: str) -> tuple[int, int, int]:
    match = SEMVER.fullmatch(value)
    if not match:
        raise ValueError(f"不是有效的 SemVer 精确版本: {value}")
    return tuple(map(int, match.groups()))


def satisfies(version: str, constraint: str) -> bool:
    current = version_tuple(version)
    constraint = constraint.strip()
    if constraint.startswith("^"):
        base = version_tuple(constraint[1:])
        if base[0] > 0:
            upper = (base[0] + 1, 0, 0)
        elif base[1] > 0:
            upper = (0, base[1] + 1, 0)
        else:
            upper = (0, 0, base[2] + 1)
        return base <= current < upper
    if constraint.startswith("~"):
        base = version_tuple(constraint[1:])
        return base <= current < (base[0], base[1] + 1, 0)
    if SEMVER.fullmatch(constraint):
        return current == version_tuple(constraint)

    parts = constraint.split()
    if not parts:
        raise ValueError("版本约束不能为空")
    for part in parts:
        match = re.fullmatch(r"(>=|<=|>|<|=)(\d+\.\d+\.\d+)", part)
        if not match:
            raise ValueError(f"不支持的版本约束: {constraint}")
        op, raw = match.groups()
        target = version_tuple(raw)
        ok = {
            ">=": current >= target,
            "<=": current <= target,
            ">": current > target,
            "<": current < target,
            "=": current == target,
        }[op]
        if not ok:
            return False
    return True


def load_catalog() -> dict:
    with CATALOG.open(encoding="utf-8") as handle:
        return json.load(handle)


def asset_map(data: dict) -> dict[str, dict]:
    return {asset["id"]: asset for asset in data.get("assets", []) if "id" in asset}


def validation_errors(data: dict) -> list[str]:
    errors: list[str] = []
    assets = data.get("assets")
    if data.get("catalogVersion") != 1:
        errors.append("catalogVersion 必须为 1")
    if not isinstance(assets, list):
        return errors + ["assets 必须是数组"]

    ids: set[str] = set()
    for index, asset in enumerate(assets):
        label = asset.get("id", f"assets[{index}]")
        asset_id = asset.get("id")
        if not isinstance(asset_id, str) or not ASSET_ID.fullmatch(asset_id):
            errors.append(f"{label}: id 格式无效")
            continue
        if asset_id in ids:
            errors.append(f"{asset_id}: ID 重复")
        ids.add(asset_id)
        try:
            version_tuple(asset.get("version", ""))
        except ValueError as exc:
            errors.append(f"{asset_id}: {exc}")
        if not asset.get("owner"):
            errors.append(f"{asset_id}: 缺少 owner")
        if asset.get("lifecycle") not in {"active", "deprecated", "retired"}:
            errors.append(f"{asset_id}: lifecycle 无效")
        source = asset.get("source", {})
        if not source.get("type") or not source.get("location"):
            errors.append(f"{asset_id}: source 不完整")

    by_id = asset_map(data)
    graph: dict[str, list[str]] = defaultdict(list)
    for asset in assets:
        if asset.get("id") not in by_id:
            continue
        for dep in asset.get("dependencies", []):
            dep_id = dep.get("id")
            if dep_id not in by_id:
                if dep.get("required", True):
                    errors.append(f"{asset['id']}: 缺少必需依赖 {dep_id}")
                continue
            try:
                if not satisfies(by_id[dep_id]["version"], dep.get("version", "")):
                    errors.append(
                        f"{asset['id']}: {dep_id}={by_id[dep_id]['version']} "
                        f"不满足 {dep.get('version')}"
                    )
            except ValueError as exc:
                errors.append(f"{asset['id']} -> {dep_id}: {exc}")
            if dep.get("required", True):
                graph[asset["id"]].append(dep_id)

    state: dict[str, int] = {}
    stack: list[str] = []

    def visit(node: str) -> None:
        if state.get(node) == 1:
            start = stack.index(node)
            errors.append("循环依赖: " + " -> ".join(stack[start:] + [node]))
            return
        if state.get(node) == 2:
            return
        state[node] = 1
        stack.append(node)
        for neighbor in graph[node]:
            visit(neighbor)
        stack.pop()
        state[node] = 2

    for asset_id in by_id:
        visit(asset_id)
    return list(dict.fromkeys(errors))


def dependency_order(data: dict) -> list[str]:
    by_id = asset_map(data)
    indegree = {item: 0 for item in by_id}
    consumers: dict[str, list[str]] = defaultdict(list)
    for asset in by_id.values():
        for dep in asset.get("dependencies", []):
            if dep.get("required", True) and dep.get("id") in by_id:
                indegree[asset["id"]] += 1
                consumers[dep["id"]].append(asset["id"])
    queue = deque(sorted(item for item, degree in indegree.items() if degree == 0))
    result: list[str] = []
    while queue:
        item = queue.popleft()
        result.append(item)
        for consumer in sorted(consumers[item]):
            indegree[consumer] -= 1
            if indegree[consumer] == 0:
                queue.append(consumer)
    if len(result) != len(by_id):
        raise ValueError("存在循环依赖，无法生成顺序")
    return result


def command_validate(data: dict) -> int:
    errors = validation_errors(data)
    if errors:
        print("校验失败:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"校验通过: {len(data['assets'])} 项资产，依赖关系有效。")
    return 0


def command_list(data: dict) -> int:
    print(f"{'ID':<28} {'VERSION':<12} {'STATUS':<12} OWNER")
    for asset in sorted(data["assets"], key=lambda item: item["id"]):
        print(f"{asset['id']:<28} {asset['version']:<12} {asset['lifecycle']:<12} {asset['owner']}")
    return 0


def command_graph(data: dict, mermaid: bool) -> int:
    if mermaid:
        print("graph TD")
        for asset in sorted(data["assets"], key=lambda item: item["id"]):
            if not asset.get("dependencies"):
                print(f'  {safe_node(asset["id"])}["{asset["id"]} {asset["version"]}"]')
            for dep in asset.get("dependencies", []):
                style = "-.->" if not dep.get("required", True) else "-->"
                print(f'  {safe_node(asset["id"])} {style}|"{dep["version"]}"| {safe_node(dep["id"])}')
    else:
        for asset_id in dependency_order(data):
            asset = asset_map(data)[asset_id]
            deps = asset.get("dependencies", [])
            rendered = ", ".join(f"{d['id']} {d['version']}" for d in deps) or "无"
            print(f"{asset_id} {asset['version']} 依赖: {rendered}")
    return 0


def safe_node(asset_id: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]", "_", asset_id)


def command_impact(data: dict, target: str) -> int:
    by_id = asset_map(data)
    if target not in by_id:
        print(f"未知资产: {target}", file=sys.stderr)
        return 2
    reverse: dict[str, list[str]] = defaultdict(list)
    for asset in by_id.values():
        for dep in asset.get("dependencies", []):
            if dep.get("id") in by_id:
                reverse[dep["id"]].append(asset["id"])
    queue = deque([(target, 0)])
    seen = {target}
    print(f"{target} 的升级影响:")
    while queue:
        item, depth = queue.popleft()
        for consumer in sorted(reverse[item]):
            if consumer not in seen:
                seen.add(consumer)
                print(f"{'  ' * (depth + 1)}- {consumer}")
                queue.append((consumer, depth + 1))
    if len(seen) == 1:
        print("- 无下游资产")
    return 0


def make_lock(data: dict) -> dict:
    by_id = asset_map(data)
    return {
        "lockVersion": 1,
        "catalogVersion": data["catalogVersion"],
        "installOrder": dependency_order(data),
        "assets": {
            asset_id: {
                "version": by_id[asset_id]["version"],
                "source": by_id[asset_id]["source"],
                "dependencies": {
                    dep["id"]: by_id[dep["id"]]["version"]
                    for dep in by_id[asset_id].get("dependencies", [])
                    if dep.get("id") in by_id
                },
            }
            for asset_id in sorted(by_id)
        },
    }


def command_lock(data: dict, check: bool) -> int:
    errors = validation_errors(data)
    if errors:
        return command_validate(data)
    expected = json.dumps(make_lock(data), ensure_ascii=False, indent=2) + "\n"
    if check:
        actual = LOCK.read_text(encoding="utf-8") if LOCK.exists() else ""
        if actual != expected:
            print("lock 文件缺失或不是最新，请执行 lock。", file=sys.stderr)
            return 1
        print("lock 文件是最新的。")
        return 0
    LOCK.write_text(expected, encoding="utf-8")
    print(f"已生成 {LOCK.name}")
    return 0


def command_bump(data: dict, target: str, version: str, write: bool) -> int:
    by_id = asset_map(data)
    if target not in by_id:
        print(f"未知资产: {target}", file=sys.stderr)
        return 2
    try:
        version_tuple(version)
    except ValueError as exc:
        print(exc, file=sys.stderr)
        return 2
    old = by_id[target]["version"]
    by_id[target]["version"] = version
    errors = validation_errors(data)
    if errors:
        by_id[target]["version"] = old
        print(f"无法把 {target} 从 {old} 升级到 {version}:")
        for error in errors:
            print(f"- {error}")
        return 1
    print(f"升级预检通过: {target} {old} -> {version}")
    if write:
        CATALOG.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print("已更新 catalog.json；请重新生成 lock 文件。")
    else:
        print("这是预演；添加 --write 才会修改 catalog.json。")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="统一管理团队 AI Skill 与 CLI")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("validate", help="校验目录、版本和依赖")
    sub.add_parser("list", help="列出全部资产")
    graph = sub.add_parser("graph", help="显示依赖关系")
    graph.add_argument("--mermaid", action="store_true", help="输出 Mermaid 图")
    impact = sub.add_parser("impact", help="查看一个资产的下游影响")
    impact.add_argument("asset_id")
    lock = sub.add_parser("lock", help="生成或检查版本快照")
    lock.add_argument("--check", action="store_true")
    bump = sub.add_parser("bump", help="预检或写入版本升级")
    bump.add_argument("asset_id")
    bump.add_argument("version")
    bump.add_argument("--write", action="store_true")
    args = parser.parse_args()

    try:
        data = load_catalog()
    except (OSError, json.JSONDecodeError) as exc:
        print(f"无法读取 catalog.json: {exc}", file=sys.stderr)
        return 2

    if args.command == "validate":
        return command_validate(data)
    if args.command == "list":
        return command_list(data)
    if args.command == "graph":
        return command_graph(data, args.mermaid)
    if args.command == "impact":
        return command_impact(data, args.asset_id)
    if args.command == "lock":
        return command_lock(data, args.check)
    if args.command == "bump":
        return command_bump(data, args.asset_id, args.version, args.write)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
