from __future__ import annotations

import re
import unittest
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[3]
SKILL = ROOT / ".agents" / "skills" / "manage-feishu-signing"
CALLBACK = ROOT / "deploy" / "auto-sign" / "callback_server.py"
REGRESSIONS = ROOT / "deploy" / "auto-sign" / "tests" / "test_regressions.py"


def read(relative: str | Path) -> str:
    path = relative if isinstance(relative, Path) else ROOT / relative
    return path.read_text(encoding="utf-8")


def app_version() -> str:
    match = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', read(CALLBACK), re.MULTILINE)
    if not match:
        raise AssertionError("callback_server.py 未定义 APP_VERSION")
    return match.group(1)


class SkillContractTests(unittest.TestCase):
    def test_required_project_and_skill_files_exist(self):
        required = [
            ROOT / "AGENTS.md",
            ROOT / "scripts" / "validate-project.ps1",
            ROOT / "scripts" / "validate-skill.py",
            ROOT / "build-release.ps1",
            ROOT / "deploy" / "run-server.sh",
            ROOT / "deploy" / "run-scheduler.sh",
            SKILL / "SKILL.md",
            SKILL / "agents" / "openai.yaml",
            SKILL / "references" / "safety-policy.md",
            SKILL / "references" / "rule-schema.md",
            SKILL / "references" / "commands.md",
            SKILL / "scripts" / "smoke-test.py",
        ]
        missing = [str(path.relative_to(ROOT)) for path in required if not path.is_file()]
        self.assertEqual(missing, [], f"缺少门禁文件: {missing}")

    def test_code_and_deployment_document_versions_match(self):
        version = app_version()
        for relative in ("deploy/发布包说明.md", "deploy/说明书.md", "deploy/部署说明.md"):
            versions = set(re.findall(r"2026\.07\.\d+\.\d+", read(relative)))
            self.assertEqual(versions, {version}, f"{relative} 版本未与代码同步")

    def test_skill_trigger_and_sync_matrix_cover_project_domains(self):
        skill = read(SKILL / "SKILL.md")
        agents = read("AGENTS.md")
        frontmatter = re.match(r"^---\n(.*?)\n---", skill, re.DOTALL)
        self.assertIsNotNone(frontmatter)
        metadata = frontmatter.group(1)
        for phrase in (
            "name: manage-feishu-signing",
            "message routing",
            "signing and rejection rules",
            "group-notification policy",
            "per-user statistics",
            "deployment packages",
        ):
            self.assertIn(phrase, metadata)
        for token in (
            "safety-policy.md",
            "rule-schema.md",
            "commands.md",
            "validate-project.ps1",
            "test_regressions.py",
        ):
            self.assertIn(token, agents)

    def test_safety_policy_has_matching_regression_guards(self):
        safety = read(SKILL / "references" / "safety-policy.md")
        regressions = read(REGRESSIONS)
        callback = read(CALLBACK)
        for phrase in (
            "never execute it",
            "模拟、测试、预览、试跑",
            "Always confirm full approve/reject",
            "platform recheck confirms success",
            "Never log passwords",
        ):
            self.assertIn(phrase, safety)
        for test_name in (
            "test_ai_mutations_become_instructions",
            "test_callback_ai_function_has_no_signing_call",
            "test_cli_all_actions_contain_typed_confirmation",
            "test_reported_phrases_are_not_query",
        ):
            self.assertIn(test_name, regressions)
        self.assertIn('"safe_ai_actions": True', callback)

    def test_command_and_menu_contract(self):
        commands = read(SKILL / "references" / "commands.md")
        callback = read(CALLBACK)
        for command in ("查询", "模拟自动签核", "待手动提醒 开", "统计", "组管理", "设置"):
            self.assertIn(command, commands)
        for event_key in ("help", "query_pending", "rules", "groups", "settings", "stats"):
            self.assertRegex(callback, rf'["\']{event_key}["\']')
            self.assertIn(f"`{event_key}`", commands)

    def test_rule_and_notification_contract(self):
        schema = read(SKILL / "references" / "rule-schema.md")
        settings = read("deploy/auto-sign/user_manager.py")
        for token in (
            "auto_reject",
            "auto_approve",
            "user_groups",
            "content_groups",
            "notification_rules",
            "default_group_notify",
        ):
            self.assertIn(token, schema)
        self.assertIn('"default_group_notify": False', settings)
        self.assertIn('"manual_pending_notify_enabled": False', settings)

    def test_release_script_is_hard_gated_and_secret_aware(self):
        release = read("build-release.ps1")
        for token in (
            "validate-project.ps1",
            "IncludeSkill",
            "config.json",
            "feishu.json",
            "users/",
            r"auth\.json",
            r"auth\.enc",
            r"secrets\.enc",
            r"qh\.env",
            r"\.qhb",
            "qh-master",
        ):
            self.assertIn(token, release)
        for token in (
            "ChangeRecord",
            "validate-change.py",
            "release-change-record.json",
            "Production change approval validation failed",
        ):
            self.assertIn(token, release)

    def test_production_kpi_and_release_governance_contract(self):
        commands = read(SKILL / "references" / "commands.md")
        deployment = read("deploy/部署说明.md")
        governance = read("deploy/发布治理与回滚.md")
        stats = read("deploy/auto-sign/stats_store.py")
        for token in (
            "/stats/kpi",
            "kpi_admin_open_ids",
            "automatic handling rate",
            "failure rate",
        ):
            self.assertIn(token, commands)
        for token in (
            "ops capacity",
            "run-server.sh",
            "run-scheduler.sh",
            "/etc/qh/qh.env",
            "SQLite",
            "Change Record",
        ):
            self.assertIn(token, deployment)
        for token in ("灰度发布", "回滚", "success_thresholds", "approved"):
            self.assertIn(token, governance)
        for table in ("work_items", "run_metrics", "request_metrics"):
            self.assertIn(table, stats)

    def test_centos7_openssl_compatibility_is_pinned_and_preflighted(self):
        requirements = read("deploy/auto-sign/requirements.txt")
        deployment = read("deploy/部署说明.md")
        runtime_check = read("deploy/auto-sign/runtime_check.py")
        self.assertIn("urllib3>=1.26.18,<2", requirements)
        self.assertIn('"$PY" auto-sign/runtime_check.py', deployment)
        self.assertIn("OpenSSL 1.0.2", runtime_check)
        self.assertIn("urllib3<2", runtime_check)

    def test_runtime_scripts_share_external_master_key_environment(self):
        server = read("deploy/run-server.sh")
        scheduler = read("deploy/run-scheduler.sh")
        for source in (server, scheduler):
            self.assertIn('ENV_FILE="${QH_ENV_FILE:-/etc/qh/qh.env}"', source)
            self.assertIn('source "$ENV_FILE"', source)
            self.assertIn('${QH_MASTER_KEY_FILE:-}', source)
            self.assertIn("运行环境未配置 QH_MASTER_KEY", source)
        self.assertIn("-m gunicorn", server)
        self.assertIn("flock -n", scheduler)

    def test_change_approval_validator_rejects_self_approval(self):
        validator_path = ROOT / "scripts" / "validate-change.py"
        spec = importlib.util.spec_from_file_location("validate_change", validator_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        record = {
            "ticket": "CHG-1",
            "version": app_version(),
            "owner": "same-person",
            "risk": "medium",
            "status": "approved",
            "approver": "same-person",
            "approved_at": "2026-07-29T16:00:00+08:00",
            "approval_url": "https://change.example.com/CHG-1",
            "canary_percent": 10,
            "rollback_version": "2026.07.29.1600",
            "rollback_steps": ["切回旧版本"],
            "success_thresholds": {
                "max_failure_rate": 1.0,
                "max_p95_ms": 2000,
                "observation_minutes": 30,
            },
        }
        self.assertIn(
            "审批人与变更负责人必须是不同人员",
            module.validate(record, app_version()),
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
