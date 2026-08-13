from pathlib import Path
from PIL import Image, ImageDraw

root = Path(r"C:\Users\lfaf-test\Documents\报告编写\AI规划\_cyberppt_work\v2\final-render")
images = [Image.open(root / f"slide-{i:02d}.png").convert("RGB") for i in range(1, 8)]
thumb_w, thumb_h = 480, 270
gap, label_h = 18, 28
sheet = Image.new("RGB", (thumb_w * 2 + gap * 3, (thumb_h + label_h) * 4 + gap * 5), "#E9EDF2")
draw = ImageDraw.Draw(sheet)
for idx, im in enumerate(images):
    r, c = divmod(idx, 2)
    x = gap + c * (thumb_w + gap)
    y = gap + r * (thumb_h + label_h + gap)
    sheet.paste(im.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS), (x, y + label_h))
    draw.text((x, y + 5), f"SLIDE {idx + 1:02d}", fill="#12355B")
sheet.save(root / "contact-sheet.png")
print(root / "contact-sheet.png")
