from __future__ import annotations

from pathlib import Path
from typing import Dict

import torch

from src.models.bacteria_cnn import create_bacteria_model
from src.utils.image_preprocessing import load_image_bgr, preprocess_image


def load_model(artifacts_path: str | Path):
    checkpoint = torch.load(artifacts_path, map_location="cpu")
    label_mapping: Dict[str, int] = checkpoint["label_mapping"]

    num_classes = len(label_mapping)
    model = create_bacteria_model(
        num_classes=num_classes,
        backbone="resnet18",
        pretrained=False,
        in_channels=1,
    )
    model.load_state_dict(checkpoint["model_state_dict"])
    model.eval()

    # Обратный маппинг: id -> имя класса
    inv_mapping = {idx: name for name, idx in label_mapping.items()}

    return model, inv_mapping


@torch.no_grad()
def predict_image(
    image_path: str | Path,
    model,
    inv_mapping: Dict[int, str],
) -> str:
    img_bgr = load_image_bgr(str(image_path))
    img_np = preprocess_image(img_bgr)  # (1, H, W)

    tensor = torch.from_numpy(img_np).unsqueeze(0)  # (1, C, H, W)

    outputs = model(tensor)
    _, pred_idx = torch.max(outputs, 1)
    pred_idx_int = int(pred_idx.item())

    return inv_mapping[pred_idx_int]


def main():
    project_root = Path(__file__).resolve().parents[2]
    artifacts_path = project_root / "artifacts" / "bacteria_classifier.pt"

    if not artifacts_path.exists():
        raise FileNotFoundError(
            f"Не найден файл модели: {artifacts_path}. "
            "Сначала запустите обучение (src/training/train.py)."
        )

    model, inv_mapping = load_model(artifacts_path)

    img_root = project_root / "img"
    example_image = project_root / "example.png"
    if example_image.exists():
        pass
    elif img_root.exists():
        first_img = next(
            (f for f in img_root.rglob("*") if f.is_file() and f.suffix.lower() in {".jpg", ".jpeg", ".png"}),
            None,
        )
        example_image = first_img or example_image
    if not example_image.exists():
        raise FileNotFoundError(
            "Не найдено изображение. Положите example.png в корень проекта или добавьте фото в img/."
        )

    pred_class = predict_image(example_image, model, inv_mapping)
    print(f"Изображение: {example_image.name} -> класс: {pred_class}")


if __name__ == "__main__":
    main()

