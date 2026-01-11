from __future__ import annotations

from dataclasses import dataclass

import pytesseract
from PIL import Image
import os


@dataclass(frozen=True)
class OCRResult:
    text: str


def ocr_image(img: Image.Image, lang: str = "eng") -> OCRResult:
    # Windows: allow explicitly pointing to tesseract.exe
    # Example: setx TESSERACT_CMD "C:\Program Files\Tesseract-OCR\tesseract.exe"
    tcmd = os.environ.get("TESSERACT_CMD")
    if tcmd:
        pytesseract.pytesseract.tesseract_cmd = tcmd

    # Note: requires the `tesseract` binary installed on the OS.
    txt = pytesseract.image_to_string(img, lang=lang) or ""
    # Normalize whitespace a bit for easier downstream matching.
    txt = " ".join(txt.split())
    return OCRResult(text=txt)

