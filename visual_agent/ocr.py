from __future__ import annotations

from dataclasses import dataclass

import pytesseract
from PIL import Image


@dataclass(frozen=True)
class OCRResult:
    text: str


def ocr_image(img: Image.Image, lang: str = "eng") -> OCRResult:
    # Note: requires the `tesseract` binary installed on the OS.
    txt = pytesseract.image_to_string(img, lang=lang) or ""
    # Normalize whitespace a bit for easier downstream matching.
    txt = " ".join(txt.split())
    return OCRResult(text=txt)

