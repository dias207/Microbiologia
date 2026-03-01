import streamlit as st
from pyngrok import ngrok
import os

# Запускаем Streamlit в фоновом режиме
import subprocess
import threading
import time

def run_streamlit():
    os.system("streamlit run streamlit_app.py --server.headless true --server.port 8501")

# Запускаем Streamlit в отдельном потоке
thread = threading.Thread(target=run_streamlit)
thread.daemon = True
thread.start()

# Ждем запуска сервера
time.sleep(5)

# Создаем туннель
public_url = ngrok.connect(8501)
print(f"🌐 Публичная ссылка: {public_url}")
print(f"🔗 Отправьте эту ссылку друзьям: {public_url}")

# Держим туннель активным
try:
    input("Нажмите Enter для остановки...")
except KeyboardInterrupt:
    pass

ngrok.disconnect(public_url)
