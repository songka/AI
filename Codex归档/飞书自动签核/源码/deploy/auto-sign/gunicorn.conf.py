# -*- coding: utf-8 -*-
"""生产 Gunicorn 配置；容量命令给出的环境变量覆盖保守默认值。"""

import os


bind = os.environ.get("QH_GUNICORN_BIND", "127.0.0.1:7000")
workers = max(1, int(os.environ.get("QH_GUNICORN_WORKERS", "1")))
threads = max(1, int(os.environ.get("QH_GUNICORN_THREADS", "4")))
worker_class = "gthread"
timeout = max(30, int(os.environ.get("QH_GUNICORN_TIMEOUT", "120")))
graceful_timeout = max(15, int(os.environ.get("QH_GUNICORN_GRACEFUL_TIMEOUT", "30")))
keepalive = 5
accesslog = None
errorlog = "-"
loglevel = os.environ.get("QH_GUNICORN_LOG_LEVEL", "error")
capture_output = False
