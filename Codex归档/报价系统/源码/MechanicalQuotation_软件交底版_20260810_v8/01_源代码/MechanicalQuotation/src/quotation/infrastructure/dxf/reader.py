"""DXF Reader — reads DXF files via ezdxf into Drawing model with RawEntity list."""

from __future__ import annotations

import logging
import time
from pathlib import Path

from quotation.domain.drawing import Drawing, DrawingFormat, ParseStatus, TextEntity
from quotation.domain.import_result import ImportResult
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

logger = logging.getLogger("quotation.infrastructure.dxf.reader")


class DxfReader:
    """Read DXF files using ezdxf and produce Drawing with RawEntity list."""

    def read(self, dxf_path: str | Path) -> ImportResult:
        """Read a DXF file and produce Drawing model with raw entities."""
        import ezdxf

        path = Path(dxf_path)
        started = time.monotonic()

        result = ImportResult(
            source_file=str(path),
            source_format="DXF",
        )

        if not path.exists():
            result.import_status = "failed"
            result.errors.append(f"File not found: {path}")
            return result

        try:
            doc = ezdxf.readfile(str(path))
        except ezdxf.DXFStructureError as e:
            result.import_status = "failed"
            result.errors.append(f"DXF structure error: {e}")
            return result
        except Exception as e:
            result.import_status = "failed"
            result.errors.append(f"DXF read error: {e}")
            return result

        try:
            msp = doc.modelspace()
            entities = list(msp)

            # Detect drawing unit
            drawing_unit, unit_source = self._detect_unit(doc)

            # Build raw entities + text
            raw_entities: list[RawEntity] = []
            entity_summary: dict[str, int] = {}
            text_entities: list[TextEntity] = []
            raw_texts: list[str] = []

            for e in entities:
                etype = e.dxftype()
                entity_summary[etype] = entity_summary.get(etype, 0) + 1

                raw = self._extract_raw_entity(e, str(path))
                if raw:
                    raw_entities.append(raw)

                # Also collect text for existing Drawing.texts
                if etype in ("TEXT", "MTEXT"):
                    content = ""
                    pos_x, pos_y = 0.0, 0.0
                    height = 2.5

                    if etype == "TEXT":
                        content = e.dxf.text
                        pos_x = e.dxf.insert.x
                        pos_y = e.dxf.insert.y
                        height = e.dxf.height
                    elif etype == "MTEXT":
                        content = e.plain_text() if hasattr(e, "plain_text") else str(e.text)
                        pos_x = e.dxf.insert.x
                        pos_y = e.dxf.insert.y
                        height = e.dxf.char_height

                    text_entities.append(TextEntity(
                        content=content,
                        position_x=pos_x,
                        position_y=pos_y,
                        height=height,
                        entity_type=etype,
                    ))
                    if content.strip():
                        raw_texts.append(content.strip())

            # Build Drawing
            drawing = Drawing(
                id=f"dxf-{path.stem}",
                file_path=str(path),
                file_name=path.name,
                source_format=DrawingFormat.DXF,
                entity_count=len(entities),
                entity_summary=entity_summary,
                raw_entities=raw_entities,
                drawing_unit=drawing_unit,
                unit_source=unit_source,
                all_texts=text_entities,
                raw_text_strings=raw_texts,
                parse_status=ParseStatus.SUCCESS,
            )

            result.drawing = drawing
            result.import_status = "success"

            if len(entities) == 0:
                result.import_status = "partial"
                result.warnings.append("DXF contains no entities")

        except Exception as e:
            result.import_status = "partial"
            result.warnings.append(f"Entity parsing warning: {e}")

        result.import_duration_ms = (time.monotonic() - started) * 1000
        return result

    # -- Unit detection --

    def _detect_unit(self, doc) -> tuple[DrawingUnit, str | None]:
        """Detect drawing unit from DXF header."""
        try:
            insunits = doc.header.get("$INSUNITS", 0)
            if insunits == 4:
                return DrawingUnit.MM, "CAD_HEADER($INSUNITS=4)"
            elif insunits == 1:
                return DrawingUnit.INCH, "CAD_HEADER($INSUNITS=1)"
        except Exception:
            pass

        # Check $MEASUREMENT
        try:
            measurement = doc.header.get("$MEASUREMENT", 0)
            if measurement == 1:
                return DrawingUnit.MM, "CAD_HEADER($MEASUREMENT=1)"
            elif measurement == 0:
                return DrawingUnit.INCH, "CAD_HEADER($MEASUREMENT=0)"
        except Exception:
            pass

        return DrawingUnit.UNKNOWN, None

    # -- Entity extraction --

    def _extract_raw_entity(self, e, source_file: str) -> RawEntity | None:
        """Extract a RawEntity from an ezdxf entity."""
        etype = e.dxftype()
        handle = e.dxf.handle if hasattr(e.dxf, "handle") else None
        layer = e.dxf.layer if hasattr(e.dxf, "layer") else None
        color = e.dxf.color if hasattr(e.dxf, "color") else None

        geometry = None
        entity_type = EntityType.UNKNOWN

        try:
            if etype == "LINE":
                geometry = LineGeometry(
                    start_x=e.dxf.start.x, start_y=e.dxf.start.y, start_z=e.dxf.start.z,
                    end_x=e.dxf.end.x, end_y=e.dxf.end.y, end_z=e.dxf.end.z,
                )
                entity_type = EntityType.LINE

            elif etype == "CIRCLE":
                geometry = CircleGeometry(
                    center_x=e.dxf.center.x, center_y=e.dxf.center.y, center_z=e.dxf.center.z,
                    radius=e.dxf.radius,
                )
                entity_type = EntityType.CIRCLE

            elif etype == "ARC":
                geometry = ArcGeometry(
                    center_x=e.dxf.center.x, center_y=e.dxf.center.y, center_z=e.dxf.center.z,
                    radius=e.dxf.radius,
                    start_angle=e.dxf.start_angle,
                    end_angle=e.dxf.end_angle,
                )
                entity_type = EntityType.ARC

            elif etype == "POLYLINE":
                verts = [[v.dxf.location.x, v.dxf.location.y, v.dxf.location.z] for v in e.vertices]
                is_closed = e.is_closed if hasattr(e, "is_closed") else False
                geometry = PolylineGeometry(vertices=verts, is_closed=is_closed, vertex_count=len(verts))
                entity_type = EntityType.POLYLINE

            elif etype == "LWPOLYLINE":
                verts = [[v[0], v[1], 0.0] for v in e.get_points()]
                is_closed = e.closed
                geometry = PolylineGeometry(vertices=verts, is_closed=is_closed, vertex_count=len(verts))
                entity_type = EntityType.LWPOLYLINE

            elif etype == "TEXT":
                geometry = TextGeometry(
                    content=e.dxf.text,
                    position_x=e.dxf.insert.x, position_y=e.dxf.insert.y, position_z=e.dxf.insert.z,
                    height=e.dxf.height,
                    rotation=e.dxf.rotation if hasattr(e.dxf, "rotation") else 0.0,
                    width_factor=e.dxf.width if hasattr(e.dxf, "width") else 1.0,
                )
                entity_type = EntityType.TEXT

            elif etype == "MTEXT":
                content = e.plain_text() if hasattr(e, "plain_text") else str(e.text)
                geometry = TextGeometry(
                    content=content,
                    position_x=e.dxf.insert.x, position_y=e.dxf.insert.y, position_z=e.dxf.insert.z,
                    height=e.dxf.char_height,
                )
                entity_type = EntityType.MTEXT

            elif etype == "INSERT":
                geometry = InsertGeometry(
                    block_name=e.dxf.name,
                    position_x=e.dxf.insert.x, position_y=e.dxf.insert.y, position_z=e.dxf.insert.z,
                    scale_x=e.dxf.xscale if hasattr(e.dxf, "xscale") else 1.0,
                    scale_y=e.dxf.yscale if hasattr(e.dxf, "yscale") else 1.0,
                    rotation=e.dxf.rotation if hasattr(e.dxf, "rotation") else 0.0,
                )
                entity_type = EntityType.INSERT

            elif etype in ("DIMENSION", "HATCH", "POINT", "ELLIPSE", "SPLINE"):
                entity_type = EntityType(etype)

        except Exception as exc:
            logger.debug("Skipping entity %s due to: %s", etype, exc)
            return None

        return RawEntity(
            entity_type=entity_type,
            handle=handle,
            geometry=geometry,
            layer=layer,
            color=color,
            source_file=source_file,
        )
