from __future__ import annotations

from typing import Dict, Tuple

import cv2
import numpy as np


def load_image_bgr(path: str) -> np.ndarray:
    """Загрузка изображения в формате BGR (как в OpenCV)."""
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Не удалось загрузить изображение: {path}")
    return img


def preprocess_image(
    img: np.ndarray,
    target_size: Tuple[int, int] = (224, 224),
) -> np.ndarray:
    """
    Базовый конвейер предобработки:
    - удаление шума (Gaussian blur)
    - усиление контраста (CLAHE)
    - нормализация и изменение размера
    """
    # Перевод в оттенки серого
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Удаление мелкого шума
    blurred = cv2.GaussianBlur(gray, (3, 3), 0)

    # Выравнивание гистограммы / CLAHE для локального контраста
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(blurred)

    # Масштабирование к целевому размеру
    resized = cv2.resize(enhanced, target_size, interpolation=cv2.INTER_AREA)

    # Нормализация к [0, 1]
    normalized = resized.astype(np.float32) / 255.0

    # Добавляем ось канала (1 канал для grayscale)
    normalized = np.expand_dims(normalized, axis=0)  # (C, H, W)

    return normalized


def binarize_image(img: np.ndarray) -> np.ndarray:
    """
    Пример бинаризации для последующего анализа формы.
    Ожидает на входе одноканальное изображение в диапазоне [0, 1] или [0, 255].
    """
    if img.ndim == 3 and img.shape[0] == 1:
        img_2d = img[0]
    else:
        img_2d = img

    # Приводим к 0–255
    if img_2d.max() <= 1.0:
        img_2d = (img_2d * 255).astype(np.uint8)
    else:
        img_2d = img_2d.astype(np.uint8)

    # Otsu threshold
    _, binary = cv2.threshold(img_2d, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    return binary


def detect_rod_shapes(img: np.ndarray) -> Dict[str, float | int | bool]:
    """
    Простейший анализ формы: пытаемся обнаружить палочковидные объекты.

    Логика:
    - бинаризуем изображение;
    - ищем контуры / компоненты;
    - для каждого считаем отношение сторон bounding box;
    - если отношение > порога и площадь достаточно большая, считаем как «палочку».
    """
    binary = binarize_image(img)

    # Немного чистим шум морфологическим открытием
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    cleaned = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel, iterations=1)

    # В некоторых изображениях бактерии могут быть тёмными на светлом фоне — инвертируем при необходимости
    white_ratio = float((cleaned > 0).mean())
    if white_ratio > 0.5:
        cleaned = cv2.bitwise_not(cleaned)

    contours, _ = cv2.findContours(cleaned, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    rod_count = 0
    max_aspect = 0.0

    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        area = w * h
        if area < 30:
            continue  # мелкий шум

        aspect = max(w, h) / max(1.0, float(min(w, h)))
        max_aspect = max(max_aspect, aspect)

        if aspect >= 3.0:
            rod_count += 1

    has_rod = rod_count > 0

    return {
        "has_rod": has_rod,
        "rod_count": int(rod_count),
        "max_aspect_ratio": float(max_aspect),
    }


