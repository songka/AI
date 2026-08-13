import importlib.util
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
DIST = ROOT / "dist" / "MechanicalQuotation"


def _build_module():
    spec = importlib.util.spec_from_file_location(
        "build_portable", ROOT / "tools" / "build_portable.py"
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_batch_launchers_use_signed_runtime_module_entrypoint_and_pid_stop():
    batch = _build_module()._batch_files()

    assert 'MechanicalQuotation.exe\" -m quotation.launcher --ui' in batch["start_ui.bat"]
    assert 'MechanicalQuotationConsole.exe\" -m quotation.launcher --api' in batch["start_api.bat"]
    assert "runtime\\api.pid" in batch["stop_api.bat"]
    assert "taskkill /PID %API_PID% /T /F" in batch["stop_api.bat"]


def test_signed_runtime_bootstrap_only_intercepts_direct_double_click():
    bootstrap = _build_module()._sitecustomize()

    assert 'sys.argv == [""]' in bootstrap
    assert 'sys.path.insert(0, str(_ROOT / "app"))' in bootstrap
    assert "from quotation.launcher import main" in bootstrap


def test_lightweight_package_uses_only_runtime_distribution_closure():
    module = _build_module()

    assert "rapidocr" not in {name.casefold() for name in module.RUNTIME_DISTRIBUTIONS}
    assert "onnxruntime" not in {name.casefold() for name in module.RUNTIME_DISTRIBUTIONS}
    assert "pymupdf" not in {name.casefold() for name in module.RUNTIME_DISTRIBUTIONS}
    assert "pytest" not in {name.casefold() for name in module.RUNTIME_DISTRIBUTIONS}


def test_config_template_contains_no_secret_and_uses_external_converter():
    config = json.loads(
        (ROOT / "config" / "user_settings.example.json").read_text(encoding="utf-8")
    )

    assert config["dwg_converter_path"] == ""
    assert "key" not in " ".join(config).casefold()


@pytest.mark.skipif(
    not (DIST / "MechanicalQuotation.exe").exists(),
    reason="portable package not built",
)
def test_built_package_layout_reports_and_requested_bundled_dependencies():
    if not (DIST / "docs" / "external-skill-agents" / "00_PART_CLASSIFICATION.md").exists():
        pytest.skip("现有便携包早于前置分类 Skill；本次按要求未重新打包")
    required = [
        "MechanicalQuotation.exe",
        "MechanicalQuotationConsole.exe",
        "start_ui.bat",
        "start_api.bat",
        "start_all.bat",
        "stop_api.bat",
        "交付与启动说明.txt",
        "快速启动器.bat",
        "快速启动器.ps1",
        "PACKAGE_VERSION.txt",
        "config/user_settings.json",
        "config/roles.yaml",
        "config/permissions.yaml",
        "exports",
        "data/current-version-pointer.json",
        "data/feature-price-calibration-gcs-v1.0.json",
        "docs/external-quotation-skill-protocol-v1.0.yaml",
        "docs/external-skill-folder-v1.0.example.json",
        "docs/EXTERNAL_SKILL_INTEGRATION.md",
        "docs/external-skill-prompt-templates-v1.0.yaml",
        "docs/EXTERNAL_SKILL_TRAINING_GUIDE.md",
        "docs/EXTERNAL_SKILL_GENERATION_PROMPT.md",
        "docs/images/current-quotation-flow-with-skill-ai-v3.png",
    ]
    for relative in required:
        assert (DIST / relative).exists(), relative
    agent_guides = list((DIST / "docs" / "external-skill-agents").glob("*.md"))
    assert len(agent_guides) == 11

    startup_guide = (DIST / "交付与启动说明.txt").read_text(encoding="utf-8")
    assert "快速启动器.bat" in startup_guide
    assert "不建议从公共槽直接运行" in startup_guide
    assert "只有外部系统通过 API 对接" in startup_guide

    secret = DIST / "runtime" / "secrets" / "deepseek_api_key.txt"
    assert not secret.exists()
    assert not (DIST / "runtime" / "secrets" / "user_store_key.txt").exists()
    # ODA is a separately licensed optional dependency; a clean handoff may
    # omit it and let each authorized workstation configure its own copy.
    assert not list(DIST.rglob("ZWCAD.EXE"))
    assert not list(DIST.rglob("pymupdf.py"))
    manifest = (DIST / "package_manifest.json").read_text(encoding="utf-8")
    assert "deepseek_api_key.txt" not in manifest
    self_check = json.loads(
        (DIST / "runtime" / "reports" / "portable_self_check.json").read_text(encoding="utf-8")
    )
    smoke = json.loads(
        (DIST / "runtime" / "reports" / "portable_demo_smoke.json").read_text(encoding="utf-8")
    )
    assert self_check["summary"]["failed"] == 0
    assert smoke["summary"]["failed"] == 0
