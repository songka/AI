"""Tests for Material domain model."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from quotation.domain.material import MaterialProperties


class TestMaterialProperties:
    def test_create(self):
        m = MaterialProperties(
            name="A6061-T6",
            density=2.70,
            category="鋁合金",
            grade="6061-T6",
        )
        assert m.name == "A6061-T6"
        assert m.density == 2.70
        assert m.category == "鋁合金"
        assert m.grade == "6061-T6"
        assert m.source_file == "material-density.yaml"

    def test_create_steel(self):
        m = MaterialProperties(
            name="S50C", density=7.85, category="碳素鋼", grade="S50C"
        )
        assert m.density == 7.85
        assert m.category == "碳素鋼"

    def test_create_with_note(self):
        m = MaterialProperties(
            name="普通鋼",
            density=7.85,
            category="普通碳鋼",
            grade="通用",
            note="通用值，用於未標明具體牌號的鋼件",
        )
        assert m.note is not None

    def test_zero_density_raises(self):
        with pytest.raises(ValidationError):
            MaterialProperties(name="Water", density=0, category="液體", grade="H2O")

    def test_negative_density_raises(self):
        with pytest.raises(ValidationError):
            MaterialProperties(name="X", density=-1.0, category="?", grade="?")

    def test_missing_required(self):
        with pytest.raises(ValidationError):
            MaterialProperties(name="X", density=1.0)  # type: ignore[call-arg]

    def test_custom_source_file(self):
        m = MaterialProperties(
            name="Custom",
            density=8.0,
            category="特殊",
            grade="X",
            source_file="custom.yaml",
        )
        assert m.source_file == "custom.yaml"
