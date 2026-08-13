# -*- coding: utf-8 -*-
"""CLI entry point for the Mechanical Quotation System.

Usage:
    quotation version
    quotation demo J003
    quotation demo W001
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import click
import ezdxf

from quotation import __version__
from quotation.infrastructure.dxf.reader import DxfReader
from quotation.infrastructure.feature.geometric import GeometricExtractor
from quotation.infrastructure.feature.manufacturing import ManufacturingExtractor
from quotation.infrastructure.feature.quotation_mapper import QuotationMapper
from quotation.infrastructure.rules.pricing_resolver import PricingResolver
from quotation.infrastructure.rules.quote_builder import QuoteBuilder

# ---------------------------------------------------------------------------
# Demo part definitions
# ---------------------------------------------------------------------------

DEMO_PARTS = {
    "J003": {
        "part_number": "UC1000005854",
        "part_name": "J003",
        "material": "S50C",
        "historical_price": 1425.0,
        "size": (928, 796),
        "circles": [(200, 398, 3), (350, 398, 3), (500, 398, 3), (650, 398, 3)],
        "texts": [
            ("S50C", 10, 810, 8),
            ("6-M6", 200, 400, 5),
            ("表面鍍鉻", 10, 820, 5),
        ],
    },
    "W001": {
        "part_number": "UC2020083221",
        "part_name": "W001",
        "material": "鋁型材",
        "size": (1300, 1300),
        "circles": [],
        "texts": [
            ("鋁型材 40x40", 10, 1320, 6),
            ("防護圍欄", 10, 1340, 6),
            ("門組件", 10, 1360, 5),
            ("白色透明亞克力", 10, 1380, 4),
            ("合頁", 10, 1400, 4),
            ("磁吸", 10, 1420, 4),
            ("把手", 10, 1440, 4),
            ("角碼", 10, 1460, 4),
            ("加強筋焊接", 10, 1480, 4),
        ],
    },
}

# ---------------------------------------------------------------------------
# Pipeline runner
# ---------------------------------------------------------------------------

def _run_demo_pipeline(part_name: str, verbose: bool = False) -> dict:
    """Run the full 6-layer quotation pipeline for a demo part."""
    part = DEMO_PARTS.get(part_name)
    if not part:
        return {"error": f"Unknown part: {part_name}. Use: J003, W001"}

    # 1. Generate DXF
    doc = ezdxf.new()
    doc.header["$INSUNITS"] = 4
    msp = doc.modelspace()
    w, h = part["size"]
    msp.add_line((0, 0), (w, 0))
    msp.add_line((w, 0), (w, h))
    msp.add_line((w, h), (0, h))
    msp.add_line((0, h), (0, 0))
    for cx, cy, r in part["circles"]:
        msp.add_circle((cx, cy), radius=r)
    for content, x, y, height in part["texts"]:
        msp.add_text(content, height=height).set_placement((x, y))
    dxf_path = Path(f"demo_{part_name}.dxf")
    doc.saveas(str(dxf_path))

    # 2. CAD Import -> Drawing
    reader = DxfReader()
    import_result = reader.read(dxf_path)
    drawing = import_result.drawing

    # 3. Feature Extraction
    geo_ext = GeometricExtractor()
    geo = geo_ext.extract(drawing.raw_entities)

    mfg_ext = ManufacturingExtractor()
    mfg = mfg_ext.extract(geo)

    # 4. Quotation Mapping
    mapper = QuotationMapper()
    qf = mapper.map(mfg, geo)

    # 5. Pricing + Rule Engine
    try:
        resolver = PricingResolver()
    except FileNotFoundError as e:
        click.echo(f"  ERROR: {e}")
        return
    items = []
    for mq in qf.machining:
        items.extend(resolver.resolve_machining(mq))
    for fq in qf.frames:
        items.extend(resolver.resolve_frame(fq))
    for aq in qf.assemblies:
        items.extend(resolver.resolve_assembly(aq))

    # 6. Quote Builder
    builder = QuoteBuilder()
    # Get feature confidence from manufacturing
    feat_conf = mfg.material.confidence if mfg.material else None
    quote = builder.build(
        quote_id=f"Q-DEMO-{part_name}",
        drawing_id=f"DEMO-{part_name}",
        part_number=part["part_number"],
        part_name=part["part_name"],
        material=part["material"],
        items=items,
        feature_confidence=feat_conf,
        price_version=resolver.price_version,
        rule_version="1.0",
    )

    # Cleanup temp DXF
    dxf_path.unlink(missing_ok=True)

    return {
        "part_info": {
            "part_number": part["part_number"],
            "part_name": part["part_name"],
            "material": part["material"],
            "size_mm": part["size"],
        },
        "feature_summary": {
            "bbox": {
                "length": geo.bounding_box.length if geo.bounding_box else 0,
                "width": geo.bounding_box.width if geo.bounding_box else 0,
            },
            "hole_candidates": geo.candidate_count,
            "text_count": len(geo.text_clusters),
            "mfg_holes": mfg.total_holes,
            "mfg_threads": mfg.total_threads,
            "frames": len(mfg.frames),
            "assemblies": len(mfg.structure_assemblies),
            "accessories": len(mfg.structure_accessories),
            "welds": len(mfg.welds),
        },
        "quote_items": [
            {
                "category": i.category,
                "name": i.name,
                "amount": i.amount,
                "source": i.source.value,
                "evidence": i.evidence,
                "confidence": i.confidence.value,
            }
            for i in quote.items
        ],
        "total": quote.total,
        "source_summary": quote.source_summary,
        "quotation_status": quote.quotation_status,
        "overall_confidence": quote.overall_confidence,
        "confidence_reason": quote.confidence_reason,
        "unknown_count": quote.unknown_count,
        "price_version": quote.price_version,
        "rules_file": resolver.rules_file_name,
        "cost_completion": quote.cost_completion,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

@click.group(invoke_without_command=True)
@click.version_option(version=__version__, prog_name="quotation")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx: click.Context, verbose: bool) -> None:
    """Mechanical 2D Quotation System - Rule-driven quotation engine."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose
    if ctx.invoked_subcommand is None:
        click.echo(cli.get_help(ctx))


