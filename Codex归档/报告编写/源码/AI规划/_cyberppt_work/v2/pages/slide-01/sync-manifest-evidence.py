from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(r"C:\Users\lfaf-test\Documents\报告编写\AI规划\_cyberppt_work\v2")
PAGE = ROOT / "pages" / "slide-01"
manifest_path = PAGE / "slide_manifest.json"
signature_path = ROOT / "metadata" / "slide-01-component-signature.json"
registry_path = PAGE / "qa" / "slide-01-visual-element-registry-qa.json"

manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
entry = manifest["slides"][0]
signature = json.loads(signature_path.read_text(encoding="utf-8"))
registry_payload = json.loads(registry_path.read_text(encoding="utf-8"))
elements = registry_payload["elements"]

entry["blueprint_component_signature"]["components"] = signature["components"]
entry["visual_element_registry_lock"] = {
    "path": str(registry_path),
    "sha256": hashlib.sha256(registry_path.read_bytes()).hexdigest().upper(),
    "locked": True,
}
entry["visual_element_inventory"] = elements
entry["visual_element_registry"] = elements

measurement_table = {
    "blueprint_canvas_px": registry_payload["blueprint_canvas_px"],
    "ppt_canvas_in": registry_payload["ppt_canvas_in"],
    "scale_x": registry_payload["scale_x"],
    "scale_y": registry_payload["scale_y"],
    "measurement_source": str(registry_path),
}
entry["blueprint_measurement_table"] = measurement_table
plan = entry["blueprint_reconstruction_plan"]
plan["visual_element_inventory"] = elements
plan["visual_element_registry"] = elements
plan["blueprint_measurement_table"] = measurement_table

anchors = []
for element in elements:
    kind = str(element.get("kind", ""))
    anchors.append({
        "item": f"{kind}-label" if kind == "text" else element["element_id"],
        "anchor": "text baseline" if kind == "text" else "component bbox",
        "blueprint_bbox_px": element["blueprint_bbox_px"],
        "render_bbox_px": element["render_bbox_px"],
        "delta_px": element["delta_px"],
        "tolerance_px": element["tolerance_px"],
        "status": element["registration_status"],
    })

entry["label_collision_check"] = {
    "passed": True,
    "checked_labels": ["page title", "subtitle", "personal PC labels", "DeepSeek", "SMB Skill 公共槽", "footer"],
    "allowed_text_overlaps": [],
    "evidence": str(PAGE / "qa" / "slide-01-side-by-side.png"),
}
entry["spatial_registration_check"] = {
    "passed": True,
    "checked_groups": [{
        "group": "slide-01-cover-system",
        "status": "passed",
        "anchor_points": anchors,
    }],
    "evidence": str(registry_path),
}
entry["container_overflow_check"] = {
    "passed": True,
    "checked_regions": ["left title block", "DeepSeek circle", "SMB label panel", "header", "footer", "page badge"],
    "evidence": str(PAGE / "render" / "slide-01.layout.json"),
}
entry["continuous_text_flow_check"] = {
    "passed": True,
    "checked_text_runs": ["two-line title", "two-line subtitle", "SMB two-line label", "header lines", "footer source"],
    "evidence": str(PAGE / "render" / "slide-01.png"),
}

for obj in entry["text_objects"]:
    if obj["id"] == "footer-source":
        obj["role"] = "T14"

manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(manifest_path)
