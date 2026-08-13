"""Extract text from vector and scanned PDF drawings."""

from __future__ import annotations

import logging
import time
from functools import lru_cache
from pathlib import Path

from quotation.domain.drawing import Drawing, DrawingFormat, ParseStatus, TextEntity
from quotation.domain.import_result import ImportResult

logger = logging.getLogger("quotation.infrastructure.pdf.reader")


class PdfReader:
    """Read PDF files and extract text content locally."""

    MAX_OCR_PAGES = 30
    OCR_SCALE = 2.0

    def read(self, pdf_path: str | Path) -> ImportResult:
        """Read a PDF file.

        Returns ImportResult with pdf_confidence and extracted text.
        """
        path = Path(pdf_path)
        started = time.monotonic()

        result = ImportResult(
            source_file=str(path),
            source_format="PDF",
        )

        if not path.exists():
            result.import_status = "failed"
            result.errors.append(f"File not found: {path}")
            return result

        # Detect PDF type and extract
        try:
            pdf_type = self._detect_type(path)
            if pdf_type == "vector":
                texts = self._extract_text_vector(path)
                confidence = "high"
            elif pdf_type == "image":
                texts = self._extract_text_ocr(path)
                confidence = "low"
            else:  # mixed
                texts = self._extract_text_vector(path)
                confidence = "medium"

            # Build minimal Drawing
            drawing = Drawing(
                id=f"pdf-{path.stem}",
                file_path=str(path),
                file_name=path.name,
                source_format=DrawingFormat.PDF,
                entity_count=len(texts),
                all_texts=texts,
                raw_text_strings=[t.content for t in texts if t.content.strip()],
                parse_status=ParseStatus.PARTIAL,  # PDF is always partial (no geometry)
            )

            result.drawing = drawing
            result.pdf_confidence = confidence
            result.import_status = "success"

        except Exception as e:
            result.import_status = "failed"
            result.errors.append(f"PDF read error: {e}")

        result.import_duration_ms = (time.monotonic() - started) * 1000
        return result

    # -- Internal implementations --

    def _detect_type(self, path: Path) -> str:
        """Detect if PDF is vector, image, or mixed.

        A PDF without extractable vector text is treated as scanned artwork.
        """
        try:
            texts = self._extract_text_vector(path)
            return "vector" if texts else "image"
        except Exception:
            return "image"

    def _extract_text_vector(self, path: Path) -> list[TextEntity]:
        """Extract text from vector PDF.

        Uses pdfminer.six if available; otherwise basic PyPDF2 fallback.
        """
        texts: list[TextEntity] = []

        # Try pdfminer first (best for CJK)
        try:
            from pdfminer.high_level import extract_pages
            from pdfminer.layout import LTTextContainer

            for page in extract_pages(path):
                for element in page:
                    if isinstance(element, LTTextContainer):
                        content = element.get_text().strip()
                        if content:
                            texts.append(TextEntity(
                                content=content,
                                position_x=element.bbox[0] if hasattr(element, 'bbox') else 0,
                                position_y=element.bbox[1] if hasattr(element, 'bbox') else 0,
                                height=element.bbox[3] - element.bbox[1] if hasattr(element, 'bbox') else 10,
                                entity_type="TEXT",
                            ))
            return texts
        except ImportError:
            logger.debug("pdfminer not available, trying PyPDF2")
        except Exception as e:
            logger.warning("pdfminer extraction failed: %s", e)

        # Fallback: PyPDF2
        try:
            from PyPDF2 import PdfReader as PyPDFReader
            reader = PyPDFReader(str(path))
            for page in reader.pages:
                content = page.extract_text()
                if content:
                    for line in content.split("\n"):
                        line = line.strip()
                        if line:
                            texts.append(TextEntity(
                                content=line,
                                position_x=0, position_y=0, height=10,
                                entity_type="TEXT",
                            ))
        except ImportError:
            logger.warning("No PDF library available (install pdfminer.six or PyPDF2)")
        except Exception as e:
            logger.warning("PyPDF2 extraction failed: %s", e)

        return texts

    def _extract_text_ocr(self, path: Path) -> list[TextEntity]:
        """Render scanned pages and recognize text with the local RapidOCR engine."""
        try:
            import pymupdf
        except ImportError as exc:  # pragma: no cover - installation integrity guard
            raise RuntimeError("缺少扫描 PDF 渲染组件 PyMuPDF") from exc

        engine = _ocr_engine()
        texts: list[TextEntity] = []
        with pymupdf.open(path) as document:
            if document.page_count > self.MAX_OCR_PAGES:
                logger.warning(
                    "扫描 PDF 共 %d 页，仅识别前 %d 页",
                    document.page_count,
                    self.MAX_OCR_PAGES,
                )
            for page_number in range(min(document.page_count, self.MAX_OCR_PAGES)):
                page = document.load_page(page_number)
                pixmap = page.get_pixmap(
                    matrix=pymupdf.Matrix(self.OCR_SCALE, self.OCR_SCALE),
                    alpha=False,
                )
                result = engine(pixmap.tobytes("png"))
                if not result.txts:
                    continue
                boxes = result.boxes if result.boxes is not None else []
                for index, content in enumerate(result.txts):
                    content = content.strip()
                    if not content:
                        continue
                    box = boxes[index] if index < len(boxes) else None
                    if box is not None:
                        x_values = [float(point[0]) / self.OCR_SCALE for point in box]
                        y_values = [float(point[1]) / self.OCR_SCALE for point in box]
                        position_x = min(x_values)
                        position_y = page.rect.height - max(y_values)
                        height = max(max(y_values) - min(y_values), 1.0) / self.OCR_SCALE
                    else:
                        position_x = 0.0
                        position_y = 0.0
                        height = 10.0
                    texts.append(
                        TextEntity(
                            content=content,
                            position_x=position_x,
                            position_y=position_y,
                            height=height,
                            layer=f"PDF第{page_number + 1}页",
                            entity_type="OCR文字",
                        )
                    )
        return texts


@lru_cache(maxsize=1)
def _ocr_engine():
    """Create the local OCR model once per process."""
    try:
        from rapidocr import RapidOCR
    except ImportError as exc:  # pragma: no cover - installation integrity guard
        raise RuntimeError("缺少扫描 PDF 识别组件 RapidOCR") from exc
    return RapidOCR()
