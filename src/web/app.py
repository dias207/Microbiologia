from __future__ import annotations

from pathlib import Path
from typing import Dict

import numpy as np
import torch
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse

from src.models.bacteria_cnn import create_bacteria_model
from src.utils.image_preprocessing import preprocess_image, detect_rod_shapes

# таксономия теперь хранится в отдельном модуле, доступна для обновления
from src.web.taxonomy_store import load_taxonomy, save_taxonomy


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACTS_PATH = PROJECT_ROOT / "artifacts" / "bacteria_classifier.pt"

# Таксономия для поддерживаемых классов и для конкретных изображений
# Переехала в отдельный модуль, поэтому определяется во время загрузки приложения
CLASS_TAXONOMY: Dict[str, Dict[str, str]] = {}

app = FastAPI(title="Bacteria CV Model")


def _load_model_and_mapping():
    if not ARTIFACTS_PATH.exists():
        raise FileNotFoundError(
            f"Не найден файл модели: {ARTIFACTS_PATH}. "
            "Сначала запустите обучение (python -m src.training.train)."
        )

    checkpoint = torch.load(ARTIFACTS_PATH, map_location="cpu")
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

    inv_mapping = {idx: name for name, idx in label_mapping.items()}
    return model, inv_mapping


MODEL, INV_MAPPING = _load_model_and_mapping()

# заполняем глобальную таксономию (с возможностью правок через API)
CLASS_TAXONOMY = load_taxonomy()


