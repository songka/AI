"""PDF Reader — extracts text from vector/scanned PDF files.

Phase 3.0: Interface only. Vector PDF text extraction + image PDF placeholder.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path

from quotation.domain.drawing import Drawing, DrawingFormat, ParseStatus, TextEntity
from quotation.domain.import_result import ImportResult

logger = logging.getLogger("quotation.infrastructure.pdf.reader")


class PdfReader:
    """Read PDF files and extract text content.

    Phase 3.0: Basic interface with vector text extraction.
    OCR (image PDF) is a placeholder for Phase 3.3.
    """

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

    # -- Internal (Phase 3.0: basic implementations) --

    def _detect_type(self, path: Path) -> str:
        """Detect if PDF is vector, image, or mixed.

        Phase 3.0 heuristic: check if text can be extracted.
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
        """OCR text from image PDF. Placeholder for Phase 3.3."""
        logger.info("OCR not yet implemented for: %s", path)
        return []
