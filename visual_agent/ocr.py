from __future__ import annotations

from dataclasses import dataclass
import os
import sys
from pathlib import Path

import pytesseract
from PIL import Image


@dataclass(frozen=True)
class OCRResult:
    text: str


def _find_tesseract_windows() -> str | None:
    """Try to find tesseract.exe in common Windows installation locations."""
    if sys.platform != "win32":
        return None
    
    common_paths = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expanduser(r"~\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"),
    ]
    
    for path in common_paths:
        if Path(path).exists():
            return path
    
    return None


def _setup_tesseract_cmd() -> None:
    """Configure pytesseract with tesseract executable path."""
    # Check if already configured
    if pytesseract.pytesseract.tesseract_cmd:
        return
    
    # First, check environment variable
    tcmd = os.environ.get("TESSERACT_CMD")
    if tcmd and Path(tcmd).exists():
        pytesseract.pytesseract.tesseract_cmd = tcmd
        return
    
    # On Windows, try to auto-detect
    if sys.platform == "win32":
        detected = _find_tesseract_windows()
        if detected:
            pytesseract.pytesseract.tesseract_cmd = detected
            return
    
    # If still not found, pytesseract will try PATH
    # We'll catch the error below if it fails


def ocr_image(img: Image.Image, lang: str = "eng") -> OCRResult:
    """Extract text from an image using OCR."""
    # Setup tesseract command path
    _setup_tesseract_cmd()
    
    try:
        # Note: requires the `tesseract` binary installed on the OS.
        txt = pytesseract.image_to_string(img, lang=lang) or ""
    except FileNotFoundError:
        raise RuntimeError(
            "Tesseract OCR not found. Please install Tesseract:\n"
            "  Windows: winget install --id UB-Mannheim.TesseractOCR -e\n"
            "  Or set TESSERACT_CMD environment variable to the tesseract.exe path"
        ) from None
    except PermissionError as e:
        tcmd = pytesseract.pytesseract.tesseract_cmd or os.environ.get("TESSERACT_CMD", "tesseract (from PATH)")
        raise RuntimeError(
            f"Permission denied when trying to run Tesseract at: {tcmd}\n"
            "This may be due to:\n"
            "  1. Antivirus/security software blocking the executable\n"
            "  2. Incorrect file permissions\n"
            "  3. Tesseract installation is corrupted\n"
            "Try running as administrator or check your security software settings."
        ) from e
    except Exception as e:
        raise RuntimeError(
            f"OCR failed: {e}\n"
            "Make sure Tesseract OCR is installed and accessible."
        ) from e
    
    # Normalize whitespace a bit for easier downstream matching.
    txt = " ".join(txt.split())
    return OCRResult(text=txt)

