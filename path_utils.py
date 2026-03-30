from __future__ import annotations

import json
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent


def load_manifest(manifest_path: Path) -> dict[str, Any]:
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def save_manifest(manifest_path: Path, manifest: dict[str, Any]) -> None:
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_local_path(base_dir: Path, value: str | None) -> Path | None:
    if not value:
        return None
    path = Path(value)
    if path.is_absolute():
        return path if path.exists() else None
    for candidate in ((base_dir / path).resolve(), (BASE_DIR / path).resolve()):
        if candidate.exists():
            return candidate
    return (base_dir / path).resolve()


def manifest_default_dir(input_image: Path, output_dir: Path) -> Path:
    return (output_dir / input_image.stem).resolve()


def manifest_path_for(input_image: Path, output_dir: Path) -> Path:
    return manifest_default_dir(input_image, output_dir) / "manifest.json"

