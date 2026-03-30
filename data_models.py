from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class ElementRecord:
    id: str
    element_type: str
    source: str
    bbox: list[int]
    score: float | None = None
    text: str | None = None
    prompt: str | None = None
    crop_path: str | None = None
    nobg_path: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

