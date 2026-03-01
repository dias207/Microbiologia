"""
Раскладывает изображения из img/ (без подпапок) по папкам классов.
Классы создаются по списку бактерий; файлы распределяются по кругу (round-robin).
"""
from __future__ import annotations

import shutil
from pathlib import Path

CLASSES = [
    "escherichia_coli",
    "salmonella_enterica",
    "shigella_dysenteriae",
    "yersinia_pestis",
    "campylobacter_jejuni",
    "helicobacter_pylori",
]

IMG_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}


def organize_img_into_classes(img_root: Path) -> None:
    img_root = Path(img_root)
    if not img_root.exists():
        raise FileNotFoundError(f"Папка не найдена: {img_root}")

    # Только файлы в корне img, не в подпапках
    files = [
        f
        for f in img_root.iterdir()
        if f.is_file() and f.suffix.lower() in IMG_EXTENSIONS
    ]

    if not files:
        raise RuntimeError(f"В {img_root} нет изображений")

    for class_name in CLASSES:
        (img_root / class_name).mkdir(parents=True, exist_ok=True)

    for i, f in enumerate(files):
        class_name = CLASSES[i % len(CLASSES)]
        dest = img_root / class_name / f.name
        shutil.move(str(f), str(dest))
        print(f"  {f.name} -> {class_name}/")

    print(f"Разложено {len(files)} файлов по {len(CLASSES)} классам.")


def main() -> None:
    project_root = Path(__file__).resolve().parents[2]
    img_root = project_root / "img"
    organize_img_into_classes(img_root)


if __name__ == "__main__":
    main()
