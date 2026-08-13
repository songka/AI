# -*- coding: utf-8 -*-
"""签核工具箱统一 CLI 入口。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


BASE = Path(__file__).resolve().parent

SIGN_HELP = """usage: qh sign [全局选项] 命令 [参数]

签核命令:
  login                         登录验证
  list                          查看待签列表
  show 编号                     查看单项详情
  approve 编号...               签核指定项目
  reject 编号...                拒签指定项目
  approve-all                   全部签核（始终二次确认）
  reject-all                    全部拒签（始终二次确认）
  fetch [--dry-run]             生成或预览 Excel 决策文件
  process [--dry-run]           读取 Excel 并执行
  run                           fetch → 编辑 → process

全局选项: --config 文件、--dry-run
"""

FEISHU_HELP = """usage: qh feishu 命令 [参数]

飞书命令:
  serve [--host HOST] [--port PORT]  启动回调与统计网页
  send                               执行多用户定时签核与通知
  test                               测试飞书连接
  setup                              生成配置模板
  lookup --email/--mobile/--chats    查询用户或群 ID
  ai-setup                           配置 OpenAI 兼容 AI
"""

SECURITY_HELP = """usage: qh security 命令 [参数]

安全管理:
  init-key       生成权限受限的主密钥文件
  migrate        把明文系统密钥和用户凭证迁移为密文
  backup         创建 AES-256-GCM 加密备份
  restore-drill  在临时目录完成恢复演练与逐文件校验
  restore        仅恢复到空的暂存目录
  offboard       先加密留档，再清理离职账号及其统计
"""

OPS_HELP = """usage: qh ops 命令 [参数]

生产运维:
  capacity  根据最近真实请求、计划任务 P95 和数据库规模生成容量建议
"""


def _delegate(script: str, args) -> int:
    return subprocess.call([sys.executable, str(BASE / script)] + list(args))


def build_parser():
    parser = argparse.ArgumentParser(
        prog="qh",
        description="飞书签核工具箱统一命令行",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "常用命令:\n"
            "  qh sign --help           查看签核命令\n"
            "  qh feishu --help         查看飞书命令\n"
            "  qh feishu serve          启动回调与统计网页\n"
            "  qh web serve             单独启动统计网页入口"
        ),
    )
    parser.add_argument("group", nargs="?", choices=["sign", "feishu", "web", "security", "ops"])
    return parser


def _serve(argv, default_host: str) -> int:
    parser = argparse.ArgumentParser(prog="qh serve", description="启动飞书回调与个人统计网页")
    parser.add_argument("--host", default=default_host)
    parser.add_argument("--port", default=7000, type=int)
    args = parser.parse_args(argv)
    from callback_server import app
    app.run(host=args.host, port=args.port, debug=False)
    return 0


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv:
        build_parser().print_help()
        return 1
    if argv[0] == "sign":
        if not argv[1:] or any(value in ("-h", "--help") for value in argv[1:]):
            print(SIGN_HELP)
            return 0
        return _delegate("cli.py", argv[1:])
    if argv[0] == "feishu":
        if not argv[1:] or any(value in ("-h", "--help") for value in argv[1:]):
            print(FEISHU_HELP)
            return 0
        if len(argv) >= 2 and argv[1] == "serve":
            return _serve(argv[2:], "0.0.0.0")
        return _delegate("cli_feishu.py", argv[1:])
    if argv[0] == "web" and len(argv) >= 2 and argv[1] == "serve":
        return _serve(argv[2:], "127.0.0.1")
    if argv[0] == "security":
        if not argv[1:] or any(value in ("-h", "--help") for value in argv[1:]):
            print(SECURITY_HELP)
            return 0
        return _delegate("security_admin.py", argv[1:])
    if argv[0] == "ops":
        if not argv[1:] or any(value in ("-h", "--help") for value in argv[1:]):
            print(OPS_HELP)
            return 0
        return _delegate("ops_manager.py", argv[1:])
    build_parser().parse_args(argv[:1])
    build_parser().print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
