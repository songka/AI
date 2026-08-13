from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

from gomoku.conversation import Intent, parse_input
from gomoku.game import Game


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = PROJECT_ROOT / "scripts"


class SafetyTests(unittest.TestCase):
    def test_parser_rejects_destructive_commands(self) -> None:
        for command in ("删除数据", "clear", "reset game", "remove all"):
            self.assertEqual(Intent.INVALID, parse_input(command).intent)

    def test_game_has_no_persistence_or_network_api(self) -> None:
        forbidden = {"save", "load", "delete", "remove", "download", "upload", "connect"}
        public_names = {name.lower() for name in dir(Game) if not name.startswith("_")}
        self.assertTrue(forbidden.isdisjoint(public_names))
        for path in (PROJECT_ROOT / "src" / "gomoku").glob("*.py"):
            source = path.read_text(encoding="utf-8")
            for module in ("socket", "requests", "urllib", "http.client"):
                self.assertNotIn(f"import {module}", source)

    def test_sensitive_scanner_detects_forbidden_fixture(self) -> None:
        scanner_path = SCRIPTS / "check-sensitive-files.py"
        specification = importlib.util.spec_from_file_location("sensitive_scanner", scanner_path)
        self.assertIsNotNone(specification)
        self.assertIsNotNone(specification.loader)
        module = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(module)
        self.assertTrue(module.is_forbidden_filename(Path("credentials.txt")))
        self.assertTrue(module.is_forbidden_filename(Path("server.key")))
        self.assertFalse(module.is_forbidden_filename(Path("architecture.md")))

    def test_release_script_has_no_overwrite_path(self) -> None:
        source = (SCRIPTS / "release.ps1").read_text(encoding="utf-8")
        self.assertIn("if (Test-Path -LiteralPath $OutputPath)", source)
        self.assertIn("will not be overwritten", source)
        self.assertNotIn("Remove-Item", source)
        self.assertIn("Get-CompatibleRelativePath", source)
        self.assertNotIn("[System.IO.Path]::GetRelativePath", source)
        self.assertIn("New-Item -ItemType Directory -Path $OutputDirectory", source)

    def test_release_skill_inclusion_is_explicit(self) -> None:
        source = (SCRIPTS / "release.ps1").read_text(encoding="utf-8")
        self.assertIn("[switch]$IncludeSkill", source)
        self.assertIn("if ($IncludeSkill)", source)
        self.assertNotIn("$IncludeSkill = $true", source)


if __name__ == "__main__":
    unittest.main()
