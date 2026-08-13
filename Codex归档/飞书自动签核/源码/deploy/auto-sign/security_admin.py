# -*- coding: utf-8 -*-
"""安全管理 CLI：密钥迁移、加密备份、恢复演练和离职账号清理。"""

from __future__ import annotations

import argparse
import getpass
import hashlib
import io
import json
import os
import shutil
import sqlite3
import tempfile
import zipfile
from contextlib import closing
from pathlib import Path, PurePosixPath

from secure_store import (
    SecureStoreError,
    generate_master_key,
    get_master_key,
    migrate_config_secrets,
    read_encrypted_json,
    write_encrypted_json,
)


MAGIC = b"QHBACKUP1"
BACKUP_PASSPHRASE_ENV = "QH_BACKUP_PASSPHRASE"
DEFAULT_ROOT = Path(__file__).resolve().parent.parent


def _backup_crypto():
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    except ImportError as exc:
        raise SecureStoreError(
            "缺少 cryptography 依赖；请先安装 auto-sign/requirements.txt"
        ) from exc
    return AESGCM, Scrypt


def _passphrase(confirm: bool = False) -> str:
    value = os.environ.get(BACKUP_PASSPHRASE_ENV, "")
    if not value:
        value = getpass.getpass("备份口令: ")
        if confirm and value != getpass.getpass("再次输入备份口令: "):
            raise SecureStoreError("两次输入的备份口令不一致")
    if len(value) < 12:
        raise SecureStoreError("备份口令至少 12 个字符")
    return value


def _derive_backup_key(passphrase: str, salt: bytes) -> bytes:
    _, Scrypt = _backup_crypto()
    return Scrypt(salt=salt, length=32, n=2**15, r=8, p=1).derive(
        passphrase.encode("utf-8")
    )


def _encrypt_backup(plaintext: bytes, passphrase: str) -> bytes:
    AESGCM, _ = _backup_crypto()
    salt = os.urandom(16)
    nonce = os.urandom(12)
    ciphertext = AESGCM(_derive_backup_key(passphrase, salt)).encrypt(
        nonce, plaintext, MAGIC
    )
    return MAGIC + salt + nonce + ciphertext


def _decrypt_backup(content: bytes, passphrase: str) -> bytes:
    AESGCM, _ = _backup_crypto()
    if not content.startswith(MAGIC) or len(content) < len(MAGIC) + 29:
        raise SecureStoreError("不是受支持的 QH 加密备份")
    offset = len(MAGIC)
    salt, nonce, ciphertext = content[offset:offset + 16], content[offset + 16:offset + 28], content[offset + 28:]
    try:
        return AESGCM(_derive_backup_key(passphrase, salt)).decrypt(
            nonce, ciphertext, MAGIC
        )
    except Exception as exc:
        raise SecureStoreError("备份认证失败：口令错误或文件已损坏") from exc


def _manifest_for(files: dict[str, bytes], purpose: str) -> dict:
    return {
        "format": 1,
        "purpose": purpose,
        "files": {
            name: {"sha256": hashlib.sha256(content).hexdigest(), "size": len(content)}
            for name, content in sorted(files.items())
        },
    }


def _make_archive(files: dict[str, bytes], purpose: str) -> bytes:
    manifest = _manifest_for(files, purpose)
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        for name, content in sorted(files.items()):
            archive.writestr(name, content)
    return output.getvalue()


