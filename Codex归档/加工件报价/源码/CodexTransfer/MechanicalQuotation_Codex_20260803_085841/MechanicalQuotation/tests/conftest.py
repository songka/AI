"""Global test fixtures and configuration."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test output."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_config():
    """Provide a Config instance with test defaults."""
    from quotation.utils.config import Config

    config = Config()
    config.output_dir = "test_output"
    config.logs_dir = "test_logs"
    config.ai_enabled = False
    return config


@pytest.fixture
def rules_yaml_path():
    """Path to the quotation rules YAML file."""
    path = Path("rules/quotation-rules.yaml")
    if path.exists():
        return str(path)
    # Fallback: try the parent directory
    alt_path = Path("../rules/quotation-rules_V1.1.yaml")
    if alt_path.exists():
        return str(alt_path)
    pytest.skip("Rules YAML file not found")
