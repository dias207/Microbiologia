# Инструкции: как опубликовать проект на GitHub и поделиться

Ниже — краткие шаги для публикации репозитория, загрузки модели и запуска/деплоя.

## 1) Создайте репозиторий на GitHub
- Перейдите на GitHub и создайте новый пустой репозиторий (например, `bacteria-cv`).

## 2) Подготовка локально и пуш
Откройте PowerShell в корне проекта и выполните:

```powershell
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/<your-username>/<repo>.git
git push -u origin main
```

Примечание: файл `.gitignore` уже создан и исключает `artifacts/` (в которой модель). Это обычно правильно — модель большие файлы лучше хранить отдельно.

## 3) Где хранить модель (`artifacts/bacteria_classifier.pt`)
Варианты:
- GitHub Releases: создайте Release через веб-интерфейс и загрузите `bacteria_classifier.pt` как asset.
- Google Drive / Dropbox / S3: загрузите файл и в `README`/скриптах указывайте публичную ссылку для скачивания.
- Git LFS (если предпочитаете хранить в репозитории):

```bash
git lfs install
git lfs track "artifacts/*.pt"
# затем добавить .gitattributes и смоделированный файл
git add .gitattributes
git add artifacts/bacteria_classifier.pt
git commit -m "Add model with LFS"
git push origin main
```

Обратите внимание на квоты Git LFS — они ограничены в бесплатных аккаунтах.

## 4) Как запустить у себя (локально)
В PowerShell (Windows):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn src.web.app:app --reload --host 0.0.0.0 --port 8000
```

Откройте в браузере: `http://localhost:8000`.

Если модель не в `artifacts/`, скачайте её в папку `artifacts` (или укажите путь).

## 5) Временный общий доступ (показ друзьям)
- Используйте `ngrok` чтобы пробросить локальный порт наружу:

```bash
ngrok http 8000
```

ngrok выдаст публичный URL, которым можно поделиться.

## 6) Деплой на Render / Heroku / Railway (быстро)
Пример для Render (рекомендуется для простого деплоя):
1. Создайте репозиторий на GitHub и запушьте код.
2. Зарегистрируйтесь в Render и создайте новый **Web Service** -> подключите GitHub -> выберите репозиторий и ветку.
3. Build & Start: если у вас есть `Procfile`, Render автоматически использует его. Иначе укажите:
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn -k uvicorn.workers.UvicornWorker src.web.app:app --bind 0.0.0.0:$PORT`
4. Убедитесь, что модель доступна во время деплоя (в репо или скачивается в step build).

Heroku похож: используйте `Procfile` и пушьте в Heroku remote.

## 7) Контейнер (Docker)
Файл `Dockerfile` добавлен. Сборка и запуск локально:

```bash
docker build -t bacteria-app .
docker run -p 8000:8000 bacteria-app
```

Для деплоя можно пушить образ в Docker Hub и запускать на VPS/Cloud.

## 8) Пример, как автоматически скачивать модель при деплое
Если модель хранится по публичной ссылке, добавьте в `Dockerfile` или в Build Command команду скачивания, например:

```dockerfile
RUN curl -L -o artifacts/bacteria_classifier.pt "https://.../bacteria_classifier.pt"
```

Или добавьте `scripts/download_model.py`, который вызывается в Build Step.

## 9) README / описание для друзей
В `README.md` положите краткие команды для запуска (раздел "Quick start") и ссылку на Release/модель.

---

Нужна помощь с одним из шагов (создать репозиторий на GitHub и запушить отсюда, подготовить Release и загрузить модель, или выполнить деплой на Render)?
