import copy
import contextlib
import importlib.util
import io
import json
import shutil
import unittest
from unittest import mock
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "tools" / "ai_assets.py"
SPEC = importlib.util.spec_from_file_location("ai_assets", MODULE_PATH)
ai_assets = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
SPEC.loader.exec_module(ai_assets)

HUB_PATH = Path(__file__).resolve().parents[1] / "tools" / "asset_hub.py"
HUB_SPEC = importlib.util.spec_from_file_location("asset_hub", HUB_PATH)
asset_hub = importlib.util.module_from_spec(HUB_SPEC)
assert HUB_SPEC.loader
import sys
sys.modules["ai_assets"] = ai_assets
HUB_SPEC.loader.exec_module(asset_hub)

SKILL_PATH = Path(__file__).resolve().parents[1] / "skills" / "ai-assets-manager" / "scripts" / "ai_assets_skill.py"
SKILL_SPEC = importlib.util.spec_from_file_location("ai_assets_skill", SKILL_PATH)
ai_assets_skill = importlib.util.module_from_spec(SKILL_SPEC)
assert SKILL_SPEC.loader
SKILL_SPEC.loader.exec_module(ai_assets_skill)


class VersionTests(unittest.TestCase):
    def test_constraints(self):
        self.assertTrue(ai_assets.satisfies("1.4.2", "^1.3.0"))
        self.assertFalse(ai_assets.satisfies("2.0.0", "^1.3.0"))
        self.assertTrue(ai_assets.satisfies("1.3.9", "~1.3.0"))
        self.assertTrue(ai_assets.satisfies("1.5.0", ">=1.3.0 <2.0.0"))


class CatalogTests(unittest.TestCase):
    def setUp(self):
        self.data = ai_assets.load_catalog()

    def test_example_is_valid(self):
        self.assertEqual([], ai_assets.validation_errors(self.data))

    def test_missing_dependency_is_reported(self):
        changed = copy.deepcopy(self.data)
        ai_assets.asset_map(changed)["skill/code-review"]["dependencies"][0]["id"] = "cli/missing"
        errors = ai_assets.validation_errors(changed)
        self.assertTrue(any("缺少必需依赖" in item for item in errors))

    def test_dependency_order_places_cli_first(self):
        order = ai_assets.dependency_order(self.data)
        self.assertLess(order.index("cli/codex"), order.index("skill/code-review"))

    def test_agent_asset_id_is_supported(self):
        self.assertIsNotNone(ai_assets.ASSET_ID.fullmatch("agent/plc-helper"))

    def test_cycle_is_reported(self):
        changed = copy.deepcopy(self.data)
        ai_assets.asset_map(changed)["cli/codex"]["dependencies"].append(
            {"id": "skill/release-note", "version": "^2.0.0", "required": True}
        )
        errors = ai_assets.validation_errors(changed)
        self.assertTrue(any("循环依赖" in item for item in errors))


