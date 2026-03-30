from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from background_remover import BriaRMBG2Remover
from baidu_ocr_client import detect_text_elements
from data_models import ElementRecord
from sam3_client import detect_visual_elements


def save_crops(
    image: Image.Image,
    elements: list[ElementRecord],
    crops_dir: Path,
    remove_bg: bool,
    rmbg_model_path: Path | None,
    crop_padding_px: int = 1,
) -> None:
    crops_dir.mkdir(parents=True, exist_ok=True)
    remover = BriaRMBG2Remover(rmbg_model_path, crops_dir / "transparent") if remove_bg else None
    for record in elements:
        x0, y0, x1, y1 = record.bbox
        box = (max(0, x0 - crop_padding_px), max(0, y0 - crop_padding_px), min(image.width, x1 + crop_padding_px), min(image.height, y1 + crop_padding_px))
        crop = image.crop(box)
        crop_path = crops_dir / f"{record.id}.png"
        crop.save(crop_path)
        record.crop_path = str(crop_path)
        if remover and record.element_type == "visual":
            record.nobg_path = remover.remove_background(crop, record.id)


def background_fill(image: Image.Image) -> tuple[int, int, int]:
    rgb = image.convert("RGB")
    pixels = [rgb.getpixel((x, 0)) for x in range(rgb.width)] + [rgb.getpixel((x, rgb.height - 1)) for x in range(rgb.width)]
    pixels += [rgb.getpixel((0, y)) for y in range(rgb.height)] + [rgb.getpixel((rgb.width - 1, y)) for y in range(rgb.height)]
    pixels.sort()
    return pixels[len(pixels) // 2]


def save_mask_artifacts(image: Image.Image, elements: list[ElementRecord], output_dir: Path) -> None:
    mask = Image.new("L", image.size, 0)
    draw_mask = ImageDraw.Draw(mask)
    for record in elements:
        draw_mask.rectangle(record.bbox, fill=255)
    mask.save(output_dir / "mask.png")
    preview = image.convert("RGB").copy()
    draw_preview = ImageDraw.Draw(preview)
    fill = background_fill(image)
    for record in elements:
        draw_preview.rectangle(record.bbox, fill=fill)
    preview.save(output_dir / "masked_preview.png")


def save_overlay(image: Image.Image, elements: list[ElementRecord], output_dir: Path) -> None:
    overlay = image.convert("RGB").copy()
    draw = ImageDraw.Draw(overlay)
    for record in elements:
        color = (235, 87, 87) if record.element_type == "visual" else (47, 128, 237)
        label = record.id if record.element_type == "visual" else f'{record.id}:{record.text or ""}'
        draw.rectangle(record.bbox, outline=color, width=3)
        draw.text((record.bbox[0] + 4, max(0, record.bbox[1] - 14)), label[:40], fill=color)
    overlay.save(output_dir / "overlay.png")


def save_extraction_manifest(
    image_path: Path,
    image: Image.Image,
    output_dir: Path,
    prompts: list[str],
    visual_elements: list[ElementRecord],
    text_elements: list[ElementRecord],
) -> Path:
    manifest = {
        "input_image": str(image_path),
        "image_size": {"width": image.width, "height": image.height},
        "sam_prompts": prompts,
        "elements": [item.to_dict() for item in [*visual_elements, *text_elements]],
        "counts": {"visual": len(visual_elements), "text": len(text_elements), "total": len(visual_elements) + len(text_elements)},
        "artifacts": {
            "overlay": str(output_dir / "overlay.png"),
            "mask": str(output_dir / "mask.png"),
            "masked_preview": str(output_dir / "masked_preview.png"),
            "restored_background": None,
        },
    }
    manifest_path = output_dir / "manifest.json"
    manifest_path.write_text(__import__("json").dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest_path


def extract_elements(
    image_path: Path,
    output_dir: Path,
    prompts: list[str],
    sam_api_key: str,
    ocr_api_key: str,
    sam_threshold: float,
    remove_bg: bool,
    text_only_mask: bool,
    rmbg_model_path: Path | None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(image_path).convert("RGB")
    visual_elements = detect_visual_elements(image, prompts, sam_api_key, sam_threshold)
    text_elements = detect_text_elements(image_path, ocr_api_key)
    all_elements = [*visual_elements, *text_elements]
    mask_elements = text_elements if text_only_mask else all_elements
    save_crops(image, all_elements, output_dir / "crops", remove_bg, rmbg_model_path)
    save_overlay(image, all_elements, output_dir)
    save_mask_artifacts(image, mask_elements, output_dir)
    return save_extraction_manifest(image_path, image, output_dir, prompts, visual_elements, text_elements)

