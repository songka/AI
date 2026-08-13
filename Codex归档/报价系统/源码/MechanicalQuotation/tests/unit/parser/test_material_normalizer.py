"""Tests for Material Normalizer."""

from __future__ import annotations

import pytest

from quotation.infrastructure.parser.material_normalizer import (
    get_canonical_name,
    normalize_material,
)


class TestExactMatches:
    def test_a6061_t6(self):
        r = normalize_material("A6061-T6")
        assert r.normalized == "A6061-T6"
        assert r.confidence == 0.95

    def test_sus304(self):
        r = normalize_material("SUS304")
        assert r.normalized == "SUS304"

    def test_s50c(self):
        r = normalize_material("S50C")
        assert r.normalized == "S50C"

    def test_skd11(self):
        r = normalize_material("SKD11")
        assert r.normalized == "SKD11"

    def test_spcc(self):
        r = normalize_material("SPCC")
        assert r.normalized == "SPCC"


class TestAliasMatches:
    def test_6061_alias(self):
        """6061 → A6061-T6"""
        r = normalize_material("6061")
        assert r.normalized == "A6061-T6"
        assert r.confidence >= 0.7

    def test_al6061_alias(self):
        r = normalize_material("AL6061")
        assert r.normalized == "A6061-T6"

    def test_304_alias(self):
        """304 → SUS304"""
        r = normalize_material("304")
        assert r.normalized == "SUS304"

    def test_sus_304_with_dash(self):
        r = normalize_material("SUS-304")
        assert r.normalized == "SUS304"

    def test_sus304_with_space(self):
        r = normalize_material("SUS 304")
        assert r.normalized == "SUS304"

    def test_lowercase(self):
        r = normalize_material("s50c")
        assert r.normalized == "S50C"

    def test_skd11_with_dash(self):
        r = normalize_material("SKD-11")
        assert r.normalized == "SKD11"


class TestPartialMatches:
    def test_6061_aluminum_chinese(self):
        r = normalize_material("6061鋁")
        assert r.normalized == "A6061-T6"
        assert r.confidence >= 0.7

    def test_aluminum_6061_chinese(self):
        r = normalize_material("鋁6061")
        assert r.normalized == "A6061-T6"

    def test_stainless_304_chinese(self):
        r = normalize_material("304不鏽鋼")
        assert r.normalized == "SUS304"

    @pytest.mark.parametrize("text", ["材質為3mm厚度不鏽鋼", "材质为3mm厚度不锈钢"])
    def test_generic_stainless_annotation_uses_shop_default_sus304(self, text):
        r = normalize_material(text)
        assert r.normalized == "SUS304"
        assert r.confidence >= 0.7

    def test_304ss(self):
        r = normalize_material("304SS")
        assert r.normalized == "SUS304"


class TestUnknownMaterials:
    def test_unknown(self):
        r = normalize_material("Unobtainium-X99")
        assert r.normalized is None
        assert r.confidence == 0.0

    def test_empty(self):
        r = normalize_material("")
        assert r.normalized is None

    def test_hint_only(self):
        """Material with category hint but unknown grade."""
        r = normalize_material("某種鋁合金")
        assert r.normalized is None
        assert r.confidence == 0.3
        assert "鋁合金" in r.note


class TestConvenience:
    def test_get_canonical_name(self):
        assert get_canonical_name("SUS304") == "SUS304"
        assert get_canonical_name("304") == "SUS304"
        assert get_canonical_name("unknown") is None
