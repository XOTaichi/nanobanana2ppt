from __future__ import annotations

from pathlib import Path

from PIL import Image
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN


DEFAULT_DPI = 96


def pixels_to_inches(px: float, dpi: int = DEFAULT_DPI) -> float:
    return px / dpi


def estimate_font_size(bbox: list[int]) -> float:
    return max(8.0, min(32.0, max(1, bbox[3] - bbox[1]) * 0.42))


def infer_alignment(text: str, bbox: list[int]) -> PP_ALIGN:
    return PP_ALIGN.CENTER if len(text.strip()) <= 12 and bbox[2] - bbox[0] > 160 else PP_ALIGN.LEFT


def pick_text_color(crop_path: Path) -> RGBColor:
    try:
        pixels = list(Image.open(crop_path).convert("RGB").getdata())
        filtered = [pixel for pixel in pixels if sum(pixel) < 720]
        if not filtered:
            return RGBColor(60, 45, 30)
        filtered.sort(key=sum)
        r, g, b = filtered[max(0, len(filtered) // 10 - 1)]
        return RGBColor(int(r), int(g), int(b))
    except Exception:
        return RGBColor(60, 45, 30)