@app.get("/", response_class=HTMLResponse)
async def index():
    return """
    <html lang="ru">
        <head>
            <meta charset="utf-8" />
            <title>Bacteria classifier</title>
            <style>
                :root {
                    --bg: #f1f5f9;
                    --card-bg: #ffffff;
                    --accent: #16a34a;
                    --accent-soft: rgba(22, 163, 74, 0.14);
                    --text: #0f172a;
                    --muted: #6b7280;
                    --border: #e5e7eb;
                }
                * {
                    box-sizing: border-box;
                }
                body {
                    margin: 0;
                    min-height: 100vh;
                    font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
                    background: radial-gradient(circle at top left, rgba(22, 163, 74, 0.12), transparent 55%), var(--bg);
                    color: var(--text);
                    display: flex;
                    align-items: stretch;
                    justify-content: center;
                }
                .layout {
                    width: 100%;
                    max-width: 880px;
                    margin: 0 auto;
                    padding: 28px 18px 32px;
                    display: flex;
                    flex-direction: column;
                    gap: 18px;
                    min-height: 100vh;
                }
                .card {
                    background: var(--card-bg);
                    border-radius: 18px;
                    padding: 22px 22px 20px;
                    box-shadow:
                        0 18px 40px rgba(15, 23, 42, 0.08),
                        0 0 0 1px rgba(148, 163, 184, 0.35);
                    border: 1px solid rgba(209, 213, 219, 0.9);
                }
                .page-header {
                    padding: 8px 4px 4px;
                }
                .title {
                    font-size: 20px;
                    font-weight: 600;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    margin-bottom: 6px;
                }
                .title-dot {
                    width: 9px;
                    height: 9px;
                    border-radius: 999px;
                    background: var(--accent);
                    box-shadow: 0 0 0 6px var(--accent-soft);
                }
                .subtitle {
                    font-size: 13px;
                    color: var(--muted);
                    margin-bottom: 14px;
                }
                .pill {
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    font-size: 11px;
                    padding: 4px 9px;
                    border-radius: 999px;
                    background: rgba(240, 253, 244, 0.95);
                    border: 1px solid rgba(22, 163, 74, 0.3);
                    color: #166534;
                    margin-bottom: 16px;
                }
                .pill-dot {
                    width: 6px;
                    height: 6px;
                    border-radius: 999px;
                    background: var(--accent);
                }
                form {
                    border-radius: 14px;
                    padding: 16px 16px 14px;
                    border: 1px dashed rgba(148, 163, 184, 0.8);
                    background: #f9fafb;
                    display: flex;
                    flex-direction: column;
                    gap: 12px;
                    margin-bottom: 12px;
                }
                .file-row {
                    display: flex;
                    align-items: center;
                    justify-content: space-between;
                    gap: 10px;
                    flex-wrap: wrap;
                }
                .file-label {
                    font-size: 13px;
                    color: var(--muted);
                }
                input[type="file"] {
                    font-size: 12px;
                    color: var(--muted);
                    max-width: 100%;
                }
                button {
                    margin-top: 4px;
                    align-self: flex-start;
                    padding: 7px 16px;
                    border-radius: 999px;
                    border: none;
                    background: linear-gradient(135deg, #22c55e, #16a34a);
                    color: white;
                    font-size: 13px;
                    font-weight: 500;
                    cursor: pointer;
                    display: inline-flex;
                    align-items: center;
                    gap: 6px;
                    box-shadow:
                        0 12px 30px rgba(22, 163, 74, 0.55),
                        0 0 0 1px rgba(34, 197, 94, 0.4);
                    transition: transform 0.1s ease, box-shadow 0.1s ease, filter 0.1s ease;
                }
                button:hover {
                    transform: translateY(-1px);
                    filter: brightness(1.05);
                    box-shadow:
                        0 18px 40px rgba(22, 163, 74, 0.7),
                        0 0 0 1px rgba(34, 197, 94, 0.6);
                }
                button:active {
                    transform: translateY(0);
                    box-shadow:
                        0 10px 24px rgba(22, 163, 74, 0.55),
                        0 0 0 1px rgba(22, 163, 74, 0.7);
                }
                button:disabled {
                    opacity: 0.5;
                    cursor: default;
                    box-shadow: none;
                }
                .result {
                    margin-top: 6px;
                    font-size: 14px;
                }
                .result-label {
                    color: var(--muted);
                }
                .result-value {
                    font-weight: 650;
                    color: var(--accent);
                }
                .shape-line {
                    font-size: 13px;
                    margin-top: 4px;
                    color: var(--muted);
                }
                .shape-line strong {
                    color: var(--text);
                }
                .error {
                    margin-top: 4px;
                    font-size: 13px;
                    color: #b91c1c;
                }
                .hint {
                    margin-top: 12px;
                    font-size: 12px;
                    color: var(--muted);
                    line-height: 1.5;
                }
                .hint strong {
                    color: var(--text);
                    font-weight: 600;
                }
            </style>
        </head>
        <body>
            <div class="layout">
                <div class="page-header">
                    <div class="title">
                        <span class="title-dot"></span>
                        <span>Учебный проект · ИИ и микробиология</span>
                    </div>
                    <div class="subtitle">
                        Демонстрация работы модели компьютерного зрения для морфологического анализа бактерий
                        в учебных целях.
                    </div>
                    <div class="pill">
                        <span class="pill-dot"></span>
                        <span>ResNet18 · палочковидные бактерии</span>
                    </div>
                </div>

                <div class="card">
                    <div class="title">
                        <span class="title-dot"></span>
                        <span>Онлайн‑классификация изображения</span>
                    </div>
                    <div class="subtitle">
                        Загрузите микроскопическое фото бактерий и получите морфологическое заключение,
                        количество палочек и пример таксономической подписи.
                    </div>
                    <form id="upload-form" enctype="multipart/form-data">
                        <div class="file-row">
                            <div class="file-label">Файл изображения</div>
                            <input id="file-input" type="file" name="file" accept="image/*" required />
                        </div>
                        <button id="submit-btn" type="submit">
                            Запустить классификацию
                        </button>
                        <div id="result" class="result"></div>
                        <div id="error" class="error"></div>
                    </form>

                    <div class="hint">
                        <strong>Важно:</strong> результаты предназначены для учебных целей. Для реальной диагностики
                        требуется большая клиническая выборка, калибровка и валидация.
                        <br />
                        После обработки изображения вы можете исправить автоматически выведенную
                        таксономию: нажмите «Исправить таксономию» и введите корректные
                        семейство/род/вид. Это позволит серверу запомнить описание для этого файла.
                    </div>
                </div>
            </div>

            <script>
                const form = document.getElementById('upload-form');
                const fileInput = document.getElementById('file-input');
                const submitBtn = document.getElementById('submit-btn');
                    const resultEl = document.getElementById('result');
                    const errorEl = document.getElementById('error');

                form.addEventListener('submit', async (e) => {
                    e.preventDefault();
                    resultEl.textContent = '';
                    errorEl.textContent = '';

                    if (!fileInput.files.length) {
                        errorEl.textContent = 'Выберите файл изображения.';
                        return;
                    }

                    const formData = new FormData();
                    formData.append('file', fileInput.files[0]);

                    submitBtn.disabled = true;
                    submitBtn.textContent = 'Классификация...';

                    try {
                        const resp = await fetch('/predict', {
                            method: 'POST',
                            body: formData
                        });
                        const data = await resp.json();

                        if (!resp.ok) {
                            errorEl.textContent = data.error || 'Ошибка при классификации.';
                        } else {
                            const cls = data.predicted_class || 'unknown';
                            let html = '<span class=\"result-label\">Предсказанный класс: </span>' +
                                '<span class=\"result-value\">' + cls + '</span>';

                            if (data.shape) {
                                const hasRod = data.shape.has_rod;
                                const count = typeof data.shape.rod_count === 'number' ? data.shape.rod_count : 0;
                                const rodLabel = hasRod ? 'палочковидная форма обнаружена' : 'палочковидная форма не обнаружена';
                                html += '<div class=\"shape-line\"><strong>Форма:</strong> ' + rodLabel + '</div>';
                                if (count > 0) {
                                    html += '<div class=\"shape-line\"><strong>Количество палочек (оценочно):</strong> ' +
                                        count + '</div>';
                                }
                            }

                            if (data.taxonomy) {
                                html += '<div class=\"shape-line\"><strong>Тұқымдастық:</strong> ' +
                                    (data.taxonomy.family || '-') + '</div>';
                                html += '<div class=\"shape-line\"><strong>Туыстастық:</strong> ' +
                                    (data.taxonomy.genus || '-') + '</div>';
                                html += '<div class=\"shape-line\"><strong>Түрі:</strong> ' +
                                    (data.taxonomy.species || '-') + '</div>';                                // кнопка редактирования
                                html += '<button id="edit-taxonomy-btn" style="margin-top:10px;">' +
                                        'Исправить таксономию</button>';                            }

                            resultEl.innerHTML = html;

                            // если появилась кнопка редактирования, привязываем обработчик
                            const editBtn = document.getElementById('edit-taxonomy-btn');
                            if (editBtn) {
                                editBtn.addEventListener('click', async () => {
                                    const fam = prompt('Семейство:', data.taxonomy.family || '');
                                    if (fam === null) return; // отмена
                                    const gen = prompt('Род:', data.taxonomy.genus || '');
                                    if (gen === null) return;
                                    const spec = prompt('Вид:', data.taxonomy.species || '');
                                    if (spec === null) return;
                                    // отправляем на сервер
                                    try {
                                        const resp2 = await fetch('/taxonomy', {
                                            method: 'POST',
                                            headers: {'Content-Type': 'application/json'},
                                            body: JSON.stringify({
                                                filename: fileInput.files[0].name,
                                                family: fam,
                                                genus: gen,
                                                species: spec,
                                            }),
                                        });
                                        const data2 = await resp2.json();
                                        if (resp2.ok) {
                                            alert('Таксономия обновлена');
                                        } else {
                                            alert('Ошибка: ' + (data2.error||'')); 
                                        }
                                    } catch(e) {
                                        alert('Не удалось отправить таксономию');
                                    }
                                });
                            }
                        }
                    } catch (err) {
                        errorEl.textContent = 'Не удалось отправить запрос. Проверьте, что сервер запущен.';
                    } finally {
                        submitBtn.disabled = false;
                        submitBtn.textContent = 'Запустить классификацию';
                    }
                });
            </script>
        </body>
    </html>
    """


