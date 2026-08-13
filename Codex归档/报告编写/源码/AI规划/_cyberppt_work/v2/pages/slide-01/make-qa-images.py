from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(r"C:\Users\lfaf-test\Documents\报告编写\AI规划\_cyberppt_work\v2")
BLUEPRINT = ROOT / "blueprints" / "slide-01.png"
RENDER = ROOT / "pages" / "slide-01" / "render" / "slide-01.png"
OUT = ROOT / "pages" / "slide-01" / "qa"
OUT.mkdir(parents=True, exist_ok=True)

bp = Image.open(BLUEPRINT).convert("RGB")
rd = Image.open(RENDER).convert("RGB").resize(bp.size, Image.Resampling.LANCZOS)

gap = 24
canvas = Image.new("RGB", (bp.width * 2 + gap, bp.height + 46), "#F7F6F0")
canvas.paste(bp, (0, 46))
canvas.paste(rd, (bp.width + gap, 46))
draw = ImageDraw.Draw(canvas)
draw.text((18, 14), "BLUEPRINT", fill="#12355B")
draw.text((bp.width + gap + 18, 14), "POWERPOINT RENDER", fill="#12355B")
canvas.save(OUT / "slide-01-side-by-side.png")

crops = {
    "title": (55, 265, 825, 625),
    "framework": (825, 130, 1640, 805),
    "footer": (25, 850, 1640, 928),
}

for name, box in crops.items():
    left = bp.crop(box)
    right = rd.crop(box)
    crop_canvas = Image.new("RGB", (left.width * 2 + gap, left.height), "#F7F6F0")
    crop_canvas.paste(left, (0, 0))
    crop_canvas.paste(right, (left.width + gap, 0))
    crop_canvas.save(OUT / f"slide-01-{name}-crop-comparison.png")

print(OUT / "slide-01-side-by-side.png")