class HubTests(unittest.TestCase):
    def setUp(self):
        self.registry = asset_hub.read_json(asset_hub.REGISTRY)

    def test_registry_is_valid(self):
        self.assertEqual([], asset_hub.validation_errors(self.registry))

    def test_every_role_can_view_pull_and_activate(self):
        policy = asset_hub.read_json(asset_hub.ROOT / "config" / "roles.json")
        required = {"asset.list", "asset.install", "asset.activate"}
        for role, definition in policy["roles"].items():
            self.assertTrue(required.issubset(set(definition["actions"])), role)

    def test_dependencies_are_resolved_before_root(self):
        selected, order = asset_hub.resolve(
            self.registry, "skill/code-review", "1.1.0", "stable"
        )
        self.assertEqual("1.3.0", selected["cli/codex"]["version"])
        self.assertLess(order.index("cli/codex"), order.index("skill/code-review"))

    def test_preview_version_can_be_selected(self):
        selected, _ = asset_hub.resolve(self.registry, "cli/codex", "1.4.0", "preview")
        self.assertEqual("1.4.0", selected["cli/codex"]["version"])

    def test_submit_and_approve_promotes_artifact(self):
        repository = asset_hub.ROOT / ".test-runtime" / "hub"
        if repository.exists():
            shutil.rmtree(repository)
        repository.mkdir(parents=True)
        try:
            shutil.copyfile(asset_hub.REGISTRY, repository / "registry.json")
            artifact = repository / "new-skill.zip"
            artifact.write_bytes(b"test skill payload")
            manifest_path = repository / "submission.json"
            manifest_path.write_text(
                json.dumps({
                    "id": "skill/new-skill",
                    "owner": "AI Platform Team",
                    "release": {
                        "version": "1.0.0",
                        "channel": "stable",
                        "releaseNotes": "Automated test release.",
                        "dependencies": [],
                        "artifact": {
                            "type": "repository",
                            "location": "placeholder",
                            "sha256": "0" * 64,
                        },
                    },
                }),
                encoding="utf-8",
            )
            self.assertEqual(0, asset_hub.command_submit(manifest_path, repository, artifact))
            candidate = repository / "submissions" / "skill__new-skill@1.0.0.json"
            self.assertEqual(
                0,
                asset_hub.command_review(
                    candidate, "reviewed", "TEST\\reviewer", "automated test"
                ),
            )
            self.assertEqual(0, asset_hub.command_approve(repository, candidate))
            updated = asset_hub.read_json(repository / "registry.json")
            release = asset_hub.release_map(asset_hub.package_map(updated)["skill/new-skill"])["1.0.0"]
            promoted = repository / release["artifact"]["location"]
            self.assertTrue(promoted.is_file())
            self.assertEqual(asset_hub.sha256(promoted), release["artifact"]["sha256"])
        finally:
            shutil.rmtree(repository.parent, ignore_errors=True)

    def test_public_repository_falls_back_to_backup(self):
        runtime = asset_hub.ROOT / ".test-runtime"
        public = runtime / "public"
        backup = runtime / "backup"
        public.mkdir(parents=True, exist_ok=True)
        backup.mkdir(parents=True, exist_ok=True)
        try:
            (public / "registry.json").write_text("not-json", encoding="utf-8")
            shutil.copyfile(asset_hub.REGISTRY, backup / "registry.json")
            registry, source = asset_hub.load_registry_with_fallback(public, backup)
            self.assertEqual(backup, source)
            self.assertIn("cli/codex", asset_hub.package_map(registry))
        finally:
            shutil.rmtree(runtime, ignore_errors=True)

    def test_submit_requires_release_notes(self):
        repository = asset_hub.ROOT / ".test-runtime" / "release-notes"
        repository.mkdir(parents=True, exist_ok=True)
        try:
            manifest = repository / "submission.json"
            manifest.write_text(json.dumps({
                "id": "agent/test-agent",
                "owner": "Test",
                "release": {
                    "version": "1.0.0", "channel": "stable",
                    "dependencies": [],
                    "artifact": {
                        "type": "repository", "location": "missing.zip",
                        "sha256": "0" * 64,
                    },
                },
            }), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "更新说明"):
                asset_hub.command_submit(manifest, repository)
        finally:
            shutil.rmtree(repository.parent, ignore_errors=True)


