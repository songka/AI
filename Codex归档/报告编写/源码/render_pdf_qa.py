from pathlib import Path
import pypdfium2 as pdfium

pdf_path = Path(r"C:\Users\lfaf-test\Documents\报告编写\报告\_qa_render\自动化设备研发与交付流程梳理报告_word.pdf")
out_dir = pdf_path.parent
for old in out_dir.glob("final-page-*.png"):
    old.unlink()
pdf = pdfium.PdfDocument(str(pdf_path))
for index in range(len(pdf)):
    page = pdf[index]
    bitmap = page.render(scale=1.7)
    image = bitmap.to_pil()
    image.save(out_dir / f"final-page-{index + 1}.png")
print(len(pdf))
