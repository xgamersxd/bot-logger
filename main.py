import re
import time
import os

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

from test_telegraf import send_metric_to_telegraf

# Паттерн для поиска кодов ответов в логе Nginx
log_pattern = re.compile(r'" (\d{3}) ')

# Путь к файлу лога Nginx
nginx_log_path = "/var/log/nginx/access.log"

# Переменная для хранения последней позиции в файле
last_position = 0

# Функция для парсинга строки лога и извлечения кода ответа
def parse_log_line(line):
    match = log_pattern.search(line)
    if match:
        return match.group(1)
    else:
        return None

# Функция для отправки сообщения в телеграм
# def send_telegram_message(message):
#     url = f"https://api.telegram.org/bot5611986812:AAHNOJBAXn34rMA83sPi0Cgh5dPKgzSRLOY/sendMessage"
#     params = {"chat_id": "-1002108620285", "text": message}
#     requests.post(url, params=params)

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
                send_metric_to_telegraf("nginx_http_answer", response_code)
                # Отправляем сообщение в телеграм
                #send_telegram_message(f"Received response code: {response_code}")

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