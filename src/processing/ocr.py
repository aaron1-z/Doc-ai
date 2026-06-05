"""OCR extraction using Tesseract."""

from __future__ import annotations

import io
from dataclasses import dataclass

import pytesseract
from PIL import Image

from src.config import Settings
from src.exceptions import DocumentProcessingError
from src.logging_config import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class OcrResult:
    text: str
    confidence: float


class OcrEngine:
    """Run Tesseract OCR on images with confidence estimation."""

    def __init__(self, settings: Settings) -> None:
        self._language = settings.ocr_language
        self._min_confidence = settings.ocr_confidence_threshold
        if settings.tesseract_cmd:
            pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd

    def extract_from_bytes(self, image_bytes: bytes, page_number: int = 1) -> OcrResult:
        """OCR an image provided as PNG/JPEG bytes."""
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode not in ("RGB", "L"):
                image = image.convert("RGB")
            return self.extract_from_image(image, page_number=page_number)
        except DocumentProcessingError:
            raise
        except Exception as exc:
            logger.exception("OCR failed for page %s", page_number)
            raise DocumentProcessingError(f"OCR failed on page {page_number}") from exc

    def extract_from_image(self, image: Image.Image, page_number: int = 1) -> OcrResult:
        """OCR a PIL image and return text with mean word confidence."""
        try:
            text = pytesseract.image_to_string(image, lang=self._language).strip()
            data = pytesseract.image_to_data(
                image,
                lang=self._language,
                output_type=pytesseract.Output.DICT,
            )
            confidences = [
                float(conf) / 100.0
                for conf, word in zip(data["conf"], data["text"], strict=True)
                if str(word).strip() and int(conf) >= 0
            ]
            confidence = sum(confidences) / len(confidences) if confidences else 0.0
            if confidence < self._min_confidence and text:
                logger.warning(
                    "Low OCR confidence on page %s: %.2f",
                    page_number,
                    confidence,
                )
            return OcrResult(text=text, confidence=confidence)
        except DocumentProcessingError:
            raise
        except Exception as exc:
            logger.exception("Tesseract error on page %s", page_number)
            raise DocumentProcessingError(
                f"Tesseract OCR failed on page {page_number}. "
                "Ensure Tesseract is installed and TESSERACT_CMD is set if needed."
            ) from exc
