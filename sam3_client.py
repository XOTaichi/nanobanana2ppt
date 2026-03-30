from __future__ import annotations

import base64
import io
import os
from typing import Any

import requests
from PIL import Image

from data_models import ElementRecord


SAM3_API_URL = os.environ.get("ROBOFLOW_API_URL", "https://serverless.roboflow.com/sam3/concept_segment")


def image_to_base64(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def polygon_to_bbox(points: list[Any], width: int, height: int) -> list[int] | None:
    xs: list[float] = []
    ys: list[float] = []
    for point in points:
        if not isinstance(point, (list, tuple)) or len(point) < 2:
            continue
        x = float(point[0])
        y = float(point[1])
        if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
            x *= width
            y *= height
        xs.append(x)
        ys.append(y)
    if not xs or not ys:
        return None
    bbox = [max(0, int(min(xs))), max(0, int(min(ys))), min(width, int(max(xs))), min(height, int(max(ys)))]
    return bbox if bbox[2] > bbox[0] and bbox[3] > bbox[1] else None


def extract_detections(response_json: dict[str, Any], image_size: tuple[int, int]) -> list[dict[str, Any]]:
    width, height = image_size
    detections: list[dict[str, Any]] = []
    for prompt_result in response_json.get("prompt_results", []):
        if not isinstance(prompt_result, dict):
            continue
        for prediction in prompt_result.get("predictions", []):
            confidence = prediction.get("confidence")
            for mask in prediction.get("masks", []):
                points = flatten_points(mask)
                bbox = polygon_to_bbox(points, width, height)
                if bbox is not None:
                    detections.append({"bbox": bbox, "score": float(confidence) if confidence is not None else None})
    return detections


def flatten_points(mask: Any) -> list[Any]:
    if not isinstance(mask, list) or not mask:
        return []
    if isinstance(mask[0], (list, tuple)) and len(mask[0]) >= 2 and isinstance(mask[0][0], (int, float)):
        return list(mask)
    points: list[Any] = []
    for item in mask:
        if isinstance(item, (list, tuple)) and item and isinstance(item[0], (list, tuple)):
            points.extend(item)
    return points


def call_sam3(image_base64: str, prompt: str, api_key: str, min_score: float) -> dict[str, Any]:
    response = requests.post(
        f"{SAM3_API_URL}?api_key={api_key}",
        json={
            "image": {"type": "base64", "value": image_base64},
            "prompts": [{"type": "text", "text": prompt}],
            "format": "polygon",
            "output_prob_thresh": min_score,
        },
        timeout=120,
    )
    response.raise_for_status()
    return response.json()


def bbox_iou(a: list[int], b: list[int]) -> float:
    ix0, iy0 = max(a[0], b[0]), max(a[1], b[1])
    ix1, iy1 = min(a[2], b[2]), min(a[3], b[3])
    if ix1 <= ix0 or iy1 <= iy0:
        return 0.0
    inter = (ix1 - ix0) * (iy1 - iy0)
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def dedupe_boxes(detections: list[dict[str, Any]], iou_threshold: float = 0.6) -> list[dict[str, Any]]:
    ordered = sorted(
        detections,
        key=lambda item: (float(item.get("score") or 0.0), (item["bbox"][2] - item["bbox"][0]) * (item["bbox"][3] - item["bbox"][1])),
        reverse=True,
    )
    kept: list[dict[str, Any]] = []
    for item in ordered:
        if any(bbox_iou(item["bbox"], other["bbox"]) >= iou_threshold for other in kept):
            continue
        kept.append(item)
    return kept


def detect_visual_elements(image: Image.Image, prompts: list[str], api_key: str, min_score: float) -> list[ElementRecord]:
    image_base64 = image_to_base64(image)
    detections: list[dict[str, Any]] = []
    for prompt in prompts:
        response_json = call_sam3(image_base64, prompt, api_key, min_score)
        for idx, item in enumerate(extract_detections(response_json, image.size), start=1):
            detections.append({**item, "prompt": prompt, "metadata": {"raw_index": idx}})
    records: list[ElementRecord] = []
    for idx, item in enumerate(dedupe_boxes(detections), start=1):
        records.append(
            ElementRecord(
                id=f"visual_{idx:03d}",
                element_type="visual",
                source="sam3",
                bbox=item["bbox"],
                score=item.get("score"),
                prompt=item.get("prompt"),
                metadata=item.get("metadata", {}),
            )
        )
    return records

