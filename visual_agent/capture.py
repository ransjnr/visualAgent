from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable

import mss
from PIL import Image, ImageFilter, ImageOps


@dataclass(frozen=True)
class Frame:
    image: Image.Image
    captured_at: datetime


def capture_primary_monitor() -> Frame:
    with mss.mss() as sct:
        mon = sct.monitors[1]  # 0 is "all", 1 is primary
        shot = sct.grab(mon)
        img = Image.frombytes("RGB", shot.size, shot.rgb)
        return Frame(image=img, captured_at=datetime.utcnow())


def redact_rects(img: Image.Image, rects: Iterable[Iterable[int]]) -> Image.Image:
    """
    Redacts rectangular regions by blurring + grayscale.
    rect is (x, y, w, h).
    """
    out = img.copy()
    for r in rects:
        x, y, w, h = [int(v) for v in r]
        if w <= 0 or h <= 0:
            continue
        crop = out.crop((x, y, x + w, y + h))
        crop = ImageOps.grayscale(crop).filter(ImageFilter.GaussianBlur(radius=8))
        out.paste(crop.convert("RGB"), (x, y))
    return out


def maybe_save_debug_frame(img: Image.Image, enabled: bool, out_dir: str) -> None:
    if not enabled:
        return
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S_%f")
    img.save(str(Path(out_dir) / f"frame_{ts}.png"))

