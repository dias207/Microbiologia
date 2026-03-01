from __future__ import annotations

from typing import Optional

import torch
import torch.nn as nn
import torchvision.models as models


class BacteriaClassifier(nn.Module):
    """
    Классификатор бактерий на основе сверточной сети с transfer learning.

    По умолчанию используется ResNet18 с заменой последнего слоя под нужное число классов.
    """

    def __init__(
        self,
        num_classes: int,
        backbone: str = "resnet18",
        pretrained: bool = True,
        in_channels: int = 1,
    ) -> None:
        super().__init__()

        if backbone == "resnet18":
            if hasattr(models, "ResNet18_Weights"):
                w = models.ResNet18_Weights.DEFAULT if pretrained else None
                self.backbone = models.resnet18(weights=w)
            else:
                self.backbone = models.resnet18(pretrained=pretrained)
        else:
            raise ValueError(f"Неизвестный backbone: {backbone}")

        # Адаптация под одноканальное (grayscale) изображение при необходимости
        if in_channels == 1:
            old_conv1 = self.backbone.conv1
            self.backbone.conv1 = nn.Conv2d(
                in_channels,
                old_conv1.out_channels,
                kernel_size=old_conv1.kernel_size,
                stride=old_conv1.stride,
                padding=old_conv1.padding,
                bias=old_conv1.bias is not None,
            )

        in_features = self.backbone.fc.in_features
        self.backbone.fc = nn.Linear(in_features, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.backbone(x)


def create_bacteria_model(
    num_classes: int,
    backbone: str = "resnet18",
    pretrained: bool = True,
    in_channels: int = 1,
) -> BacteriaClassifier:
    """Фабричная функция для удобного создания модели."""
    return BacteriaClassifier(
        num_classes=num_classes,
        backbone=backbone,
        pretrained=pretrained,
        in_channels=in_channels,
    )