def _verify_archive(content: bytes) -> tuple[dict, dict[str, bytes]]:
    try:
        with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
            names = archive.namelist()
            for name in names:
                path = PurePosixPath(name)
                if path.is_absolute() or ".." in path.parts:
                    raise SecureStoreError(f"备份包含不安全路径: {name}")
            manifest = json.loads(archive.read("manifest.json").decode("utf-8"))
            files = {
                name: archive.read(name)
                for name in names
                if name != "manifest.json"
            }
    except (KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        raise SecureStoreError("备份内部结构无效") from exc
    expected = manifest.get("files", {})
    if set(files) != set(expected):
        raise SecureStoreError("备份清单与文件集合不一致")
    for name, content in files.items():
        item = expected[name]
        if len(content) != item.get("size") or hashlib.sha256(content).hexdigest() != item.get("sha256"):
            raise SecureStoreError(f"备份文件校验失败: {name}")
    return manifest, files


def _write_private(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise SecureStoreError(f"拒绝覆盖已有文件: {path}")
    path.write_bytes(content)
    if os.name != "nt":
        path.chmod(0o600)


def _runtime_files(root: Path) -> dict[str, bytes]:
    files: dict[str, bytes] = {}
    for relative in ("config.json", "feishu.json", "secrets.enc", "auth.enc", "sign_events.json"):
        path = root / relative
        if path.is_file():
            files[relative] = path.read_bytes()
    for folder in ("users", "data"):
        base = root / folder
        if base.is_dir():
            for path in base.rglob("*"):
                if path.is_file() and "__pycache__" not in path.parts and path.suffix not in (".log", ".pyc"):
                    files[path.relative_to(root).as_posix()] = path.read_bytes()
    if not files:
        raise SecureStoreError(f"未找到可备份的运行数据: {root}")
    return files


def create_backup(root: Path, output: Path, purpose: str = "full") -> dict:
    files = _runtime_files(root)
    encrypted = _encrypt_backup(_make_archive(files, purpose), _passphrase(confirm=True))
    _write_private(output, encrypted)
    return _manifest_for(files, purpose)


def restore_drill(backup: Path) -> dict:
    plaintext = _decrypt_backup(backup.read_bytes(), _passphrase())
    manifest, files = _verify_archive(plaintext)
    with tempfile.TemporaryDirectory(
        prefix="qh-restore-drill-", dir=str(backup.resolve().parent)
    ) as temp:
        target = Path(temp)
        for name, content in files.items():
            path = target / PurePosixPath(name)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        for name, item in manifest["files"].items():
            restored = (target / PurePosixPath(name)).read_bytes()
            if hashlib.sha256(restored).hexdigest() != item["sha256"]:
                raise SecureStoreError(f"恢复演练复核失败: {name}")
    return manifest


def restore_to_staging(backup: Path, target: Path, confirmation: str) -> dict:
    resolved = target.resolve()
    if confirmation != str(resolved):
        raise SecureStoreError("--confirm-target 必须与恢复目录的绝对路径完全一致")
    if resolved.exists() and any(resolved.iterdir()):
        raise SecureStoreError("恢复目录必须不存在或为空，禁止覆盖生产数据")
    plaintext = _decrypt_backup(backup.read_bytes(), _passphrase())
    manifest, files = _verify_archive(plaintext)
    resolved.mkdir(parents=True, exist_ok=True)
    for name, content in files.items():
        path = resolved / PurePosixPath(name)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
    return manifest


def _valid_open_id(value: str) -> str:
    value = str(value or "").strip()
    if not value or value in (".", "..") or any(char in value for char in ("/", "\\", "\0")):
        raise SecureStoreError("open_id 无效")
    return value


def _offboarding_files(root: Path, open_id: str) -> dict[str, bytes]:
    user_dir = root / "users" / open_id
    if not user_dir.is_dir():
        raise SecureStoreError(f"用户目录不存在: {open_id}")
    files = {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in user_dir.rglob("*") if path.is_file()
    }
    db_path = root / "data" / "stats.db"
    if db_path.exists():
        with closing(sqlite3.connect(str(db_path))) as conn:
            conn.row_factory = sqlite3.Row
            rows = [dict(row) for row in conn.execute(
                "SELECT * FROM sign_actions WHERE open_id = ? ORDER BY id", (open_id,)
            ).fetchall()]
        files[f"offboarding/{open_id}/stats.json"] = json.dumps(
            rows, ensure_ascii=False, indent=2
        ).encode("utf-8")
    return files


def offboard(root: Path, open_id: str, output: Path, confirmation: str) -> int:
    open_id = _valid_open_id(open_id)
    if confirmation != open_id:
        raise SecureStoreError("--confirm-open-id 必须与待清理 open_id 完全一致")
    files = _offboarding_files(root, open_id)
    user_dir = (root / "users" / open_id).resolve()
    output = output.resolve()
    if output == user_dir or user_dir in output.parents:
        raise SecureStoreError("离职留档必须放在待删除用户目录之外")
    encrypted = _encrypt_backup(
        _make_archive(files, f"offboarding:{open_id}"), _passphrase(confirm=True)
    )
    _write_private(output, encrypted)

    user_root = (root / "users").resolve()
    user_dir = (user_root / open_id).resolve()
    if user_dir.parent != user_root:
        raise SecureStoreError("离职清理路径越界")
    shutil.rmtree(user_dir)

    deleted = 0
    db_path = root / "data" / "stats.db"
    if db_path.exists():
        with closing(sqlite3.connect(str(db_path))) as conn, conn:
            deleted = conn.execute(
                "DELETE FROM sign_actions WHERE open_id = ?", (open_id,)
            ).rowcount

    users_root = root / "users"
    if users_root.exists():
        for settings_path in users_root.glob("*/settings.json"):
            try:
                settings = json.loads(settings_path.read_text(encoding="utf-8"))
                wait_for = settings.get("wait_for") or {}
                users = wait_for.get("users") if isinstance(wait_for, dict) else None
                if isinstance(users, list):
                    remaining = [item for item in users if item.get("open_id") != open_id]
                    if len(remaining) != len(users):
                        settings["wait_for"] = (
                            {"users": remaining, "mode": "ANY"} if remaining else None
                        )
                        settings_path.write_text(
                            json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
                            encoding="utf-8",
                        )
            except (OSError, json.JSONDecodeError, AttributeError):
                continue
    return deleted


def cmd_init_key(args) -> int:
    path = Path(args.output).resolve()
    _write_private(path, (generate_master_key() + "\n").encode("ascii"))
    print(f"主密钥文件已创建: {path}")
    print(f"请设置 QH_MASTER_KEY_FILE={path}，并将该文件放入独立密钥托管/灾备流程。")
    return 0


def cmd_migrate(args) -> int:
    get_master_key()
    root = Path(args.root).resolve()
    migrated_fields = migrate_config_secrets(root / "feishu.json")
    migrated_users = 0
    for legacy in (root / "users").glob("*/auth.json"):
        data = json.loads(legacy.read_text(encoding="utf-8-sig"))
        write_encrypted_json(legacy.with_name("auth.enc"), data)
        legacy.unlink()
        migrated_users += 1
    legacy_global = root / "auth.json"
    if legacy_global.exists():
        data = json.loads(legacy_global.read_text(encoding="utf-8-sig"))
        write_encrypted_json(root / "auth.enc", data)
        legacy_global.unlink()
    print(f"迁移完成：系统密钥字段 {len(migrated_fields)} 个，用户凭证 {migrated_users} 份。")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qh security", description="凭证、密钥、备份与离职清理")
    sub = parser.add_subparsers(dest="command", required=True)
    init_key = sub.add_parser("init-key", help="生成权限受限的主密钥文件")
    init_key.add_argument("--output", required=True)
    init_key.set_defaults(func=cmd_init_key)
    migrate = sub.add_parser("migrate", help="迁移明文系统密钥和用户凭证")
    migrate.add_argument("--root", default=str(DEFAULT_ROOT))
    migrate.set_defaults(func=cmd_migrate)
    backup = sub.add_parser("backup", help="创建带认证的 AES-256-GCM 加密备份")
    backup.add_argument("--root", default=str(DEFAULT_ROOT))
    backup.add_argument("--output", required=True)
    backup.set_defaults(func=lambda a: (create_backup(Path(a.root).resolve(), Path(a.output).resolve()), print("加密备份已创建并生成完整性清单。"))[1] or 0)
    drill = sub.add_parser("restore-drill", help="在临时目录解密、恢复并逐文件复核")
    drill.add_argument("--backup", required=True)
    drill.set_defaults(func=lambda a: (restore_drill(Path(a.backup).resolve()), print("恢复演练通过：认证、清单与逐文件哈希均有效。"))[1] or 0)
    restore = sub.add_parser("restore", help="仅恢复到空的演练/暂存目录")
    restore.add_argument("--backup", required=True)
    restore.add_argument("--target", required=True)
    restore.add_argument("--confirm-target", required=True)
    restore.set_defaults(func=lambda a: (restore_to_staging(Path(a.backup).resolve(), Path(a.target), a.confirm_target), print("已恢复到空暂存目录；未覆盖生产数据。"))[1] or 0)
    depart = sub.add_parser("offboard", help="先加密留档，再清除离职账号及其统计")
    depart.add_argument("--root", default=str(DEFAULT_ROOT))
    depart.add_argument("--open-id", required=True)
    depart.add_argument("--backup", required=True)
    depart.add_argument("--confirm-open-id", required=True)
    depart.set_defaults(func=lambda a: (print(f"离职清理完成；删除统计 {offboard(Path(a.root).resolve(), a.open_id, Path(a.backup).resolve(), a.confirm_open_id)} 条。"), 0)[1])
    return parser


def main(argv=None) -> int:
    try:
        args = build_parser().parse_args(argv)
        return int(args.func(args) or 0)
    except (SecureStoreError, OSError, json.JSONDecodeError, sqlite3.Error) as exc:
        print(f"[安全管理失败] {exc}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
