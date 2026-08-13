"""Smoke tests — verify that the project infrastructure is functional.

These tests validate Phase 0 completion.
"""

from __future__ import annotations

import sys
from pathlib import Path


class TestProjectStructure:
    """Verify that the project directory structure matches the constitution."""

    def test_src_directory_exists(self):
        """src/quotation/ must exist."""
        src = Path("src/quotation")
        assert src.is_dir(), f"Missing: {src}"

    def test_domain_layer_exists(self):
        """Domain layer directory must exist."""
        assert Path("src/quotation/domain").is_dir()

    def test_application_layer_exists(self):
        """Application layer directory must exist."""
        assert Path("src/quotation/application").is_dir()

    def test_infrastructure_layer_exists(self):
        """Infrastructure layer directory must exist."""
        assert Path("src/quotation/infrastructure").is_dir()

    def test_rules_engine_exists(self):
        """Rules engine directory must exist."""
        assert Path("src/quotation/rules").is_dir()

    def test_cli_exists(self):
        """CLI entry point must exist."""
        assert Path("src/quotation/cli").is_dir()

    def test_utils_exists(self):
        """Utils directory must exist."""
        assert Path("src/quotation/utils").is_dir()

    def test_tests_exist(self):
        """Tests directory must exist with unit/integration/regression."""
        assert Path("tests/unit").is_dir()
        assert Path("tests/integration").is_dir()
        assert Path("tests/regression").is_dir()

    def test_pyproject_exists(self):
        """pyproject.toml must exist."""
        assert Path("pyproject.toml").is_file()


class TestVersion:
    """Verify the package version is accessible."""

    def test_version_is_string(self):
        """__version__ must be a non-empty string."""
        from quotation import __version__

        assert isinstance(__version__, str)
        assert len(__version__) > 0

    def test_version_format(self):
        """Version should follow semver format (major.minor.patch)."""
        from quotation import __version__

        parts = __version__.split(".")
        assert len(parts) >= 2, f"Invalid version format: {__version__}"
        for part in parts:
            assert part.isdigit(), f"Version part not numeric: {part}"


class TestConfig:
    """Verify the configuration system works."""

    def test_config_creation(self):
        """Config should create with default values."""
        from quotation.utils.config import Config

        config = Config()
        assert config is not None
        assert config.rules_dir == "rules"
        assert config.ai_enabled is False  # Must default to disabled

    def test_config_from_env(self):
        """Config.from_env() should return a Config instance."""
        from quotation.utils.config import Config

        config = Config.from_env()
        assert isinstance(config, Config)

    def test_config_ensure_dirs(self, temp_dir):
        """ensure_dirs should create output and logs directories."""
        from quotation.utils.config import Config

        config = Config()
        config.output_dir = str(temp_dir / "output")
        config.logs_dir = str(temp_dir / "logs")
        config.ensure_dirs()

        assert Path(config.output_dir).is_dir()
        assert Path(config.logs_dir).is_dir()


class TestLogging:
    """Verify the logging system works."""

    def test_setup_logging_returns_logger(self):
        """setup_logging should return a Logger."""
        from quotation.utils.logging import setup_logging

        logger = setup_logging(level="DEBUG")
        assert logger is not None
        assert logger.name == "quotation"

    def test_get_logger_returns_child(self):
        """get_logger should return a child logger."""
        from quotation.utils.logging import get_logger, setup_logging

        setup_logging(level="DEBUG")
        logger = get_logger("test_module")
        assert logger.name == "quotation.test_module"


class TestSerialization:
    """Verify the serialization utilities work."""

    def test_to_json_basic(self):
        """to_json should serialize basic objects."""
        from quotation.utils.serialization import to_json

        data = {"key": "value", "number": 42}
        result = to_json(data)
        assert "key" in result
        assert "value" in result
        assert "42" in result

    def test_to_json_unicode(self):
        """to_json should handle Chinese characters."""
        from quotation.utils.serialization import to_json

        data = {"材料": "AL6061", "價格": 38}
        result = to_json(data)
        assert "材料" in result
        assert "AL6061" in result


class TestCLI:
    """Verify the CLI is importable and has expected commands."""

    def test_cli_is_importable(self):
        """CLI module should be importable."""
        from quotation.cli.main import cli

        assert cli is not None

    def test_cli_has_version_command(self):
        """CLI should have a version command."""
        from quotation.cli.main import cli

        commands = cli.commands
        assert "version" in commands

    def test_cli_has_analyze_command(self):
        """CLI should have an analyze command."""
        from quotation.cli.main import cli

        assert "analyze" in cli.commands

    def test_cli_has_batch_command(self):
        """CLI should have a batch command."""
        from quotation.cli.main import cli

        assert "batch" in cli.commands

    def test_cli_batch_empty_directory_is_friendly(self, tmp_path):
        from click.testing import CliRunner

        from quotation.cli.main import cli

        result = CliRunner().invoke(cli, ["batch", str(tmp_path)])
        assert result.exit_code == 0
        assert "没有找到可报价" in result.output
        assert "not yet implemented" not in result.output


class TestPythonVersion:
    """Verify Python version meets minimum requirement."""

    def test_python_version(self):
        """Python must be 3.11 or higher."""
        assert sys.version_info >= (3, 11), (
            f"Python 3.11+ required, got {sys.version_info.major}.{sys.version_info.minor}"
        )
