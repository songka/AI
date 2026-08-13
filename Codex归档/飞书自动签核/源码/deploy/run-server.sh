#!/usr/bin/env bash
set -euo pipefail

ROOT="${QH_ROOT:-/www/wwwroot/lfaf.eu.org/qh}"
PYTHON="${QH_PYTHON:-/www/server/python_manager/versions/3.9.7/bin/python3}"
ENV_FILE="${QH_ENV_FILE:-/etc/qh/qh.env}"

if [[ -r "$ENV_FILE" ]]; then
    # shellcheck source=/dev/null
    source "$ENV_FILE"
elif [[ -z "${QH_MASTER_KEY:-}" && -z "${QH_MASTER_KEY_FILE:-}" ]]; then
    echo "[错误] 未找到运行环境文件且未注入主密钥: $ENV_FILE" >&2
    exit 1
fi

if [[ -z "${QH_MASTER_KEY:-}" && -z "${QH_MASTER_KEY_FILE:-}" ]]; then
    echo "[错误] 运行环境未配置 QH_MASTER_KEY 或 QH_MASTER_KEY_FILE" >&2
    exit 1
fi

cd "$ROOT"
exec "$PYTHON" -m gunicorn \
    -c auto-sign/gunicorn.conf.py \
    --chdir auto-sign \
    callback_server:app