@cli.command()
@click.argument("part", type=click.Choice(["J003", "W001"]))
@click.option("--json", "-j", "output_json", is_flag=True, help="Output as JSON only")
@click.pass_context
def demo(ctx: click.Context, part: str, output_json: bool) -> None:
    """Run full quotation pipeline for a demo part.

    \b
    J003: S50C machined plate, 928x796x15, 4xM6, chrome plating
    W001: Aluminum profile guard frame, 1300x1300, with door assembly
    """
    click.echo(f"\n{'='*60}")
    click.echo(f"  Demo: {part} - Full Quotation Pipeline")
    click.echo(f"{'='*60}\n")

    result = _run_demo_pipeline(part, verbose=ctx.obj.get("verbose", False))

    if "error" in result:
        click.echo(f"  ERROR: {result['error']}")
        return

    if output_json:
        click.echo(json.dumps(result, ensure_ascii=False, indent=2))
        return

    # Part info
    pi = result["part_info"]
    click.echo(f"  Part:       {pi['part_number']} ({pi['part_name']})")
    click.echo(f"  Material:   {pi['material']}")
    click.echo(f"  Size:       {pi['size_mm'][0]}x{pi['size_mm'][1]}mm")

    # Feature summary
    fs = result["feature_summary"]
    click.echo(f"\n  --- Feature Summary ---")
    click.echo(f"  BoundingBox:   {fs['bbox']['length']:.0f}x{fs['bbox']['width']:.0f}mm")
    click.echo(f"  Holes:         {fs['mfg_holes']} (threads: {fs['mfg_threads']})")
    click.echo(f"  Frames:        {fs['frames']}")
    click.echo(f"  Assemblies:    {fs['assemblies']}")
    click.echo(f"  Accessories:   {fs['accessories']}")
    click.echo(f"  Text entities: {fs['text_count']}")

    # Quote items
    click.echo(f"\n  --- Quote Items ---")
    for i, item in enumerate(result["quote_items"], 1):
        source_label = {"C": "Company Rule", "E": "Industry Est", "H": "Historical", "U": "UNKNOWN"}
        sl = source_label.get(item["source"], item["source"])
        click.echo(f"  {i}. [{item['source']}] {item['name']}")
        click.echo(f"     Amount: {item['amount']:.2f}  |  Confidence: {item['confidence']}")
        if item.get("evidence"):
            ev = str(item['evidence']).replace('\xa5', 'CNY').replace('→', '->')
            click.echo(f"     Calc:   {ev}")

    # Summary
    click.echo(f"\n  --- Quote Summary ---")
    click.echo(f"  Total:        {result['total']:.2f} CNY")
    click.echo(f"  Status:       {result['quotation_status']}")
    click.echo(f"  Confidence:   {result['overall_confidence']:.0%} ({result['confidence_reason']})")
    click.echo(f"  Unknown:      {result['unknown_count']} items")
    click.echo(f"  Rules:        {result['price_version']} ({result.get('rules_file', '')})")

    # Benchmark comparison
    hist_price = DEMO_PARTS.get(part, {}).get("historical_price")
    if hist_price:
        dev = (result["total"] - hist_price) / hist_price * 100
        click.echo(f"\n  --- Benchmark ---")
        click.echo(f"  Historical:   {hist_price:.2f} CNY")
        click.echo(f"  System:       {result['total']:.2f} CNY")
        click.echo(f"  Deviation:    {dev:+.1f}%")

    # Unknown cost report
    unknowns = [i for i in result["quote_items"] if i["source"] == "U"]
    if unknowns:
        click.echo(f"\n  --- Unknown Cost Report ---")
        for u in unknowns:
            click.echo(f"  [U] {u['name']}: price not configured")

    # Cost completion
    cc = result.get("cost_completion", 100)
    click.echo(f"\n  Cost Completion: {cc:.0f}%")

    click.echo(f"\n{'='*60}\n")


@cli.command()
@click.argument("drawing_path", type=click.Path(exists=True))
@click.pass_context
def analyze(ctx: click.Context, drawing_path: str) -> None:
    """Analyze a DXF drawing and show entity summary."""
    reader = DxfReader()
    result = reader.read(drawing_path)
    if result.is_failed:
        click.echo(f"Error: {result.errors}")
        return
    d = result.drawing
    click.echo(f"File:    {d.file_name}")
    click.echo(f"Format:  {d.source_format.value}")
    click.echo(f"Unit:    {d.drawing_unit.value} ({d.unit_source or 'unknown'})")
    click.echo(f"Entities: {d.entity_count}")
    click.echo(f"Summary:  {d.entity_summary}")
    click.echo(f"Texts:   {d.raw_text_strings}")


@cli.command()
@click.argument("directory", type=click.Path(exists=True))
@click.pass_context
def batch(ctx: click.Context, directory: str) -> None:
    """Batch process all DXF/DWG files in a directory."""
    dxf_files = list(Path(directory).glob("*.dxf")) + list(Path(directory).glob("*.DXF"))
    click.echo(f"Found {len(dxf_files)} DXF files in {directory}")
    click.echo("Batch processing not yet implemented.")


@cli.command()
def version() -> None:
    """Show version information."""
    click.echo(f"Mechanical Quotation System v{__version__}")


if __name__ == "__main__":
    sys.exit(cli())
