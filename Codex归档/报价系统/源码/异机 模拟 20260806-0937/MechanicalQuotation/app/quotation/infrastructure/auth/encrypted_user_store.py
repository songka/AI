"""AES-GCM encrypted user store suitable for an SMB document slot."""

from __future__ import annotations

import base64
import json
import os
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from quotation.domain.user import User


class EncryptedUserStore:
    """Encrypt the complete user array; no username or hash appears in clear text."""

    FORMAT = "MECHANICAL_QUOTATION_USERS_AESGCM_V1"

    def __init__(self, path: str | Path, encryption_key: str) -> None:
        if len(encryption_key) < 16:
            raise ValueError("用户资料加密密钥至少需要 16 个字符")
        self.path = Path(path)
        self._passphrase = encryption_key.encode("utf-8")

    def load(self) -> list[User]:
        if not self.path.is_file():
            return []
        try:
            envelope = json.loads(self.path.read_text(encoding="utf-8"))
            if envelope.get("format") != self.FORMAT:
                raise ValueError("用户资料格式不受支持")
            salt = base64.b64decode(envelope["salt"])
            nonce = base64.b64decode(envelope["nonce"])
            ciphertext = base64.b64decode(envelope["ciphertext"])
            plaintext = AESGCM(self._derive_key(salt)).decrypt(
                nonce, ciphertext, self.FORMAT.encode("ascii")
            )
            payload = json.loads(plaintext.decode("utf-8"))
            return [User.from_dict(item) for item in payload["users"]]
        except InvalidTag as exc:
            raise ValueError("用户资料解密失败：密钥错误或文件已被修改") from exc
        except (KeyError, TypeError, json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise ValueError("用户资料解密失败：文件格式损坏") from exc

    def save(self, users: list[User]) -> Path:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        salt = os.urandom(16)
        nonce = os.urandom(12)
        plaintext = json.dumps(
            {"users": [user.to_dict() for user in users]},
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        ciphertext = AESGCM(self._derive_key(salt)).encrypt(
            nonce, plaintext, self.FORMAT.encode("ascii")
        )
        envelope = {
            "format": self.FORMAT,
            "salt": base64.b64encode(salt).decode("ascii"),
            "nonce": base64.b64encode(nonce).decode("ascii"),
            "ciphertext": base64.b64encode(ciphertext).decode("ascii"),
        }
        temporary = self.path.with_name(f".{self.path.name}.tmp")
        temporary.write_text(
            json.dumps(envelope, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        temporary.replace(self.path)
        return self.path

    def _derive_key(self, salt: bytes) -> bytes:
        return PBKDF2HMAC(
            algorithm=hashes.SHA256(), length=32, salt=salt, iterations=300_000
        ).derive(self._passphrase)
