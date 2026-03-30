from __future__ import annotations

import base64
import io
import urllib.parse
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from data_models import ElementRecord


class BaiduAccurateOCRClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.api_url = "https://aip.baidubce.com/rest/2.0/ocr/v1/accurate"

    def recognize(self, image_path: Path) -> dict[str, Any]:
        image_encoded, image_size = encode_image(image_path)
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }
        url = self.api_url
        if self.api_key.startswith("bce-v3/"):
            headers["Authorization"] = f"Bearer {self.api_key}"
        else:
            url = f"{self.api_url}?access_token={self.api_key}"
        data = urllib.parse.urlencode(
            {
                "image": image_encoded,
                "language_type": "CHN_ENG",
                "recognize_granularity": "big",
                "detect_direction": "false",
                "vertexes_location": "false",
                "paragraph": "false",
                "probability": "true",
                "multidirectional_recognize": "false",
            }
        )
        response = requests.post(url, headers=headers, data=data, timeout=60)
        response.raise_for_status()
        result = response.json()
        if "error_code" in result:
            raise RuntimeError(f'Baidu API error [{result.get("error_code")}]: {result.get("error_msg")}')
        return {
            "words_result_num": result.get("words_result_num", 0),
            "text_lines": build_text_lines(result.get("words_result", [])),
            "image_size": {"width": image_size[0], "height": image_size[1]},
        }


def encode_image(image_path: Path) -> tuple[str, tuple[int, int]]:
    with Image.open(image_path) as img:
        size = img.size
        if img.mode != "RGB":
            img = img.convert("RGB")
        width, height = img.size
        max_size = 8192
        if width > max_size or height > max_size:
            ratio = min(max_size / width, max_size / height)
            img = img.resize((int(width * ratio), int(height * ratio)), Image.Resampling.LANCZOS)
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=95)
    image_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return image_base64, size


def location_to_bbox(location: dict[str, int]) -> list[int]:
    left = int(location.get("left", 0))
    top = int(location.get("top", 0))
    width = int(location.get("width", 0))
    height = int(location.get("height", 0))
    return [left, top, left + width, top + height]


def build_text_lines(words_result: list[dict[str, Any]]) -> list[dict[str, Any]]:
    text_lines: list[dict[str, Any]] = []
    for line in words_result:
        location = line.get("location", {})
        text_lines.append(
            {
                "text": line.get("words", "").strip(),
                "bbox": location_to_bbox(location),
                "probability": line.get("probability"),
            }
        )
    return text_lines


def detect_text_elements(image_path: Path, api_key: str) -> list[ElementRecord]:
    result = BaiduAccurateOCRClient(api_key).recognize(image_path)
    records: list[ElementRecord] = []
    for idx, line in enumerate(result.get("text_lines", []), start=1):
        text = (line.get("text") or "").strip()
        bbox = line.get("bbox") or []
        if not text or len(bbox) != 4:
            continue
        prob = None
        probability = line.get("probability")
        if isinstance(probability, dict):
            prob = float(probability.get("average", 0.0))
        records.append(
            ElementRecord(
                id=f"text_{idx:03d}",
                element_type="text",
                source="baidu_ocr",
                bbox=[int(v) for v in bbox],
                score=prob,
                text=text,
            )
        )
    return records

