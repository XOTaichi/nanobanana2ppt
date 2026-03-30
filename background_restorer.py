from __future__ import annotations

import base64
import io
import re
from pathlib import Path
from typing import Any

import requests
from PIL import Image

from background_restore_prompt import build_background_restore_prompt
from path_utils import load_manifest, resolve_local_path, save_manifest


def image_to_data_url(image: Image.Image) -> str:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return f"data:image/png;base64,{base64.b64encode(buffer.getvalue()).decode('utf-8')}"


def normalize_openrouter_url(base_url: str) -> str:
    return base_url if base_url.endswith("/chat/completions") else base_url.rstrip("/") + "/chat/completions"


def parse_image_from_result(result: dict[str, Any]) -> Image.Image:
    message = (result.get("choices") or [{}])[0].get("message", {})
    candidates: list[Any] = []
    for key in ("images",):
        value = message.get(key)
        if isinstance(value, list):
            candidates.extend(value)
    content = message.get("content")
    if isinstance(content, list):
        candidates.extend(content)
    elif isinstance(content, str):
        candidates.extend(re.findall(r"data:image/[^;]+;base64,[A-Za-z0-9+/=\s]+", content))
    top_images = result.get("images")
    if isinstance(top_images, list):
        candidates.extend(top_images)
    for item in candidates:
        image = parse_image_candidate(item)
        if image is not None:
            return image
    raise RuntimeError("OpenRouter returned success but no parseable image payload.")


def parse_image_candidate(candidate: Any) -> Image.Image | None:
    if isinstance(candidate, dict):
        for key in ("b64_json", "base64", "data"):
            if isinstance(candidate.get(key), str):
                return decode_base64_image(candidate[key])
        for key in ("image_url", "url"):
            nested = candidate.get(key)
            if isinstance(nested, str):
                return parse_image_candidate(nested)
            if isinstance(nested, dict):
                return parse_image_candidate(nested.get("url"))
        return None
    if not isinstance(candidate, str):
        return None
    text = candidate.strip()
    if text.startswith("data:image/"):
        return decode_base64_image(text.split(",", 1)[1])
    if text.startswith("http://") or text.startswith("https://"):
        resp = requests.get(text, timeout=120)
        if resp.status_code == 200 and resp.content:
            image = Image.open(io.BytesIO(resp.content))
            image.load()
            return image
        return None
    return decode_base64_image(text)


def decode_base64_image(image_b64: str) -> Image.Image | None:
    try:
        clean = re.sub(r"\s+", "", image_b64)
        clean += "=" * ((4 - len(clean) % 4) % 4)
        image = Image.open(io.BytesIO(base64.b64decode(clean)))
        image.load()
        return image
    except Exception:
        return None


def restore_background(
    manifest_path: Path,
    output_path: Path,
    api_key: str,
    api_base: str,
    model: str,
    resolution: str,
    aspect_ratio: str | None,
) -> Path:
    manifest = load_manifest(manifest_path)
    masked_path = resolve_local_path(manifest_path.parent, manifest.get("artifacts", {}).get("masked_preview"))
    original_path = resolve_local_path(manifest_path.parent, manifest.get("input_image"))
    if masked_path is None or original_path is None:
        raise RuntimeError("Missing masked preview or input image referenced by manifest.")
    masked = Image.open(masked_path).convert("RGB")
    original = Image.open(original_path).convert("RGB")
    width, height = original.size
    prompt = (
        "Strict instruction: perform color-and-container inpainting only.\n"
        "The masked white regions must be restored as background or container fill only.\n"
        "Do not reproduce any text or symbols from the reference image.\n"
        f"{build_background_restore_prompt()}\n"
        f"Aspect ratio target: {aspect_ratio or f'{width}:{height}'}.\n"
        f"Resolution target: {resolution.upper()}.\n"
        "Use the first reference image as the masked preview and the second reference image as the original page.\n"
        "Return one edited image."
    )
    response = requests.post(
        normalize_openrouter_url(api_base),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://localhost",
            "X-Title": "image2ppt",
        },
        json={
            "model": model.split("#", 1)[0].strip(),
            "messages": [{"role": "user", "content": [{"type": "text", "text": prompt}, {"type": "image_url", "image_url": {"url": image_to_data_url(masked)}}, {"type": "image_url", "image_url": {"url": image_to_data_url(original)}}]}],
            "modalities": ["image"],
            "stream": False,
        },
        timeout=300,
    )
    if response.status_code != 200:
        raise RuntimeError(f"OpenRouter API error: status={response.status_code}, body={response.text[:500]!r}")
    restored = Image.open(io.BytesIO(response.content)) if response.headers.get("content-type", "").startswith("image/") else parse_image_from_result(response.json())
    output_path.parent.mkdir(parents=True, exist_ok=True)
    restored.save(output_path)
    manifest.setdefault("artifacts", {})["restored_background"] = str(output_path)
    save_manifest(manifest_path, manifest)
    return output_path