@app.post("/predict")
async def predict(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        if not contents:
            return JSONResponse(
                status_code=400,
                content={"error": "Пустой файл"},
            )

        # bytes -> numpy BGR через OpenCV
        import cv2

        file_bytes = np.frombuffer(contents, dtype=np.uint8)
        img_bgr = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        if img_bgr is None:
            return JSONResponse(
                status_code=400,
                content={"error": "Не удалось прочитать изображение"},
            )

        img_np = preprocess_image(img_bgr)  # (1, H, W), float32
        tensor = torch.from_numpy(img_np).unsqueeze(0)  # (1, C, H, W)

        # Анализ морфологии «палочка / не палочка»
        shape_info = detect_rod_shapes(img_np)

        with torch.no_grad():
            outputs = MODEL(tensor)
            _, pred_idx = torch.max(outputs, 1)
            pred_idx_int = int(pred_idx.item())

        pred_class = INV_MAPPING.get(pred_idx_int, "unknown")

        # сначала ищем таксономию по имени загруженного файла
        file_key = Path(file.filename).stem
        taxonomy = CLASS_TAXONOMY.get(file_key) or CLASS_TAXONOMY.get(pred_class, {})

        return {
            "filename": file.filename,
            "predicted_class": pred_class,
            "shape": {
                "has_rod": bool(shape_info.get("has_rod", False)),
                "rod_count": int(shape_info.get("rod_count", 0)),
                "max_aspect_ratio": float(shape_info.get("max_aspect_ratio", 0.0)),
            },
            "taxonomy": {
                "family": taxonomy.get("family", ""),
                "genus": taxonomy.get("genus", ""),
                "species": taxonomy.get("species", ""),
            },
        }
    except Exception as exc:  # noqa: BLE001
        return JSONResponse(
            status_code=500,
            content={"error": str(exc)},
        )


@app.post("/taxonomy")
async def update_taxonomy(entry: Dict[str, str]):
    """Добавить / изменить запись таксономии для конкретного имени файла.

    Ожидаемые поля JSON: filename, family, genus, species.
    """
    filename = entry.get("filename")
    if not filename:
        return JSONResponse(status_code=400, content={"error": "'filename' is required"})

    key = Path(filename).stem
    CLASS_TAXONOMY[key] = {
        "family": entry.get("family", ""),
        "genus": entry.get("genus", ""),
        "species": entry.get("species", ""),
    }
    save_taxonomy(CLASS_TAXONOMY)
    return {"status": "ok", "key": key}


@app.get("/taxonomy")
async def get_taxonomy(filename: str):
    """Получить запись таксономии по имени файла (или классу).

    Параметр query: filename — имя файла (можно с расширением) или имя класса.
    """
    key = Path(filename).stem
    entry = CLASS_TAXONOMY.get(key)
    if entry is None:
        return JSONResponse(status_code=404, content={"error": "not found"})
    return {"filename": key, **entry}


@app.post("/taxonomy/reload")
async def reload_taxonomy():
    """Принудительно перечитать файл `taxonomy.json`.

    Удобно, если вы редактировали файл вручную и хотите, чтобы изменения
    вступили в силу без перезапуска сервера.
    """
    global CLASS_TAXONOMY
    CLASS_TAXONOMY = load_taxonomy()
    return {"status": "reloaded", "count": len(CLASS_TAXONOMY)}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("src.web.app:app", host="127.0.0.1", port=8000, reload=True)

