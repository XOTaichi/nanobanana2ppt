#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from background_restorer import restore_background
from env_utils import get_required_env, load_dotenv


BASE_DIR = Path(__file__).resolve().parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Restore a clean background from a manifest.")
    parser.add_argument("manifest", type=Path, help="Path to manifest.json or its directory")
    parser.add_argument("--output", type=Path, default=None, help="Output path for restored background")
    parser.add_argument("--dotenv", type=Path, default=BASE_DIR / ".env", help="Path to .env file")
    parser.add_argument("--aspect-ratio", default=None, help="Optional aspect ratio override, e.g. 16:9")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    load_dotenv(args.dotenv)
    manifest_path = args.manifest.resolve()
    if manifest_path.is_dir():
        manifest_path = manifest_path / "manifest.json"
    output_path = args.output.resolve() if args.output else (manifest_path.parent / "restored_background.png").resolve()
    result = restore_background(
        manifest_path=manifest_path,
        output_path=output_path,
        api_key=get_required_env("IMAGE_API_KEY"),
        api_base=get_required_env("IMAGE_API_BASE"),
        model=get_required_env("IMAGE_MODEL"),
        resolution=__import__("os").environ.get("DEFAULT_RESOLUTION", "2K"),
        aspect_ratio=args.aspect_ratio,
    )
    print(result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

