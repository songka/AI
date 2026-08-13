from pathlib import Path
from PIL import Image, ImageDraw

folder = Path(r"C:\Users\lfaf-test\Documents\报告编写\报告\_qa_render")
files = sorted(folder.glob("final-page-*.png"), key=lambda p: int(p.stem.split("-")[-1]))
thumb_w = 360
items = []
for f in files:
    im = Image.open(f).convert("RGB")
    scale = thumb_w / im.width
    im = im.resize((thumb_w, int(im.height * scale)))
    items.append((f.name, im))
cell_h = max(im.height for _, im in items) + 34
sheet = Image.new("RGB", (thumb_w * 2 + 30, cell_h * 5 + 30), "#d9dde3")
draw = ImageDraw.Draw(sheet)
for i, (name, im) in enumerate(items):
    x = 10 + (i % 2) * (thumb_w + 10)
    y = 10 + (i // 2) * cell_h
    sheet.paste(im, (x, y + 24))
    draw.text((x + 4, y + 4), name, fill="black")
sheet.save(folder / "final-contact-sheet.png")
