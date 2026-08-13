from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from pathlib import Path

ROOT = Path(r"C:\Users\lfaf-test\Documents\报告编写\AI规划\_cyberppt_work\v2")
PAGE = ROOT / "pages" / "slide-01"
QA = PAGE / "qa"
QA.mkdir(parents=True, exist_ok=True)

registry_path = ROOT / "metadata" / "slide-01-visual-element-registry.json"
layout_path = PAGE / "render" / "slide-01.layout.json"
signature_path = ROOT / "metadata" / "slide-01-component-signature.json"
object_report_path = QA / "pptx-object-report.json"

registry = json.loads(registry_path.read_text(encoding="utf-8"))
layout = json.loads(layout_path.read_text(encoding="utf-8"))
signature = json.loads(signature_path.read_text(encoding="utf-8"))
object_report = json.loads(object_report_path.read_text(encoding="utf-8"))

objects: dict[str, list[float]] = {}

def visit(value):
    if isinstance(value, dict):
        bbox = value.get("bbox")
        name = value.get("name") or value.get("alt")
        if name and isinstance(bbox, list) and len(bbox) == 4:
            objects[str(name)] = [float(v) for v in bbox]
        for child in value.values():
            visit(child)
    elif isinstance(value, list):
        for child in value:
            visit(child)

visit(layout)

mapping = {
    "header-left": "header-left",
    "header-right": "header-right",
    "header-rule": "header-rule",
    "main-title": "page-title",
    "subtitle": "subtitle",
    "accent-rule": "title-accent",
    "report-date": "report-date",
    "pc-1": "pc-group-1",
    "pc-2": "pc-group-2",
    "pc-3": "pc-group-3",
    "pc-connectors": "pc-connectors-group",
    "deepseek-core": "deepseek-group",
    "smb-share": "smb-group",
    "framework-orbit": "orbit-group",
    "robot-arm": "robot-group",
    "plc-gears": "plc-gears-group",
    "footer-rule": "footer-rule",
    "footer-source": "footer-source",
    "page-number": "page-badge",
}

component_map = {
    "header-left": "header", "header-right": "header", "header-rule": "header",
    "main-title": "title-block", "subtitle": "title-block", "accent-rule": "title-block", "report-date": "title-block",
    "pc-1": "framework-hero", "pc-2": "framework-hero", "pc-3": "framework-hero",
    "pc-connectors": "framework-hero", "deepseek-core": "framework-hero", "smb-share": "framework-hero",
    "framework-orbit": "technical-decoration", "robot-arm": "technical-decoration", "plc-gears": "technical-decoration",
    "footer-rule": "footer", "footer-source": "footer", "page-number": "footer",
}

role_map = {
    "main-title": "title", "subtitle": "subtitle", "deepseek-core": "main_visual", "smb-share": "main_visual",
    "footer-source": "source", "page-number": "page_number",
}

sx = registry["blueprint_canvas_px"]["w"] / 1280
sy = registry["blueprint_canvas_px"]["h"] / 720
registered = deepcopy(registry)
failures = []

for element in registered["elements"]:
    element_id = element["id"]
    element["element_id"] = element_id
    element["element_type"] = element.get("kind", "visual_element")
    element["source_component_id"] = component_map[element_id]
    element["role"] = role_map.get(element_id, "decoration" if element.get("priority") == "P2" else "supporting_visual")
    if element_id == "footer-source":
        element["priority"] = "P0"
    if element["priority"] in {"P0", "P1"}:
        element["measurement_mode"] = "individual_bbox"
    else:
        element["measurement_mode"] = "decoration_group"
        element["group_bbox_px"] = element["blueprint_bbox_px"]
        element["color"] = "#12355B"
        element["spacing_px"] = 0
        element["alignment"] = "blueprint-aligned"
        element["repeat_direction"] = "none"
        element["opacity"] = 1
        element["reproduction_strategy"] = "native-shape-or-approved-tabler-icon"
        element["count"] = 1
    layout_name = mapping[element_id]
    bbox = objects.get(layout_name)
    if not bbox:
        failures.append({"element_id": element_id, "code": "LAYOUT_OBJECT_MISSING"})
        continue
    render_bbox = {
        "x": round(bbox[0] * sx, 2),
        "y": round(bbox[1] * sy, 2),
        "w": round(bbox[2] * sx, 2),
        "h": round(bbox[3] * sy, 2),
    }
    target = element["blueprint_bbox_px"]
    delta = {k: round(render_bbox[k] - float(target[k]), 2) for k in ("x", "y", "w", "h")}
    element["render_bbox_px"] = render_bbox
    element["delta_px"] = delta
    tolerance = float(element["tolerance_px"])
    passed = all(abs(v) <= tolerance for v in delta.values())
    element["registration_status"] = "passed" if passed else "failed"
    kind = str(element.get("kind", ""))
    if kind in {"text", "page-number"}:
        element["pixel_mean_abs_tolerance"] = 125
    elif "decorative" in kind:
        element["pixel_mean_abs_tolerance"] = 125
    elif kind == "line":
        element["pixel_mean_abs_tolerance"] = 110
    elif kind in {"node", "connectors"}:
        element["pixel_mean_abs_tolerance"] = 95
    else:
        element["pixel_mean_abs_tolerance"] = 60
    if not passed:
        failures.append({"element_id": element_id, "code": "BBOX_DELTA_EXCEEDED", "delta_px": delta, "tolerance_px": tolerance})

registered["render_registration"] = {
    "render_source": str(PAGE / "render" / "slide-01.png"),
    "layout_source": str(layout_path),
    "passed": not failures,
    "failures": failures,
}
qa_registry_path = QA / "slide-01-visual-element-registry-qa.json"
qa_registry_path.write_text(json.dumps(registered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

component_check = {
    "schema": "cyberppt.component_signature_check.v1",
    "slide": 1,
    "signature_path": str(signature_path),
    "signature_locked": signature.get("locked") is True,
    "expected_component_count": len(signature.get("components", [])),
    "pptx_object_report_path": str(object_report_path),
    "actual_shapes": object_report["slides"][0]["shapes"],
    "actual_pictures": object_report["slides"][0]["pictures"],
    "full_slide_pictures": object_report["slides"][0]["full_slide_pictures"],
    "passed": signature.get("locked") is True and not object_report.get("failures"),
}
component_check_path = QA / "component-signature-check.json"
component_check_path.write_text(json.dumps(component_check, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

print(json.dumps({
    "qa_registry": str(qa_registry_path),
    "registration_passed": not failures,
    "registration_failures": len(failures),
    "component_check": str(component_check_path),
}, ensure_ascii=False, indent=2))
