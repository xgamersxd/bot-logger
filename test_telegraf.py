import requests

# URL Telegraf для приема метрик
telegraf_url = "http://localhost:8186/write?db=telegraf"

# Функция для отправки метрик в Telegraf
def send_metric_to_telegraf(metric_name, metric_value):
    metric_data = f"{metric_name} value={metric_value}"
    response = requests.post(telegraf_url, data=metric_data)
    if response.status_code == 204:
        print(f"Metric '{metric_name}' sent successfully with value {metric_value}")
    else:
        print(f"Failed to send metric '{metric_name}'")
