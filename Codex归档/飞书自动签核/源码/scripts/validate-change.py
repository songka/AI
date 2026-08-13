from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from urllib.parse import urlparse


REQUIRED = {
    "ticket",
    "version",
    "owner",
    "risk",
    "status",
    "approver",
    "approved_at",
    "approval_url",
    "canary_percent",
    "rollback_version",
    "rollback_steps",
    "success_thresholds",
}


def validate(record: dict, expected_version: str) -> list[str]:
    errors = []
    missing = sorted(REQUIRED - set(record))
    if missing:
        errors.append("缺少字段: " + ", ".join(missing))
        return errors
    if str(record["version"]) != expected_version:
        errors.append("变更版本与 APP_VERSION 不一致")
    if str(record["status"]).lower() != "approved":
        errors.append("变更状态必须为 approved")
    if not str(record["owner"]).strip() or str(record["owner"]) == str(record["approver"]):
        errors.append("审批人与变更负责人必须是不同人员")
    if str(record["risk"]).lower() not in ("low", "medium", "high"):
        errors.append("risk 必须为 low、medium 或 high")
    try:
        approved_at = dt.datetime.fromisoformat(str(record["approved_at"]).replace("Z", "+00:00"))
        if not approved_at.tzinfo:
            errors.append("approved_at 必须包含时区")
    except ValueError:
        errors.append("approved_at 必须是 ISO-8601 时间")
    approval_url = urlparse(str(record["approval_url"]))
    if approval_url.scheme != "https" or not approval_url.netloc:
        errors.append("approval_url 必须是 HTTPS 审批记录地址")
    try:
        canary = int(record["canary_percent"])
        if canary < 1 or canary > 50:
            errors.append("canary_percent 必须在 1 到 50 之间")
    except (TypeError, ValueError):
        errors.append("canary_percent 必须是整数")
    if not str(record["rollback_version"]).strip():
        errors.append("必须指定 rollback_version")
    if not isinstance(record["rollback_steps"], list) or not record["rollback_steps"]:
        errors.append("rollback_steps 必须是非空数组")
    thresholds = record["success_thresholds"]
    for key in ("max_failure_rate", "max_p95_ms", "observation_minutes"):
        if not isinstance(thresholds, dict) or key not in thresholds:
            errors.append(f"success_thresholds 缺少 {key}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="验证生产变更审批记录")
    parser.add_argument("record")
    parser.add_argument("--version", required=True)
    args = parser.parse_args()
    path = Path(args.record)
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"FAIL: 无法读取变更审批记录: {exc}")
        return 1
    errors = validate(record, args.version)
    if errors:
        for error in errors:
            print("FAIL:", error)
        return 1
    print(f"PASS: change {record['ticket']} approved for {record['version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
