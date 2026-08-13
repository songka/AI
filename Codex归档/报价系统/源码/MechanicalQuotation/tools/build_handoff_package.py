#!/usr/bin/env python
"""Build a secret-free software handoff folder and archive."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_NAME = "MechanicalQuotation_软件交底版_20260810_v8"


def _load_portable_builder():
    path = ROOT / "tools" / "build_portable.py"
    spec = importlib.util.spec_from_file_location("mq_build_portable", path)
    if spec is None or spec.loader is None:
        raise RuntimeError("无法载入便携版构建工具")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _source_ignore(directory: str, names: list[str]) -> set[str]:
    ignored: set[str] = set()
    for name in names:
        lowered = name.casefold()
        if (
            lowered in {
                ".git", ".venv", "venv", "build", "dist", "runtime",
                "htmlcov", "__pycache__", ".pytest_cache", ".ruff_cache",
                ".mypy_cache",
            }
            or lowered.startswith((".pytest", ".test-", ".test_", ".codex", ".launcher"))
            or lowered.endswith((".pyc", ".pyo", ".zip"))
            or lowered.startswith("mechanicalquotation_")
        ):
            ignored.add(name)
    return ignored


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _assert_secret_free(root: Path) -> None:
    forbidden_names = {
        "deepseek_api_key.txt",
        "user_store_key.txt",
        "quotation_history.db",
    }
    found = [path for path in root.rglob("*") if path.is_file() and path.name in forbidden_names]
    if found:
        details = ", ".join(str(path.relative_to(root)) for path in found)
        raise RuntimeError(f"交底包发现禁止交付的运行文件：{details}")


def _write_manifest(root: Path) -> Path:
    manifest = root / "SHA256SUMS.txt"
    lines: list[str] = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        if path == manifest:
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        lines.append(f"{digest}  {path.relative_to(root).as_posix()}")
    _write(manifest, "\n".join(lines) + "\n")
    return manifest


def build(output_parent: Path, name: str, backend: str) -> tuple[Path, Path]:
    destination = output_parent.resolve() / name
    if destination.exists():
        raise FileExistsError(f"目标交底目录已存在，请换版本名：{destination}")

    portable_builder = _load_portable_builder()
    portable = portable_builder.build(backend=backend)

    source_target = destination / "01_源代码" / "MechanicalQuotation"
    program_target = destination / "02_可执行程序" / "MechanicalQuotation"
    docs_target = destination / "03_交底资料"
    tool_target = destination / "04_Skill与Agent工具" / "external-quotation-skill-refactor"
    config_target = destination / "05_配置模板"

    shutil.copytree(ROOT, source_target, ignore=_source_ignore)
    shutil.copytree(portable, program_target)
    shutil.copytree(ROOT / "docs" / "handoff", docs_target)
    shutil.copytree(ROOT / "skills" / "external-quotation-skill-refactor", tool_target)
    config_target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "config" / "user_settings.example.json",
        config_target / "user_settings.example.json",
    )
    _write(
        config_target / "数据库地址示例.json",
        json.dumps(
            {
                "本机目录": "runtime/data",
                "本机文件": "D:/MechanicalQuotationData/quotes.db",
                "公共目录": "\\\\server\\quotation\\database",
                "公共文件": "\\\\server\\quotation\\database\\quotes.db",
            },
            ensure_ascii=False,
            indent=2,
        ) + "\n",
    )
    _write(
        config_target / "Key配置说明.txt",
        "本交底包默认不含任何 Key。\n"
        "需要 AI 时，请在软件“系统设置”中点击“从文件设置/更换”，"
        "选择仅含一行 Key 的 UTF-8 文本文件。\n"
        "不要把真实 Key 放入本交底目录、源代码、公共槽 Skill/Agent 或压缩包。\n",
    )
    _write(
        destination / "请先阅读.txt",
        "机械加工件智能报价系统软件交底版\n\n"
        "请先打开 03_交底资料\\00_交底资料索引.md。\n"
        "可执行程序位于 02_可执行程序\\MechanicalQuotation。\n"
        "本交底包默认无 Key、无用户口令、无报价历史数据库。\n",
    )

    _assert_secret_free(destination)
    _write_manifest(destination)
    archive = Path(
        shutil.make_archive(str(destination), "zip", destination.parent, destination.name)
    )
    return destination, archive


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-parent", type=Path, default=ROOT.parent)
    parser.add_argument("--name", default=DEFAULT_NAME)
    parser.add_argument(
        "--backend", choices=("python-runtime", "pyinstaller", "existing"),
        default="python-runtime",
    )
    args = parser.parse_args()
    folder, archive = build(args.output_parent, args.name, args.backend)
    print(f"交底目录：{folder}")
    print(f"交底压缩包：{archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
