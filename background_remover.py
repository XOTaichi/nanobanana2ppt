from __future__ import annotations

import os
from pathlib import Path

from PIL import Image


class BriaRMBG2Remover:
    def __init__(self, model_path: Path | str | None = None, output_dir: Path | str | None = None):
        import torch
        from torchvision import transforms
        from transformers import AutoModelForImageSegmentation

        self._torch = torch
        self._transforms = transforms
        self.model_path = Path(model_path) if model_path else None
        self.output_dir = Path(output_dir) if output_dir else Path("./output/icons")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.model_repo_id = "briaai/RMBG-2.0"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        model_source = str(self.model_path) if self.model_path and self.model_path.exists() else self.model_repo_id
        kwargs = {"trust_remote_code": True}
        if model_source == self.model_repo_id:
            kwargs["token"] = os.environ.get("HF_TOKEN") or os.environ.get("HUGGINGFACE_TOKEN")
        self.model = AutoModelForImageSegmentation.from_pretrained(model_source, **kwargs).eval().to(self.device)
        self.image_size = (1024, 1024)
        self.transform_image = transforms.Compose(
            [
                transforms.Resize(self.image_size),
                transforms.ToTensor(),
                transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
            ]
        )

    def remove_background(self, image: Image.Image, output_name: str) -> str:
        image_rgb = image.convert("RGB")
        input_tensor = self.transform_image(image_rgb).unsqueeze(0).to(self.device)
        with self._torch.no_grad():
            preds = self.model(input_tensor)[-1].sigmoid().cpu()
        alpha = self._transforms.ToPILImage()(preds[0].squeeze()).resize(image_rgb.size)
        output = image_rgb.copy()
        output.putalpha(alpha)
        output_path = self.output_dir / f"{output_name}_nobg.png"
        output.save(output_path)
        return str(output_path)

