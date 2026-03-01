# ИИ-модель для распознавания палочковидных бактерий

Проект на Python: узконаправленная модель компьютерного зрения для классификации бактерий по микроскопическим изображениям (Escherichia, Salmonella, Shigella, Yersinia, Campylobacter, Helicobacter).

## Структура проекта

```text
Project-4/
  README.md
  requirements.txt
  run_all.ps1          # Установка, CSV, обучение одним скриптом
  img/                 # Папка с изображениями (по подпапкам-классам)
    train.csv, val.csv # Генерируются скриптом
    escherichia_coli/
    salmonella_enterica/
    ...
  artifacts/
    bacteria_classifier.pt  # Сохранённая модель после обучения
  src/
    data/       dataset.py, make_csv_from_img.py, organize_img.py
    models/     bacteria_cnn.py
    training/   train.py
    inference/  predict.py
    utils/      image_preprocessing.py
    web/        app.py  # веб-сервер FastAPI
```

## Быстрый старт

**Вариант 1 — всё одной командой (PowerShell):**

```powershell
.\run_all.ps1
```

**Вариант 2 — по шагам:**

1. Установить зависимости:
   ```bash
   python -m pip install -r requirements.txt
   ```

2. Если фото лежат в `img/` без подпапок — разложить по классам:
   ```bash
   python -m src.data.organize_img
   ```

3. Сгенерировать разбиение на train/val:
   ```bash
   python -m src.data.make_csv_from_img
   ```

4. Обучить модель:
   ```bash
   python -m src.training.train
   ```

5. Предсказание по одному изображению (берётся из `img/` или `example.png`):
   ```bash
   python -m src.inference.predict
   ```

6. Запустить веб-интерфейс в браузере:
   ```bash
   uvicorn src.web.app:app --reload
   ```
   Затем открыть в браузере: `http://127.0.0.1:8000/`

## Датасет

- Изображения лежат в **`img/`**, по подпапкам на класс:
  - `img/escherichia_coli/`, `img/salmonella_enterica/`, и т.д.

### Динамическая таксономия

Сервер умеет хранить и выдавать таксономические подписи по имени загружаемого
файла. По-умолчанию используются заранее определённые классы (см. исходники),
но вы можете присылать корректные описания для любых изображений через API:

```bash
# отправка таксономии для файла (без участия модели)
curl -X POST "http://localhost:8000/taxonomy" \
    -H 'Content-Type: application/json' \
    -d '{"filename":"MyPhoto.jpg","family":"Neisseriaceae","genus":"Neisseria","species":"N. meningitidis"}'
```

```bash
# получить текущую запись (или 404, если нет)
curl "http://localhost:8000/taxonomy?filename=MyPhoto.jpg"
```
</blockquote>
- Скрипт `organize_img` раскладывает фото из корня `img/` по этим папкам (round-robin), если подпапок ещё нет.
- `make_csv_from_img` создаёт `img/train.csv` и `img/val.csv` по структуре папок.

## Модель

- ResNet18 (transfer learning), один канал (grayscale после предобработки).
- Предобработка: шум, CLAHE, нормализация, размер 224×224.
- Сохранение: `artifacts/bacteria_classifier.pt` (веса + маппинг классов).
