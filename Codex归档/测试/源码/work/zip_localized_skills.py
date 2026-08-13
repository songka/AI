from pathlib import Path
import os
import shutil
import zipfile

BASE = Path(r"C:\Users\lfaf-test\Documents\测试\电气工程师agent skill")
PACKAGES = [
    "EE-AI-Toolkit(电气工程师AI工具包)",
    "PLC-Programming(PLC编程开发综合)",
]


def rebuild_package_zip(skill_name: str) -> tuple[Path, int, int]:
    root = BASE / skill_name
    package_dir = root / "package"
    zip_path = root / "package.zip"
    backup_path = root / "package.zip.bak"
    tmp_path = root / "package.localized.zip"

    if zip_path.exists() and not backup_path.exists():
        shutil.copy2(zip_path, backup_path)
    if tmp_path.exists():
        tmp_path.unlink()

    file_count = 0
    with zipfile.ZipFile(tmp_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in sorted(package_dir.rglob("*")):
            if file_path.is_file():
                zf.write(file_path, file_path.relative_to(package_dir).as_posix())
                file_count += 1

    os.replace(tmp_path, zip_path)
    return zip_path, zip_path.stat().st_size, file_count


for name in PACKAGES:
    path, size, count = rebuild_package_zip(name)
    print(f"{path.name}\t{size}\t{count}")
