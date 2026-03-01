from __future__ import annotations

from pathlib import Path
from typing import Dict

import torch
from torch import nn, optim
from torch.utils.data import DataLoader

from src.data.dataset import BacteriaCsvDataset
from src.models.bacteria_cnn import create_bacteria_model


def create_dataloaders(
    train_csv: str | Path,
    val_csv: str | Path,
    root_dir: str | Path | None,
    batch_size: int,
    num_workers: int = 0,
):
    train_dataset = BacteriaCsvDataset(csv_path=train_csv, root_dir=root_dir)
    val_dataset = BacteriaCsvDataset(
        csv_path=val_csv,
        root_dir=root_dir,
        label_mapping=train_dataset.label_mapping,
    )

    train_loader = DataLoader(
        train_dataset,
        batch_size=batch_size,
        shuffle=True,
        num_workers=num_workers,
    )
    val_loader = DataLoader(
        val_dataset,
        batch_size=batch_size,
        shuffle=False,
        num_workers=num_workers,
    )

    return train_loader, val_loader, train_dataset.label_mapping


def train_one_epoch(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    optimizer: optim.Optimizer,
    device: torch.device,
) -> float:
    model.train()
    running_loss = 0.0

    for inputs, labels in dataloader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)

    return running_loss / len(dataloader.dataset)


@torch.no_grad()
def evaluate(
    model: nn.Module,
    dataloader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Dict[str, float]:
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, labels in dataloader:
        inputs = inputs.to(device)
        labels = labels.to(device)

        outputs = model(inputs)
        loss = criterion(outputs, labels)
        running_loss += loss.item() * inputs.size(0)

        _, preds = torch.max(outputs, 1)
        correct += (preds == labels).sum().item()
        total += labels.size(0)

    avg_loss = running_loss / len(dataloader.dataset)
    accuracy = correct / total if total > 0 else 0.0

    return {"loss": avg_loss, "accuracy": accuracy}


def main():
    # --- Настраиваем пути и гиперпараметры ---
    project_root = Path(__file__).resolve().parents[2]
    # Используем папку с изображениями рядом с src, например "img"
    data_root = project_root / "img"

    train_csv = data_root / "train.csv"
    val_csv = data_root / "val.csv"

    batch_size = 8
    num_epochs = 5
    learning_rate = 1e-4

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    # --- Даталоадеры ---
    train_loader, val_loader, label_mapping = create_dataloaders(
        train_csv=train_csv,
        val_csv=val_csv,
        root_dir=data_root,
        batch_size=batch_size,
        num_workers=0,
    )

    num_classes = len(label_mapping)

    # --- Модель, лосс, оптимизатор ---
    model = create_bacteria_model(
        num_classes=num_classes,
        backbone="resnet18",
        pretrained=True,
        in_channels=1,
    ).to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=learning_rate)

    # --- Цикл обучения ---
    for epoch in range(1, num_epochs + 1):
        train_loss = train_one_epoch(
            model=model,
            dataloader=train_loader,
            criterion=criterion,
            optimizer=optimizer,
            device=device,
        )

        metrics = evaluate(
            model=model,
            dataloader=val_loader,
            criterion=criterion,
            device=device,
        )

        print(
            f"Эпоха {epoch}/{num_epochs} | "
            f"train_loss={train_loss:.4f} | "
            f"val_loss={metrics['loss']:.4f} | "
            f"val_acc={metrics['accuracy']:.4f}"
        )

    # --- Сохранение модели и маппинга классов ---
    output_dir = project_root / "artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)

    model_path = output_dir / "bacteria_classifier.pt"
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "label_mapping": label_mapping,
        },
        model_path,
    )

    print(f"Модель сохранена в: {model_path}")


if __name__ == "__main__":
    main()

