from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Tuple

import pandas as pd
from PIL import Image
import torch
from torch.utils.data import Dataset

from src.utils.image_preprocessing import preprocess_image


class BacteriaCsvDataset(Dataset):
    """
    Датасет, который читает пути к изображениям и метки классов из CSV.

    Ожидаемый формат CSV:
        image_path,label
        path/to/image1.png,escherichia_coli
        path/to/image2.png,salmonella_enterica

    Путь к изображениям может быть абсолютным или относительным к root_dir.
    """

    def __init__(
        self,
        csv_path: str | Path,
        root_dir: str | Path | None = None,
        label_mapping: Optional[dict[str, int]] = None,
        transform: Optional[Callable] = None,
        target_size: Tuple[int, int] = (224, 224),
    ) -> None:
        self.csv_path = Path(csv_path)
        self.root_dir = Path(root_dir) if root_dir is not None else None
        self.df = pd.read_csv(self.csv_path)

        if "image_path" not in self.df.columns or "label" not in self.df.columns:
            raise ValueError("CSV должен содержать колонки 'image_path' и 'label'")

        self.transform = transform
        self.target_size = target_size

        # Если маппинг не задан, создаём автоматически по алфавиту
        if label_mapping is None:
            classes = sorted(self.df["label"].unique())
            self.label_mapping = {name: idx for idx, name in enumerate(classes)}
        else:
            self.label_mapping = label_mapping

    def __len__(self) -> int:
        return len(self.df)

    def __getitem__(self, idx: int):
        row = self.df.iloc[idx]
        img_path = Path(row["image_path"])

        if not img_path.is_absolute() and self.root_dir is not None:
            img_path = self.root_dir / img_path

        if not img_path.exists():
            raise FileNotFoundError(f"Файл изображения не найден: {img_path}")

        # Чтение RGB для совместимости с torchvision-пайплайном
        pil_img = Image.open(img_path).convert("RGB")
        img_np = preprocess_image(
            img=pil_img_to_bgr_numpy(pil_img), target_size=self.target_size
        )

        # В данный момент preprocess_image возвращает (1, H, W) grayscale;
        # при необходимости можно адаптировать под RGB.
        tensor = torch.from_numpy(img_np)  # (C, H, W), float32

        if self.transform is not None:
            tensor = self.transform(tensor)

        label_name = str(row["label"])
        if label_name not in self.label_mapping:
            raise KeyError(f"Неизвестная метка класса: {label_name}")
        label_idx = self.label_mapping[label_name]
        label_tensor = torch.tensor(label_idx, dtype=torch.long)

        return tensor, label_tensor


def pil_img_to_bgr_numpy(img: Image.Image):
    """Вспомогательная функция: PIL (RGB) -> numpy BGR для использования в OpenCV-пайплайне."""
    import numpy as np
    import cv2

    rgb = np.array(img)
    bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr

