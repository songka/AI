"""Tests for Dimension Parser."""

from __future__ import annotations

import pytest

from quotation.infrastructure.parser.dimension_parser import (
    DimensionStatus,
    parse_dimension,
)


class TestParse3DDimensions:
    def test_star_separator(self):
        r = parse_dimension("928*796*15")
        assert r.status == DimensionStatus.SUCCESS
        assert r.length == 928.0
        assert r.width == 796.0
        assert r.height == 15.0
        assert r.is_circular is False

    def test_x_separator_lowercase(self):
        r = parse_dimension("60x70x20")
        assert r.status == DimensionStatus.SUCCESS
        assert r.length == 60.0
        assert r.width == 70.0
        assert r.height == 20.0

    def test_multiplication_sign(self):
        r = parse_dimension("1300×117.2×88")
        assert r.status == DimensionStatus.SUCCESS
        assert r.length == 1300.0
        assert r.width == 117.2
        assert r.height == 88.0

    def test_decimal_values(self):
        r = parse_dimension("1208*103.5*2")
        assert r.length == 1208.0
        assert r.width == 103.5
        assert r.height == 2.0

    def test_spaces_around_separator(self):
        r = parse_dimension("798 * 530 * 15")
        assert r.length == 798.0
        assert r.width == 530.0
        assert r.height == 15.0


class TestParse2DDimensions:
    def test_two_dimensional(self):
        r = parse_dimension("40*40")
        assert r.status == DimensionStatus.PARTIAL
        assert r.length == 40.0
        assert r.width == 40.0
        assert r.height is None

    def test_rectangular_2d(self):
        r = parse_dimension("60×70")
        assert r.length == 60.0
        assert r.width == 70.0


class TestParseCircular:
    def test_diameter_times_thickness(self):
        r = parse_dimension("φ250×15")
        assert r.status == DimensionStatus.SUCCESS
        assert r.length == 250.0
        assert r.height == 15.0
        assert r.is_circular is True

    def test_phi_star_format(self):
        r = parse_dimension("Φ250*15")
        assert r.length == 250.0
        assert r.is_circular is True

    def test_single_diameter(self):
        r = parse_dimension("φ250")
        assert r.status == DimensionStatus.PARTIAL
        assert r.length == 250.0
        assert r.is_circular is True


class TestParseThreadSpec:
    def test_m8(self):
        r = parse_dimension("M8")
        assert r.status == DimensionStatus.SUCCESS
        assert r.is_thread is True
        assert r.thread_spec == "M8"

    def test_m6(self):
        r = parse_dimension("M6")
        assert r.is_thread is True
        assert r.thread_spec == "M6"

    def test_m12_with_pitch(self):
        r = parse_dimension("M12×1.5")
        assert r.is_thread is True
        assert r.thread_spec == "M12×1.5"

    def test_lowercase_m(self):
        r = parse_dimension("m8")
        assert r.is_thread is True
        assert r.thread_spec == "M8"


class TestParseEdgeCases:
    def test_empty_string(self):
        r = parse_dimension("")
        assert r.status == DimensionStatus.FAILED

    def test_single_number(self):
        r = parse_dimension("15")
        assert r.status == DimensionStatus.PARTIAL
        assert r.height == 15.0

    def test_unparseable_text(self):
        r = parse_dimension("some random text")
        assert r.status == DimensionStatus.FAILED

    def test_whitespace_only(self):
        r = parse_dimension("   ")
        assert r.status == DimensionStatus.FAILED