class PortableSkillTests(unittest.TestCase):
    def test_gate_distinguishes_login_from_missing_repository(self):
        runtime = asset_hub.ROOT / ".test-runtime" / "gate-state"
        share = runtime / "share"
        public = share / "data" / "AI-Assets"
        share.mkdir(parents=True, exist_ok=True)
        try:
            output = io.StringIO()
            with (
                mock.patch.object(ai_assets_skill, "SHARE_ROOT", share),
                mock.patch.object(ai_assets_skill, "PUBLIC", public),
                mock.patch.object(ai_assets_skill, "smb_principal", return_value="GETACAD\\tester"),
                contextlib.redirect_stdout(output),
            ):
                self.assertEqual(0, ai_assets_skill.gate())
            result = json.loads(output.getvalue())
            self.assertEqual("setup_required", result["state"])
            self.assertEqual("GETACAD\\tester", result["principal"])
        finally:
            shutil.rmtree(runtime.parent, ignore_errors=True)

    def test_secure_login_is_not_process_scoped(self):
        script = (
            asset_hub.ROOT / "skills" / "ai-assets-manager" / "scripts" / "secure-login.ps1"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("net.exe", script)
        self.assertIn("smb-identity.ps1", script)
        self.assertIn("Disconnect-AiAssetsServerConnections", script)
        self.assertIn("输入 Y 确认", script)
        self.assertIn("Start-Process", script)
        self.assertIn("-NoNewWindow", script)
        self.assertIn("$connectProcess.ExitCode", script)
        self.assertIn("$deleteProcess.ExitCode", script)
        self.assertNotIn("New-PSDrive", script)

    def test_hub_wrapper_verifies_identity_and_can_login(self):
        script = (
            asset_hub.ROOT / "skills" / "ai-assets-manager" / "scripts" / "hub.ps1"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("smb-identity.ps1", script)
        self.assertIn("secure-login.ps1", script)
        self.assertIn("Join-Path $PSScriptRoot 'asset_hub.py'", script)
        self.assertTrue(
            (
                asset_hub.ROOT
                / "skills"
                / "ai-assets-manager"
                / "scripts"
                / "ai_assets.py"
            ).is_file()
        )

    def test_identity_helper_uses_windows_network_provider_fallback(self):
        script = (
            asset_hub.ROOT / "skills" / "ai-assets-manager" / "scripts" / "smb-identity.ps1"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("WNetGetUser", script)
        self.assertIn("Get-SmbConnection", script)
        self.assertNotIn("AI_ASSET_ACTOR", script)

    def test_repository_principal_uses_native_fallback(self):
        repository = Path(r"\\server\share\repo")
        completed = asset_hub.subprocess.CompletedProcess([], 0, stdout="", stderr="")
        with (
            mock.patch.object(asset_hub.subprocess, "run", return_value=completed),
            mock.patch.object(
                asset_hub, "native_smb_principal", return_value="GETACAD\\tester"
            ),
        ):
            self.assertEqual(
                "GETACAD\\tester",
                asset_hub.repository_principal(repository, require_smb_identity=True),
            )

    def test_initial_deployment_bootstraps_actual_smb_administrator(self):
        script = (asset_hub.ROOT / "scripts" / "deploy-to-smb.ps1").read_text(
            encoding="utf-8-sig"
        )
        self.assertIn("Get-AiAssetsSmbPrincipal", script)
        self.assertIn("Initialize-Administrator", script)
        self.assertIn("bootstrap-admin.completed.json", script)
        self.assertIn("UTF8Encoding($false)", script)

    def test_initial_admin_recovery_is_one_time_and_placeholder_limited(self):
        script = (
            asset_hub.ROOT / "scripts" / "recover-initial-admin.ps1"
        ).read_text(encoding="utf-8-sig")
        self.assertIn("GETACAD\\lfaf-test", script)
        self.assertIn("bootstrap-admin.completed.json", script)
        self.assertIn("Test-SameAccountSet", script)
        self.assertIn("originalRolesSha256", script)
        self.assertIn("UTF8Encoding($false)", script)

    def test_generated_release_notes_are_chinese(self):
        root = asset_hub.ROOT / ".test-runtime" / "release-note-generation"
        root.mkdir(parents=True, exist_ok=True)
        try:
            (root / "SKILL.md").write_text("# 测试\n", encoding="utf-8")
            notes, _ = ai_assets_skill.generated_release_notes(
                root, {"id": "skill/test", "version": "1.0.0"}
            )
            self.assertIn("首次发布", notes)
        finally:
            shutil.rmtree(root.parent, ignore_errors=True)

    def test_backup_rotation_keeps_three(self):
        parent = asset_hub.ROOT / ".test-runtime" / "backup-rotation"
        parent.mkdir(parents=True, exist_ok=True)
        try:
            for index in range(5):
                item = parent / f".ai-assets-manager.backup.20260725-00000{index}.1.0.{index}"
                item.mkdir()
            ai_assets_skill.prune_backups(parent)
            self.assertEqual(3, len(ai_assets_skill.backup_directories(parent)))
        finally:
            shutil.rmtree(parent.parent, ignore_errors=True)

    def test_backup_mirrors_to_public(self):
        runtime = asset_hub.ROOT / ".test-runtime"
        public = runtime / "public"
        backup = runtime / "backup"
        public.mkdir(parents=True, exist_ok=True)
        backup.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(asset_hub.REGISTRY, backup / "registry.json")
            artifact_sources = {
                "artifacts/cli/codex/1.3.0/codex-1.3.0.txt": asset_hub.ROOT / "examples" / "artifacts" / "codex-1.3.0.txt",
                "artifacts/cli/codex/1.4.0/codex-1.4.0.txt": asset_hub.ROOT / "examples" / "artifacts" / "codex-1.4.0.txt",
                "artifacts/skill/code-review/1.1.0/code-review-1.1.0.txt": asset_hub.ROOT / "examples" / "artifacts" / "code-review-1.1.0.txt",
                "artifacts/skill/ai-assets-manager/1.0.0/ai-assets-manager-1.0.0.zip": asset_hub.ROOT / "artifacts" / "skill" / "ai-assets-manager" / "1.0.0" / "ai-assets-manager-1.0.0.zip",
                "artifacts/skill/ai-assets-manager/1.0.1/ai-assets-manager-1.0.1.zip": asset_hub.ROOT / "artifacts" / "skill" / "ai-assets-manager" / "1.0.1" / "ai-assets-manager-1.0.1.zip",
                "artifacts/skill/ai-assets-manager/1.0.2/ai-assets-manager-1.0.2.zip": asset_hub.ROOT / "artifacts" / "skill" / "ai-assets-manager" / "1.0.2" / "ai-assets-manager-1.0.2.zip",
                "artifacts/skill/ai-assets-manager/1.0.3/ai-assets-manager-1.0.3.zip": asset_hub.ROOT / "artifacts" / "skill" / "ai-assets-manager" / "1.0.3" / "ai-assets-manager-1.0.3.zip",
                "artifacts/skill/ai-assets-manager/1.0.4/ai-assets-manager-1.0.4.zip": asset_hub.ROOT / "artifacts" / "skill" / "ai-assets-manager" / "1.0.4" / "ai-assets-manager-1.0.4.zip",
                "artifacts/skill/ai-assets-manager/1.0.5/ai-assets-manager-1.0.5.zip": asset_hub.ROOT / "artifacts" / "skill" / "ai-assets-manager" / "1.0.5" / "ai-assets-manager-1.0.5.zip",
                "artifacts/skill/ai-assets-manager/1.0.6/ai-assets-manager-1.0.6.zip": asset_hub.ROOT / "artifacts" / "skill" / "ai-assets-manager" / "1.0.6" / "ai-assets-manager-1.0.6.zip",
            }
            for relative, source in artifact_sources.items():
                destination = backup / relative
                destination.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, destination)
            self.assertEqual(0, asset_hub.command_mirror(backup, public))
            self.assertEqual(
                asset_hub.read_json(backup / "registry.json"),
                asset_hub.read_json(public / "registry.json"),
            )
            self.assertTrue((public / "artifacts" / "cli" / "codex" / "1.3.0" / "codex-1.3.0.txt").is_file())
        finally:
            shutil.rmtree(runtime, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
