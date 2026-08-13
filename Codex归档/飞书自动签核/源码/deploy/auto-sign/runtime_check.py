# -*- coding: utf-8 -*-
"""部署运行时预检，不读取配置或凭证。"""

from __future__ import annotations

import ssl
import sys


def main() -> int:
    errors = []
    if sys.version_info < (3, 9):
        errors.append("Python 必须为 3.9 或更高版本")
    try:
        import urllib3
        urllib3_version = urllib3.__version__
    except Exception as exc:
        errors.append(f"urllib3 无法导入: {exc}")
        urllib3_version = "unavailable"
    openssl_version = ssl.OPENSSL_VERSION
    if "OpenSSL 1.0.2" in openssl_version and urllib3_version.startswith("2."):
        errors.append(
            "OpenSSL 1.0.2 必须使用 urllib3<2；请重新安装 requirements.txt"
        )
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"OpenSSL: {openssl_version}")
    print(f"urllib3: {urllib3_version}")
    if errors:
        for error in errors:
            print(f"FAIL: {error}")
        return 1
    print("PASS: runtime dependency compatibility")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
