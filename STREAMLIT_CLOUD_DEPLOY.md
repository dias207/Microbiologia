# Streamlit Cloud Deployment Guide

## 1) Подготовка модели (важно!)

Так как файл модели `artifacts/bacteria_classifier.pt` слишком большой (~100+ МБ), он не включен в GitHub. Нужно загрузить его отдельно:

### Вариант A: GitHub Releases (рекомендуется)
1. Перейдите на https://github.com/dias207/Microbiologia/releases
2. Нажмите "Create a new release"
3. Версия: `v1.0`
4. Название: `Model v1.0`
5. Нажмите "Attach binaries" и загрузите файл `artifacts/bacteria_classifier.pt`
6. Нажмите "Publish release"
7. Скопируйте публичную ссылку на скачивание файла

После загрузки ссылка будет выглядеть примерно так:
```
https://github.com/dias207/Microbiologia/releases/download/v1.0/bacteria_classifier.pt
```

### Вариант B: Google Drive / Dropbox
1. Загрузите файл на Google Drive
2. Поделитесь ссылкой (сделайте публичной)
3. Модифицируйте ссылку:
   - Google Drive: `https://drive.google.com/uc?export=download&id=<FILE_ID>`
   - Получите FILE_ID из ссылки

## 2) Развертывание на Streamlit Cloud

### Шаг 1: Создайте аккаунт на Streamlit Cloud
1. Перейдите на https://streamlit.io/cloud
2. Нажмите "Sign up"
3. Авторизуйтесь через GitHub

### Шаг 2: Создайте приложение
1. Нажмите "New app"
2. Выберите:
   - Repository: `dias207/Microbiologia`
   - Branch: `main`
   - Main file path: `streamlit_app.py`
3. Нажмите "Deploy"

### Шаг 3: Добавьте переменную окружения для модели
1. На странице приложения нажмите "⋮" (три точки) → "Settings"
2. Перейдите на вкладку "Secrets"
3. Добавьте в `secrets.toml`:
```toml
MODEL_URL = "https://github.com/dias207/Microbiologia/releases/download/v1.0/bacteria_classifier.pt"
```
Скопируйте ссылку, полученную на шаге 1.

4. Нажмите "Save"

### Шаг 4: Перезагрузите приложение
1. Вернитесь на главную страницу приложения
2. Нажмите меню → "Reboot app" или просто дождитесь автоматической перезагрузки

## 3) Готово!

Приложение будет доступно по адресу:
```
https://share.streamlit.io/<username>/Microbiologia/
```

Вы также можете поделиться прямой ссылкой с друзьями.

## Альтернативный вариант: Если модель не загружается

Если во время первого запуска модель не загружается (ошибка FileNotFoundError), то:

1. Убедитесь, что ссылка на модель корректна
2. Проверьте, что переменная `MODEL_URL` добавлена в `secrets.toml`
3. Нажмите "Reboot app" в меню приложения
4. Проверьте логи (нажмите "Terminal" или смотрите logs)

## Локальное тестирование перед Streamlit Cloud

Перед деплоем протестируйте локально:

```powershell
.\.venv\Scripts\Activate.ps1
$env:MODEL_URL = "https://github.com/dias207/Microbiologia/releases/download/v1.0/bacteria_classifier.pt"
streamlit run streamlit_app.py
```

Если модель скачивается и приложение работает локально, оно будет работать и на Streamlit Cloud.
