from __future__ import annotations

import csv
import random
from pathlib import Path


def create_csv_from_img_folder(
    img_root: Path,
    train_csv: Path,
    val_csv: Path,
    val_ratio: float = 0.2,
):
    """
    Создаёт train.csv и val.csv из структуры:

    img/
      escherichia_coli/
        img001.png
        ...
      salmonella_enterica/
        ...
      ...

    В CSV записываются строки:
        image_path,label
        escherichia_coli/img001.png,escherichia_coli
    """
    if not img_root.exists():
        raise FileNotFoundError(f"Папка с изображениями не найдена: {img_root}")

    samples = []

    for class_dir in sorted(img_root.iterdir()):
        if not class_dir.is_dir():
            continue

        label = class_dir.name
        for img_path in class_dir.glob("*.*"):
            if not img_path.is_file():
                continue
            # путь относительно img_root
            rel_path = img_path.relative_to(img_root)
            samples.append((str(rel_path).replace("\\", "/"), label))

    if not samples:
        raise RuntimeError(f"Не найдено изображений в {img_root}")

    random.shuffle(samples)

    val_size = int(len(samples) * val_ratio)
    val_samples = samples[:val_size]
    train_samples = samples[val_size:]

    def write_csv(path: Path, rows):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["image_path", "label"])
            writer.writerows(rows)

    write_csv(train_csv, train_samples)
    write_csv(val_csv, val_samples)

    print(f"train.csv: {len(train_samples)} образцов -> {train_csv}")
    print(f"val.csv:   {len(val_samples)} образцов -> {val_csv}")


def main():
    project_root = Path(__file__).resolve().parents[2]
    img_root = project_root / "img"

    train_csv = img_root / "train.csv"
    val_csv = img_root / "val.csv"

    create_csv_from_img_folder(
        img_root=img_root,
        train_csv=train_csv,
        val_csv=val_csv,
        val_ratio=0.2,
    )


if __name__ == "__main__":
    main()

