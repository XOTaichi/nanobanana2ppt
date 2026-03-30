#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from ppt_exporter import export_ppt


BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export an editable PPT from image2ppt manifest.")
    parser.add_argument("manifest", type=Path, help="Path to manifest.json")
    parser.add_argument("--output", type=Path, default=None, help="Output PPTX path")
    parser.add_argument("--background", choices=["white", "restored"], default="restored")
    parser.add_argument("--text-only", action="store_true", help="Only place text elements on the editable slide")
    parser.add_argument("--disable-rmbg", action="store_true", help="Disable RMBG preprocessing during export")
    parser.add_argument("--rmbg-model-path", type=Path, default=None, help="Optional local RMBG model path")
    parser.add_argument("--min-alpha-pixels", type=int, default=80)
    parser.add_argument("--min-alpha-ratio", type=float, default=0.08)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = args.manifest.resolve()
    output_path = args.output.resolve() if args.output else (manifest_path.parent / "overlay_editable.pptx").resolve()
    result = export_ppt(
        manifest_path=manifest_path,
        output_pptx=output_path,
        background_mode=args.background,
        text_only=args.text_only,
        use_rmbg=not args.disable_rmbg,
        rmbg_model_path=args.rmbg_model_path.resolve() if args.rmbg_model_path else None,
        min_alpha_pixels=args.min_alpha_pixels,
        min_alpha_ratio=args.min_alpha_ratio,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

