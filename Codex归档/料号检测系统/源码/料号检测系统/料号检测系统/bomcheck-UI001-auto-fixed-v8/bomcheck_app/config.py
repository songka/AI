from __future__ import annotations

import json
import logging
import os
import re
import shutil
from dataclasses import dataclass
from json import JSONDecodeError
from pathlib import Path
from typing import Any, Dict


logger = logging.getLogger(__name__)


DEFAULT_CONFIG = {
    "invalid_part_db": r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\12失效料号查询系统\数据库\失效料号.xlsx",
    "binding_library": r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\12失效料号查询系统\数据库\绑定料号.js",
    "important_materials": r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\12失效料号查询系统\数据库\重要物料.txt",
    "system_part_db": r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\12失效料号查询系统\数据库\系统物料.xlsx",
    "blocked_applicants": r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\12失效料号查询系统\数据库\屏蔽申请人.txt",
    "part_asset_dir": r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\12失效料号查询系统\数据库\料号资源",
    "account_store": r"\\10.97.0.210\lfaf_Engineer\电控历史资料\7-内部运算公式\12失效料号查询系统\数据库\accounts.json",
    "ua_lookup_dir": "",
    "asset_unc_prefix": "",
    "asset_local_prefix": "",
}


@dataclass
class AppConfig:
    invalid_part_db: Path
    binding_library: Path
    important_materials: Path
    system_part_db: Path
    blocked_applicants: Path
    part_asset_dir: Path
    account_store: Path
    ua_lookup_dir: Path | None
    asset_unc_prefix: str = ""
    asset_local_prefix: str = ""

    @classmethod
    def from_dict(cls, data: Dict[str, Any], base_dir: Path) -> "AppConfig":
        return cls(
            invalid_part_db=_resolve_path(
                data.get("invalid_part_db") or DEFAULT_CONFIG["invalid_part_db"],
                base_dir,
            ),
            binding_library=_resolve_path(
                data.get("binding_library") or DEFAULT_CONFIG["binding_library"],
                base_dir,
            ),
            important_materials=_resolve_path(
                data.get("important_materials") or DEFAULT_CONFIG["important_materials"],
                base_dir,
            ),
            system_part_db=_resolve_path(
                data.get("system_part_db") or DEFAULT_CONFIG["system_part_db"],
                base_dir,
            ),
            blocked_applicants=_resolve_path(
                data.get("blocked_applicants") or DEFAULT_CONFIG["blocked_applicants"],
                base_dir,
            ),
            part_asset_dir=_resolve_path(
                data.get("part_asset_dir") or DEFAULT_CONFIG["part_asset_dir"],
                base_dir,
            ),
            account_store=_resolve_path(
                data.get("account_store") or DEFAULT_CONFIG["account_store"],
                base_dir,
            ),
            ua_lookup_dir=_resolve_optional_path(
                data.get("ua_lookup_dir"), base_dir
            ),
            asset_unc_prefix=str(data.get("asset_unc_prefix") or ""),
            asset_local_prefix=str(data.get("asset_local_prefix") or ""),
        )

    def to_dict(self, base_dir: Path) -> Dict[str, str]:
        return {
            "invalid_part_db": _to_relative(self.invalid_part_db, base_dir),
            "binding_library": _to_relative(self.binding_library, base_dir),
            "important_materials": _to_relative(self.important_materials, base_dir),
            "system_part_db": _to_relative(self.system_part_db, base_dir),
            "blocked_applicants": _to_relative(self.blocked_applicants, base_dir),
            "part_asset_dir": _to_relative(self.part_asset_dir, base_dir),
            "account_store": _to_relative(self.account_store, base_dir),
            "ua_lookup_dir": _to_relative(self.ua_lookup_dir, base_dir)
            if self.ua_lookup_dir
            else "",
            "asset_unc_prefix": self.asset_unc_prefix,
            "asset_local_prefix": self.asset_local_prefix,
        }


def load_config(path: Path) -> AppConfig:
    base_dir = path.parent
    if not path.exists():
        save_config(path, AppConfig.from_dict(DEFAULT_CONFIG, base_dir))

    encodings = ["utf-8", "utf-8-sig", "gbk"]
    raw_text = None
    last_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        try:
            raw_text = path.read_text(encoding=encoding)
            if encoding != encodings[0]:
                logger.warning("配置文件读取回退：%s (encoding=%s)", path, encoding)
            break
        except UnicodeDecodeError as exc:
            last_error = exc
    else:  # pragma: no cover - defensive fallback
        tried = ", ".join(encodings)
        raise RuntimeError(
            f"无法读取配置文件：{path}。已尝试编码：{tried}。请将文件保存为 UTF-8。"
        ) from last_error

    sanitized_text = _sanitize_json_text(raw_text)
    corrected = sanitized_text != raw_text

    try:
        data = json.loads(sanitized_text)
    except JSONDecodeError:
        # If we still cannot load the configuration, fall back to defaults and
        # preserve the original text for manual inspection.
        backup_path = path.with_suffix(path.suffix + ".bak")
        backup_path.write_text(raw_text, encoding="utf-8")
        data = DEFAULT_CONFIG
        corrected = True

    config = AppConfig.from_dict(data, base_dir)
    if corrected:
        save_config(path, config)
    return config


def save_config(path: Path, config: AppConfig, base_dir: Path | None = None) -> None:
    target_dir = path.parent
    target_dir.mkdir(parents=True, exist_ok=True)

    backup_path = path.with_suffix(path.suffix + ".bak")
    if path.exists():
        try:
            shutil.copy2(path, backup_path)
        except Exception:  # noqa: BLE001
            logger.exception("备份配置文件失败：%s", path)

    text = json.dumps(
        config.to_dict(base_dir or target_dir),
        ensure_ascii=False,
        indent=2,
    )
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(text)
        handle.write("\n")
        handle.flush()
        os.fsync(handle.fileno())
    tmp.replace(path)


def _escape_invalid_backslashes(raw_text: str) -> str:
    pattern = r"(?<!\\)\\(?![\\/\"bfnrtu])"
    return re.sub(pattern, r"\\\\", raw_text)


def _sanitize_json_text(raw_text: str) -> str:
    # Strip BOM, normalize newlines, remove comments, repair stray backslashes and
    # trailing commas so config files copied between machines remain loadable.
    text = raw_text.lstrip("\ufeff").replace("\r\n", "\n")
    text = _strip_json_comments(text)
    text = _escape_invalid_backslashes(text)
    return _remove_trailing_commas(text)


def _resolve_path(value: str | None, base_dir: Path) -> Path:
    if not value:
        return base_dir
    p = Path(value)
    if not p.is_absolute():
        p = base_dir / p
    return p


def _resolve_optional_path(value: str | None, base_dir: Path) -> Path | None:
    if not value:
        return None
    return _resolve_path(value, base_dir)


def _to_relative(path: Path, base_dir: Path) -> str:
    try:
        return str(path.relative_to(base_dir))
    except ValueError:
        return str(path)


def _strip_json_comments(text: str) -> str:
    # Remove // line comments that start a line and /* block comments */ while
    # leaving inline URLs untouched.
    text = re.sub(r"(?m)^\s*//.*$", "", text)
    return re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)


def _remove_trailing_commas(text: str) -> str:
    return re.sub(r",(\s*[}\]])", r"\1", text)
