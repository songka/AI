from __future__ import annotations

import py_compile
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "app.py"


FRAMEWORK_TOKENS = [
    "UI_AUTOMATION_STEPS",
    "build_panel_title",
    "build_path_panel",
    "build_text_editor_panel",
    "build_action_bar",
    "build_status_badge",
    "set_status_badge_tone",
]


CLASS_CHECKS = {
    "Application": ["build_status_badge", "set_status_badge_tone", "_build_page_header"],
    "DataFileEditor": ["build_dialog_header", "build_panel_title", "build_action_bar"],
    "SystemPartViewer": ["build_path_panel", "build_panel_title"],
    "InvalidPartEditor": ["build_path_panel", "build_panel_title", "build_action_bar"],
    "LoginDialog": ["build_dialog_header", "build_action_bar"],
    "AdminSettingsDialog": ["build_dialog_header", "build_panel_title"],
    "BlockedApplicantEditor": [
        "build_path_panel",
        "build_text_editor_panel",
        "build_action_bar",
    ],
    "BindingEditor": ["build_panel_title", "build_action_bar", "refresh_on_open"],
    "PartAssetManager": ["build_panel_title", "build_action_bar", "refresh_on_open"],
    "ImportantMaterialEditor": [
        "build_path_panel",
        "build_text_editor_panel",
        "build_action_bar",
    ],
}


COMPILE_TARGETS = [
    ROOT / "app.py",
    ROOT / "app_web.py",
    ROOT / "bomcheck_app" / "part_assets.py",
    ROOT / "bomcheck_app" / "binding_library.py",
]


def class_block(source: str, class_name: str) -> str:
    matches = list(re.finditer(r"^class\s+(\w+)", source, re.MULTILINE))
    for index, match in enumerate(matches):
        if match.group(1) != class_name:
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(source)
        return source[match.start() : end]
    return ""


def main() -> int:
    source = APP.read_text(encoding="utf-8")
    missing: list[str] = []

    for token in FRAMEWORK_TOKENS:
        if token not in source:
            missing.append(f"framework token missing: {token}")

    for class_name, tokens in CLASS_CHECKS.items():
        block = class_block(source, class_name)
        if not block:
            missing.append(f"class missing: {class_name}")
            continue
        for token in tokens:
            if token not in block:
                missing.append(f"{class_name} missing: {token}")

    for path in COMPILE_TARGETS:
        py_compile.compile(str(path), doraise=True)

    if missing:
        for item in missing:
            print(f"FAIL {item}")
        return 1

    print("OK ui automation framework checks passed")
    print(f"OK compiled {len(COMPILE_TARGETS)} targets")
    return 0


if __name__ == "__main__":
    sys.exit(main())
