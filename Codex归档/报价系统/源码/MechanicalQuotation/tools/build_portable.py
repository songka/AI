#!/usr/bin/env python
"""Build the licensed-code-only Windows demonstration package.

The default ``python-runtime`` backend copies the locally installed, PSF-signed
Python runtime. This avoids enterprise endpoint protection quarantining the
unsigned PyInstaller bootloader. PyInstaller remains available for machines
where the generated executable can be signed or allow-listed.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from packaging.requirements import Requirement

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist" / "MechanicalQuotation"
WORK = ROOT / "build" / "portable-pyinstaller"

RUNTIME_DISTRIBUTIONS = (
    "bcrypt",
    "click",
    "cryptography",
    "ezdxf",
    "fastapi",
    "httpx",
    "openpyxl",
    "pydantic",
    "python-multipart",
    "PyYAML",
    "uvicorn",
)


def _copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\r\n" if path.suffix == ".bat" else "\n")


def _batch_files() -> dict[str, str]:
    header = '@echo off\nchcp 65001 >nul\ncd /d "%~dp0"\n'
    ui_launcher = '"%~dp0MechanicalQuotation.exe" -m quotation.launcher'
    console_launcher = '"%~dp0MechanicalQuotationConsole.exe" -m quotation.launcher'
    return {
        "start_ui.bat": header + ui_launcher + " --ui\n",
        "start_api.bat": header + console_launcher + " --api\n",
        "start_all.bat": header
        + 'start "MechanicalQuotation API" /min "%~dp0MechanicalQuotationConsole.exe" '
        + "-m quotation.launcher --api\n"
        + "timeout /t 2 /nobreak >nul\n"
        + ui_launcher
        + " --ui\n",
        "stop_api.bat": header
        + "if not exist runtime\\api.pid (echo API PID file not found.& exit /b 0)\n"
        + "set /p API_PID=<runtime\\api.pid\n"
        + "taskkill /PID %API_PID% /T /F\n",
        "run_self_check.bat": header + console_launcher + " --self-check\npause\n",
        "run_demo_smoke.bat": header + console_launcher + " --smoke\npause\n",
    }


def _clean_dist() -> None:
    resolved_dist = DIST.resolve()
    resolved_root = ROOT.resolve()
    if resolved_dist.parent != resolved_root / "dist":
        raise RuntimeError(f"Refusing to clean unexpected package path: {resolved_dist}")
    if DIST.exists():
        shutil.rmtree(DIST)


def _build_pyinstaller() -> None:
    command = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onedir",
        "--name",
        "MechanicalQuotation",
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(WORK),
        "--specpath",
        str(WORK),
        "--paths",
        str(ROOT / "src"),
        "--hidden-import",
        "quotation.api.main",
        "--hidden-import",
        "quotation.ui.demo_app",
        "--hidden-import",
        "quotation.portable_checks",
        "--collect-all",
        "ezdxf",
        "--collect-all",
        "uvicorn",
        str(ROOT / "src" / "quotation" / "launcher.py"),
    ]
    subprocess.run(command, cwd=ROOT, check=True)


def _sitecustomize() -> str:
    return '''"""Bootstrap the signed-runtime portable application."""
from __future__ import annotations

import os
import sys
from pathlib import Path

_ROOT = Path(sys.executable).resolve().parent
os.chdir(_ROOT)
sys.path.insert(0, str(_ROOT / "app"))

# A direct double-click supplies no arguments. Standard ``-m`` invocations
# used by the batch launchers continue through Python's normal startup path.
if (
    Path(sys.executable).stem.casefold() == "mechanicalquotation"
    and sys.argv == [""]
):
    from quotation.launcher import main

    try:
        main()
    except SystemExit as exc:
        os._exit(exc.code if isinstance(exc.code, int) else 1)
    os._exit(0)
'''


def _runtime_distribution_closure() -> list[importlib.metadata.Distribution]:
    """Resolve installed production dependencies without copying the whole venv."""

    pending = list(RUNTIME_DISTRIBUTIONS)
    resolved: dict[str, importlib.metadata.Distribution] = {}
    while pending:
        requested = pending.pop()
        try:
            distribution = importlib.metadata.distribution(requested)
        except importlib.metadata.PackageNotFoundError as exc:
            raise RuntimeError(f"Missing runtime dependency: {requested}") from exc
        canonical = distribution.metadata["Name"].casefold().replace("_", "-")
        if canonical in resolved:
            continue
        resolved[canonical] = distribution
        for raw_requirement in distribution.requires or ():
            requirement = Requirement(raw_requirement)
            if requirement.marker and not requirement.marker.evaluate({"extra": ""}):
                continue
            pending.append(requirement.name)
    return [resolved[name] for name in sorted(resolved)]


def _copy_runtime_site_packages(source_root: Path, destination_root: Path) -> None:
    copied_files: set[Path] = set()
    for distribution in _runtime_distribution_closure():
        for item in distribution.files or ():
            source = Path(distribution.locate_file(item)).resolve()
            try:
                relative = source.relative_to(source_root.resolve())
            except ValueError:
                continue
            lowered_parts = {part.casefold() for part in relative.parts}
            normalized_relative = relative.as_posix().casefold()
            if (
                "__pycache__" in lowered_parts
                or "test" in lowered_parts
                or "tests" in lowered_parts
                or "_pyinstaller" in lowered_parts
                or source.suffix.casefold() in {".pyc", ".pyo"}
                or source.name.casefold() == "pytest_plugin.py"
                or normalized_relative.endswith("ezdxf/addons/drawing/pymupdf.py")
            ):
                continue
            if not source.is_file() or relative in copied_files:
                continue
            _copy(source, destination_root / relative)
            copied_files.add(relative)


def _build_python_runtime() -> None:
    base = Path(sys.base_prefix)
    pythonw = base / "pythonw.exe"
    python = base / "python.exe"
    if not pythonw.exists():
        raise FileNotFoundError(f"Signed Python runtime not found: {pythonw}")
    if not python.exists():
        raise FileNotFoundError(f"Signed Python console runtime not found: {python}")

    _clean_dist()
    DIST.mkdir(parents=True)
    _copy(pythonw, DIST / "MechanicalQuotation.exe")
    _copy(python, DIST / "MechanicalQuotationConsole.exe")
    for pattern in ("*.dll", "*.pyd", "*.zip"):
        for source in base.glob(pattern):
            _copy(source, DIST / source.name)
    for name in ("DLLs", "Lib", "tcl"):
        source = base / name
        if source.exists():
            ignored = shutil.ignore_patterns(
                "__pycache__", ".pytest_cache", "test", "tests", "*.pyc", "*.pyo"
            )
            if name == "Lib":
                ignored = shutil.ignore_patterns(
                    "site-packages", "__pycache__", ".pytest_cache", "test", "tests",
                    "idlelib", "ensurepip", "*.pyc", "*.pyo",
                )
            shutil.copytree(source, DIST / name, dirs_exist_ok=True, ignore=ignored)

    venv_site_packages = Path(sys.prefix) / "Lib" / "site-packages"
    if not venv_site_packages.is_dir():
        raise FileNotFoundError(f"Virtualenv site-packages not found: {venv_site_packages}")
    _copy_runtime_site_packages(
        venv_site_packages, DIST / "Lib" / "site-packages"
    )
    shutil.copytree(
        ROOT / "src" / "quotation",
        DIST / "app" / "quotation",
        ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "pdf"),
    )
    _write(DIST / "Lib" / "site-packages" / "sitecustomize.py", _sitecustomize())


def build(
    backend: str = "python-runtime",
    skip_pyinstaller: bool = False,
    oda_source: str | Path | None = None,
    deepseek_key_file: str | Path | None = None,
) -> Path:
    # Keep the old keyword for callers that only refresh sidecars around an
    # existing PyInstaller build.
    if skip_pyinstaller:
        backend = "existing"
    package_backend = backend
    if backend == "python-runtime":
        _build_python_runtime()
    elif backend == "pyinstaller":
        _build_pyinstaller()
    elif backend == "existing":
        marker = DIST / "PACKAGE_BACKEND.txt"
        if marker.is_file() and "python-runtime" in marker.read_text(encoding="utf-8"):
            shutil.copytree(
                ROOT / "src" / "quotation",
                DIST / "app" / "quotation",
                dirs_exist_ok=True,
                ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "pdf"),
            )
            _copy(Path(sys.base_prefix) / "python.exe", DIST / "MechanicalQuotationConsole.exe")
            package_backend = "python-runtime"
    else:
        raise ValueError(f"Unsupported backend: {backend}")
    if not (DIST / "MechanicalQuotation.exe").exists():
        raise FileNotFoundError("Portable output is missing MechanicalQuotation.exe")

    optional_pdf_adapter = (
        DIST / "Lib" / "site-packages" / "ezdxf" / "addons" / "drawing" / "pymupdf.py"
    )
    if optional_pdf_adapter.is_file():
        optional_pdf_adapter.unlink()

    _copy(ROOT / "rules" / "quotation-rules.yaml", DIST / "rules" / "quotation-rules.yaml")
    _copy(
        ROOT / "rules" / "imports" / "r01-v1.0" / "pricing-rules-excel-r01-v1.0.json",
        DIST / "rules" / "imports" / "r01-v1.0" / "pricing-rules-excel-r01-v1.0.json",
    )
    pointer = json.loads(
        (ROOT / "data" / "current-version-pointer.json").read_text(encoding="utf-8")
    )
    _copy(
        ROOT / "data" / "current-version-pointer.json",
        DIST / "data" / "current-version-pointer.json",
    )
    _copy(ROOT / "data" / pointer["snapshot_path"], DIST / "data" / pointer["snapshot_path"])
    _copy(
        ROOT / "data" / "feature-price-calibration-gcs-v1.0.json",
        DIST / "data" / "feature-price-calibration-gcs-v1.0.json",
    )
    for document in (
        "external-quotation-skill-protocol-v1.0.yaml",
        "external-skill-folder-v1.0.example.json",
        "EXTERNAL_SKILL_INTEGRATION.md",
        "external-skill-prompt-templates-v1.0.yaml",
        "EXTERNAL_SKILL_TRAINING_GUIDE.md",
        "EXTERNAL_SKILL_GENERATION_PROMPT.md",
    ):
        _copy(ROOT / "docs" / document, DIST / "docs" / document)
    shutil.copytree(
        ROOT / "docs" / "external-skill-agents",
        DIST / "docs" / "external-skill-agents",
        dirs_exist_ok=True,
    )
    _copy(
        ROOT / "docs" / "images" / "current-quotation-flow-with-skill-ai-v3.png",
        DIST / "docs" / "images" / "current-quotation-flow-with-skill-ai-v3.png",
    )
    settings_target = DIST / "config" / "user_settings.json"
    _copy(ROOT / "config" / "user_settings.example.json", settings_target)
    # AuthService loads these RBAC catalogs at login time.  A GUI executable
    # has no console, so omitting them previously looked like a dead button.
    _copy(ROOT / "config" / "roles.yaml", DIST / "config" / "roles.yaml")
    _copy(
        ROOT / "config" / "permissions.yaml",
        DIST / "config" / "permissions.yaml",
    )
    bundled_oda = None
    if oda_source is not None:
        oda_root = Path(oda_source).resolve()
        oda_executable = oda_root / "ODAFileConverter.exe"
        if not oda_executable.is_file():
            raise FileNotFoundError(f"ODA directory is missing ODAFileConverter.exe: {oda_root}")
        bundled_oda = DIST / "third_party" / oda_root.name
        shutil.copytree(
            oda_root,
            bundled_oda,
            dirs_exist_ok=True,
            ignore=shutil.ignore_patterns("*.msi", "*.pdb"),
        )
        settings = json.loads(settings_target.read_text(encoding="utf-8"))
        settings["dwg_converter_path"] = (
            f"../third_party/{bundled_oda.name}/ODAFileConverter.exe"
        )
        settings["dwg_converter_note"] = "交付包内 ODA 转换器；仅限已获第三方授权的内部电脑使用"
        _write(settings_target, json.dumps(settings, ensure_ascii=False, indent=2))

    for directory in (
        DIST / "exports",
        DIST / "runtime" / "data",
        DIST / "runtime" / "reports",
        DIST / "runtime" / "secrets",
        DIST / "runtime" / "tmp",
    ):
        directory.mkdir(parents=True, exist_ok=True)
    secret = DIST / "runtime" / "secrets" / "deepseek_api_key.txt"
    if deepseek_key_file is not None:
        key_source = Path(deepseek_key_file).resolve()
        if not key_source.is_file() or key_source.stat().st_size == 0:
            raise FileNotFoundError("DeepSeek Key 文件不存在或为空")
        _copy(key_source, secret)
    _write(
        DIST / "THIRD_PARTY_NOT_BUNDLED.txt",
        (
            "ODA File Converter 已按交付要求放入 third_party；仅限公司确认已获授权的内部电脑使用。\n"
            if bundled_oda is not None
            else "ODA File Converter 与中望 CAD 均未包含于本套件。\n"
        )
        + "第三方软件版权及授权归原厂所有；请勿向未获授权的对象再分发。\n",
    )
    _write(
        DIST / "交付与启动说明.txt",
        "机械加工报价系统——交付与启动说明\n\n"
        "1. 必须复制或解压整个 MechanicalQuotation 文件夹，不能只复制 EXE。\n"
        "2. 放在 SMB 公共槽时，请双击“快速启动器.bat”；它会按版本复制到本机后启动，首次复制稍慢，之后快速启动。\n"
        "3. 不建议从公共槽直接运行 MechanicalQuotation.exe；若文件夹已完整复制到本机，则可直接双击 EXE。\n"
        "4. 只有外部系统通过 API 对接或调试 Swagger 时才需要双击 start_api.bat；启动后可打开 http://127.0.0.1:8000/docs，默认只允许本机访问。\n"
        "5. DXF 可直接使用；本轻量版不支持 PDF。\n"
        + (
            "6. DWG 转换器已放在 third_party 并自动配置；仅限已获授权的内部电脑使用。\n"
            if bundled_oda is not None
            else "6. DWG 需要接收电脑另行合法安装 ODA File Converter，并在系统设置填写路径。\n"
        )
        +
        "7. SLDDRW、SLDPRT 需要接收电脑安装可用的 SOLIDWORKS。\n"
        + (
            "8. 本交付包已按要求配置 DeepSeek Key；请仅交给获授权人员，并妥善保管。\n"
            if deepseek_key_file is not None
            else "8. 交付包默认不含 DeepSeek Key；请在“系统设置”中从文本文件单独设置。\n"
        )
        +
        "9. 另一台电脑须能访问公司内网 DeepSeek 服务及 SMB 公共槽；Windows 防火墙可允许本程序访问公司网络。\n"
        "10. 外接 Skill 可使用 HTTP、本地或 SMB 文件夹；文件夹内文档由程序内置 DeepSeek 执行，不运行外部程序。\n"
        "11. 首次使用建议运行 run_self_check.bat；若使用 FastAPI且无法启动，请查看窗口错误和 runtime/reports。\n",
    )
    _write(
        DIST / "PACKAGE_BACKEND.txt",
        "Backend: " + package_backend + "\n"
        "The default package uses the locally installed PSF-signed Python runtime.\n",
    )
    _write(
        DIST / "PACKAGE_VERSION.txt",
        "Build ID: " + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "\n",
    )
    _copy(ROOT / "tools" / "portable_fast_launcher.ps1", DIST / "快速启动器.ps1")
    _copy(ROOT / "tools" / "portable_fast_launcher.bat", DIST / "快速启动器.bat")
    for name, content in _batch_files().items():
        _write(DIST / name, content)

    manifest = []
    package_manifest = DIST / "package_manifest.json"
    secret_paths = {
        secret,
        DIST / "runtime" / "secrets" / "user_store_key.txt",
    }
    for path in sorted(p for p in DIST.rglob("*") if p.is_file()):
        if path in secret_paths or path == package_manifest:
            continue
        manifest.append(
            {
                "path": path.relative_to(DIST).as_posix(),
                "size": path.stat().st_size,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
        )
    _write(package_manifest, json.dumps(manifest, ensure_ascii=False, indent=2))
    print(f"Portable package ready: {DIST}")
    return DIST


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend",
        choices=("python-runtime", "pyinstaller", "existing"),
        default="python-runtime",
    )
    parser.add_argument("--skip-pyinstaller", action="store_true")
    parser.add_argument("--oda-source")
    parser.add_argument("--deepseek-key-file")
    args = parser.parse_args()
    build(
        backend=args.backend,
        skip_pyinstaller=args.skip_pyinstaller,
        oda_source=args.oda_source,
        deepseek_key_file=args.deepseek_key_file,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
