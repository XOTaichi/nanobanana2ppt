#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from artifact_builder import extract_elements
from env_utils import load_dotenv
from path_utils import manifest_default_dir


BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract text and visual elements from an image.")
    parser.add_argument("input_png", type=Path, help="Input PNG path")
    parser.add_argument("--output-dir", type=Path, default=BASE_DIR / "output", help="Base output directory")
    parser.add_argument("--dotenv", type=Path, default=BASE_DIR / ".env", help="Path to .env file")
    parser.add_argument("--sam-prompts", default="icon,arrow,diagram,chart", help="Comma-separated SAM3 prompts")
    parser.add_argument("--sam-threshold", type=float, default=0.5)
    parser.add_argument("--sam-api-key", default=None)
    parser.add_argument("--ocr-api-key", default=None)
    parser.add_argument("--remove-bg", action="store_true", help="Run BRIA RMBG for visual crops")
    parser.add_argument("--text-only-mask", action="store_true", help="Only mask text elements in mask artifacts")
    parser.add_argument("--rmbg-model-path", type=Path, default=BASE_DIR / "model", help="Optional local RMBG model path")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(args.dotenv)
    image_path = args.input_png.resolve()
    if not image_path.exists():
        print(f"Input image not found: {image_path}", file=sys.stderr)
        return 2
    sam_api_key = args.sam_api_key or os.environ.get("ROBOFLOW_API_KEY")
    ocr_api_key = args.ocr_api_key or os.environ.get("BAIDU_API_KEY")
    if not sam_api_key or not ocr_api_key:
        print("Missing ROBOFLOW_API_KEY or BAIDU_API_KEY", file=sys.stderr)
        return 2
    prompts = [item.strip() for item in args.sam_prompts.split(",") if item.strip()]
    output_dir = manifest_default_dir(image_path, args.output_dir.resolve())
    manifest_path = extract_elements(
        image_path=image_path,
        output_dir=output_dir,
        prompts=prompts,
        sam_api_key=sam_api_key,
        ocr_api_key=ocr_api_key,
        sam_threshold=args.sam_threshold,
        remove_bg=args.remove_bg,
        text_only_mask=args.text_only_mask,
        rmbg_model_path=args.rmbg_model_path.resolve() if args.rmbg_model_path else None,
    )
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

