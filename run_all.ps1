# Установка зависимостей, генерация CSV и обучение
Set-Location $PSScriptRoot

Write-Host "Установка зависимостей..."
python -m pip install -r requirements.txt -q

Write-Host "Генерация train.csv / val.csv..."
python -m src.data.make_csv_from_img

Write-Host "Запуск обучения..."
python -m src.training.train

Write-Host "Готово. Модель: artifacts\bacteria_classifier.pt"
