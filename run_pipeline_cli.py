#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from artifact_builder import extract_elements
from env_utils import get_required_env, load_dotenv
from background_restorer import restore_background
from path_utils import manifest_default_dir
from ppt_exporter import export_ppt


BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the full image2ppt pipeline.")
    parser.add_argument("input_png", type=Path, help="Input PNG path")
    parser.add_argument("--output-dir", type=Path, default=BASE_DIR / "output", help="Base output directory")
    parser.add_argument("--dotenv", type=Path, default=BASE_DIR / ".env", help="Path to .env file")
    parser.add_argument("--sam-prompts", default="icon,arrow,diagram", help="Comma-separated SAM3 prompts")
    parser.add_argument("--sam-threshold", type=float, default=0.5)
    parser.add_argument("--sam-api-key", default=None)
    parser.add_argument("--ocr-api-key", default=None)
    parser.add_argument("--remove-bg", action="store_true")
    parser.add_argument("--rmbg-model-path", type=Path, default="model")
    parser.add_argument("--restore-background", action="store_true")
    parser.add_argument("--restore-output", type=Path, default=None)
    parser.add_argument("--aspect-ratio", default=None)
    parser.add_argument("--background", choices=["white", "restored"], default="restored")
    parser.add_argument("--disable-rmbg", action="store_true")
    parser.add_argument("--min-alpha-pixels", type=int, default=80)
    parser.add_argument("--min-alpha-ratio", type=float, default=0.08)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(args.dotenv)
    input_image = args.input_png.resolve()
    if not input_image.exists():
        print(f"Input image not found: {input_image}", file=sys.stderr)
        return 2
    output_dir = manifest_default_dir(input_image, args.output_dir.resolve())
    manifest_path = extract_elements(
        image_path=input_image,
        output_dir=output_dir,
        prompts=[item.strip() for item in args.sam_prompts.split(",") if item.strip()],
        sam_api_key=args.sam_api_key or os.environ.get("ROBOFLOW_API_KEY", ""),
        ocr_api_key=args.ocr_api_key or os.environ.get("BAIDU_API_KEY", ""),
        sam_threshold=args.sam_threshold,
        remove_bg=args.remove_bg,
        text_only_mask=False,
        rmbg_model_path=args.rmbg_model_path.resolve() if args.rmbg_model_path else None,
    )
    if args.restore_background:
        restore_background(
            manifest_path=manifest_path,
            output_path=args.restore_output.resolve() if args.restore_output else (manifest_path.parent / "restored_background.png").resolve(),
            api_key=get_required_env("IMAGE_API_KEY"),
            api_base=get_required_env("IMAGE_API_BASE"),
            model=get_required_env("IMAGE_MODEL"),
            resolution=os.environ.get("DEFAULT_RESOLUTION", "2K"),
            aspect_ratio=args.aspect_ratio,
        )
    ppt_path = export_ppt(
        manifest_path=manifest_path,
        output_pptx=manifest_path.parent / "overlay_editable.pptx",
        background_mode=args.background,
        text_only=False,
        use_rmbg=not args.disable_rmbg,
        rmbg_model_path=args.rmbg_model_path.resolve() if args.rmbg_model_path else None,
        min_alpha_pixels=args.min_alpha_pixels,
        min_alpha_ratio=args.min_alpha_ratio,
    )
    print(manifest_path)
    print(ppt_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

