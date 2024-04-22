import re
import time
import os
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Паттерн для поиска кодов ответов в логе Nginx
log_pattern = re.compile(r'" (\d{3}) ')

# Путь к файлу лога Nginx на Windows
nginx_log_path = "D:\\nginx-1.24.0\\logs\\access.log"

# URL Telegraf для приема метрик
telegraf_url = "http://localhost:8186/write?db=nginx"

# Переменная для хранения последней позиции в файле
last_position = 0

# Токен и chat_id телеграм-бота
TOKEN = "5611986812:AAHNOJBAXn34rMA83sPi0Cgh5dPKgzSRLOY"
chat_id = "-1002108620285"

# Функция для парсинга строки лога и извлечения кода ответа
def parse_log_line(line):
    match = log_pattern.search(line)
    if match:
        return match.group(1)
    else:
        return None

# Функция для отправки метрик в Telegraf
def send_metric_to_telegraf(response_code):
    metric_data = f'nginx_response_code value={response_code}'
    response = requests.post(telegraf_url, data=metric_data)
    if response.status_code == 204:
        print(f"Metric sent successfully: nginx_response_code={response_code}")
    else:
        print("Failed to send metric to Telegraf")

# Функция для отправки сообщения в телеграм
def send_telegram_message(message):
    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    params = {"chat_id": chat_id, "text": message}
    requests.post(url, params=params)

# Функция для обработки новых строк в логе
def handle_new_log_entry():
    global last_position
    observer = Observer()
    observer.schedule(NginxLogHandler(), path=os.path.dirname(nginx_log_path), recursive=False)
    observer.start()

    with open(nginx_log_path, 'r') as file:
        # Перемещаемся к последней известной позиции в файле
        file.seek(last_position)
        # Читаем только новые данные
        new_data = file.read()
        # Обновляем последнюю позицию
        last_position = file.tell()
        
        # Разбиваем новые данные на строки и обрабатываем каждую
        for line in new_data.split('\n'):
            response_code = parse_log_line(line)
            if response_code:
                # Отправляем код ответа в Telegraf
                send_metric_to_telegraf(response_code)
                # Отправляем сообщение в телеграм
                send_telegram_message(f"Received response code: {response_code}")

    observer.stop()
    observer.join()

# Наблюдатель за изменениями в файле лога Nginx
class NginxLogHandler(FileSystemEventHandler):
    def on_modified(self, event):
        print("Log file modified at:", event.src_path)
        handle_new_log_entry()

if __name__ == "__main__":
    # Проверка наличия файла лога
    if os.path.exists(nginx_log_path):
        print("Nginx log found at:", nginx_log_path)
        
        while True:
            handle_new_log_entry()
            time.sleep(1)
    else:
        print("Nginx log not found at:", nginx_log_path)