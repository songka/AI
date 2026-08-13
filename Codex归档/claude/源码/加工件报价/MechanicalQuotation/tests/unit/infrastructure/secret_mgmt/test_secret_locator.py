"""Tests for SecretLocator."""
from __future__ import annotations

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from quotation.infrastructure.secrets.secret_locator import SecretLocator


class TestSecretLocator:
    def test_env_var_priority(self, monkeypatch):
        monkeypatch.setenv("MECHANICAL_QUOTATION_DEEPSEEK_KEY", "env-key-123")
        key = SecretLocator.get_deepseek_key()
        assert key == "env-key-123"

    def test_env_var_empty_ignored(self, monkeypatch):
        monkeypatch.setenv("MECHANICAL_QUOTATION_DEEPSEEK_KEY", "   ")
        # When env var is whitespace-only, fall through to file search
        # Mock _find_secret_path to prevent finding the runtime dev key
        with patch.object(SecretLocator, '_find_secret_path', return_value=None):
            key = SecretLocator.get_deepseek_key()
            assert key is None

    def test_not_configured_without_key(self, monkeypatch):
        monkeypatch.delenv("MECHANICAL_QUOTATION_DEEPSEEK_KEY", raising=False)
        # In CI/test env without runtime secret file
        with patch.object(SecretLocator, '_find_secret_path', return_value=None):
            key = SecretLocator.get_deepseek_key()
            assert key is None

    def test_is_configured_false(self, monkeypatch):
        monkeypatch.delenv("MECHANICAL_QUOTATION_DEEPSEEK_KEY", raising=False)
        with patch.object(SecretLocator, '_find_secret_path', return_value=None):
            assert SecretLocator.is_configured() is False

    def test_file_key_loading(self, tmp_path):
        secret_file = tmp_path / "deepseek_api_key.txt"
        secret_file.write_text("file-key-456\n")
        with patch.object(SecretLocator, '_find_secret_path', return_value=secret_file):
            monkeypatch = pytest.MonkeyPatch()
            monkeypatch.delenv("MECHANICAL_QUOTATION_DEEPSEEK_KEY", raising=False)
            key = SecretLocator.get_deepseek_key()
            assert key == "file-key-456"
