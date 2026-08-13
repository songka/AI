"""Tests for RawEntity model and DrawingUnit."""

from __future__ import annotations

import json

from quotation.domain.raw_entity import (
    ArcGeometry,
    CircleGeometry,
    DrawingUnit,
    EntityType,
    InsertGeometry,
    LineGeometry,
    PolylineGeometry,
    RawEntity,
    TextGeometry,
)


class TestDrawingUnit:
    def test_values(self):
        assert DrawingUnit.MM == "MM"
        assert DrawingUnit.INCH == "INCH"
        assert DrawingUnit.UNKNOWN == "UNKNOWN"


class TestLineGeometry:
    def test_create(self):
        g = LineGeometry(start_x=0, start_y=0, end_x=100, end_y=0)
        assert g.length == 100.0

    def test_diagonal(self):
        g = LineGeometry(start_x=0, start_y=0, end_x=30, end_y=40)
        assert g.length == 50.0

    def test_3d(self):
        g = LineGeometry(start_x=0, start_y=0, start_z=5, end_x=0, end_y=0, end_z=15)
        assert g.start_z == 5
        assert g.end_z == 15


class TestCircleGeometry:
    def test_create(self):
        g = CircleGeometry(center_x=50, center_y=25, radius=5)
        assert g.radius == 5.0
        assert g.diameter == 10.0

    def test_serialize(self):
        g = CircleGeometry(center_x=10, center_y=20, radius=3)
        data = g.model_dump()
        assert data["radius"] == 3.0


class TestArcGeometry:
    def test_create(self):
        g = ArcGeometry(center_x=0, center_y=0, radius=10, start_angle=0, end_angle=90)
        assert g.angle_span == 90.0

    def test_wrap_angle(self):
        g = ArcGeometry(center_x=0, center_y=0, radius=10, start_angle=270, end_angle=90)
        assert g.angle_span == 180.0


class TestPolylineGeometry:
    def test_create(self):
        g = PolylineGeometry(
            vertices=[[0, 0, 0], [100, 0, 0], [100, 50, 0], [0, 50, 0]],
            is_closed=True,
            vertex_count=4,
        )
        assert len(g.vertices) == 4
        assert g.is_closed

    def test_serialize(self):
        g = PolylineGeometry(vertices=[[1, 2, 0], [3, 4, 0]], vertex_count=2)
        data = g.model_dump()
        assert len(data["vertices"]) == 2


class TestTextGeometry:
    def test_create(self):
        g = TextGeometry(content="S50C", position_x=10, position_y=30, height=5.0)
        assert g.content == "S50C"
        assert g.height == 5.0


class TestInsertGeometry:
    def test_create(self):
        g = InsertGeometry(block_name="BOLT_M6", position_x=50, position_y=50)
        assert g.block_name == "BOLT_M6"


class TestRawEntity:
    def test_line_entity(self):
        geom = LineGeometry(start_x=0, start_y=0, end_x=100, end_y=0)
        e = RawEntity(
            entity_type=EntityType.LINE,
            handle="AB",
            geometry=geom,
            layer="0",
            color=7,
            source_file="test.dxf",
        )
        assert e.entity_type == EntityType.LINE
        assert e.layer == "0"
        assert e.color == 7
        assert e.source_file == "test.dxf"
        assert isinstance(e.geometry, LineGeometry)
        assert e.geometry.length == 100.0

    def test_circle_entity(self):
        geom = CircleGeometry(center_x=50, center_y=25, radius=5)
        e = RawEntity(entity_type=EntityType.CIRCLE, geometry=geom, layer="HOLES")
        assert isinstance(e.geometry, CircleGeometry)
        assert e.geometry.diameter == 10.0

    def test_arc_entity(self):
        geom = ArcGeometry(center_x=0, center_y=0, radius=10, start_angle=0, end_angle=180)
        e = RawEntity(entity_type=EntityType.ARC, geometry=geom)
        assert e.geometry.angle_span == 180.0

    def test_polyline_entity(self):
        geom = PolylineGeometry(vertices=[[0, 0], [10, 0], [10, 10]], is_closed=True, vertex_count=3)
        e = RawEntity(entity_type=EntityType.LWPOLYLINE, geometry=geom)
        assert e.geometry.is_closed

    def test_json_roundtrip(self):
        geom = CircleGeometry(center_x=50, center_y=25, radius=5)
        e = RawEntity(
            entity_type=EntityType.CIRCLE,
            handle="AB",
            geometry=geom,
            layer="HOLES",
            color=1,
            source_file="test.dxf",
        )
        json_str = e.model_dump_json()
        restored = RawEntity.model_validate_json(json_str)
        assert restored.entity_type == EntityType.CIRCLE
        assert restored.handle == "AB"
        assert restored.layer == "HOLES"
        assert isinstance(restored.geometry, CircleGeometry)
        assert restored.geometry.radius == 5.0

    def test_list_serialization(self):
        """List of RawEntity should JSON-serialize correctly."""
        entities = [
            RawEntity(entity_type=EntityType.LINE, geometry=LineGeometry(start_x=0, start_y=0, end_x=10, end_y=0)),
            RawEntity(entity_type=EntityType.CIRCLE, geometry=CircleGeometry(center_x=5, center_y=5, radius=2)),
        ]
        data = [e.model_dump() for e in entities]
        json_str = json.dumps(data, ensure_ascii=False)
        assert "LINE" in json_str
        assert "CIRCLE" in json_str

    def test_no_geometry(self):
        e = RawEntity(entity_type=EntityType.HATCH, layer="HATCH")
        assert e.geometry is None
