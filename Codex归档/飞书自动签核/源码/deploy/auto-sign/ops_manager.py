# -*- coding: utf-8 -*-
"""基于真实运行指标生成容量建议；不会直接修改生产服务。"""

from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path

from stats_store import load_profile, production_kpis


def capacity_recommendation(
    db_path: Path, days: int, cpu_count: int, memory_mb: int
) -> dict:
    profile = load_profile(db_path, days)
    kpis = production_kpis(db_path, days)
    result = {"profile": profile, "kpis": kpis, "recommendation": None}
    if not profile["has_real_load"]:
        result["reason"] = "尚无真实请求或计划任务样本；至少采集 7 天后再调整容量"
        return result

    peak_rpm = profile["peak_requests_per_minute"]
    p95_seconds = max(profile["request_p95_ms"], 50) / 1000
    estimated_concurrency = peak_rpm * p95_seconds / 60
    target_threads = max(2, math.ceil(estimated_concurrency * 2))
    threads_per_worker = 4
    cpu_cap = max(1, cpu_count * 2 + 1)
    memory_cap = max(1, memory_mb // 180)
    workers = max(
        1, min(cpu_cap, memory_cap, math.ceil(target_threads / threads_per_worker))
    )

    peak_runs = profile["peak_runs_per_minute"]
    batch_seconds = peak_runs * profile["run_p95_ms"] / 1000
    scheduler_minutes = max(1, math.ceil(batch_seconds / 45)) if batch_seconds else 1
    db_size = db_path.stat().st_size if db_path.exists() else 0
    daily_metric_writes = (
        profile["request_count"] + profile["run_count"]
    ) / max(1, days)
    database = (
        "postgresql"
        if db_size >= 512 * 1024 * 1024 or daily_metric_writes >= 50000
        else "sqlite-wal"
    )
    result["recommendation"] = {
        "gunicorn_workers": workers,
        "gunicorn_threads": threads_per_worker,
        "scheduler_interval_minutes": scheduler_minutes,
        "scheduler_lock": "flock -n /run/qh-auto-sign.lock",
        "database": database,
        "database_size_bytes": db_size,
        "evidence": {
            "peak_requests_per_minute": peak_rpm,
            "request_p95_ms": profile["request_p95_ms"],
            "peak_runs_per_minute": peak_runs,
            "run_p95_ms": profile["run_p95_ms"],
            "estimated_concurrency": round(estimated_concurrency, 3),
            "daily_metric_writes": round(daily_metric_writes, 1),
        },
    }
    return result


def cmd_capacity(args) -> int:
    result = capacity_recommendation(
        Path(args.db),
        max(1, int(args.days)),
        max(1, int(args.cpu)),
        max(256, int(args.memory_mb)),
    )
    content = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content + "\n", encoding="utf-8")
        print(f"容量建议已写入: {output}")
    else:
        print(content)
    return 0 if result["recommendation"] else 2


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="qh ops", description="生产 KPI 与容量评估")
    sub = parser.add_subparsers(dest="command", required=True)
    capacity = sub.add_parser("capacity", help="根据真实负载生成容量建议")
    capacity.add_argument("--db", default=str(Path("data") / "stats.db"))
    capacity.add_argument("--days", type=int, default=7)
    capacity.add_argument("--cpu", type=int, default=os.cpu_count() or 1)
    capacity.add_argument("--memory-mb", type=int, default=2048)
    capacity.add_argument("--output")
    capacity.set_defaults(func=cmd_capacity)
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    raise SystemExit(main())
