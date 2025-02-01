import time
import json
import requests
from datetime import datetime

# URL API Национального банка Республики Беларусь
API_URL = "https://api.nbrb.by/exrates/currencies"

# Словарь с кодами валют (USD, EUR, RUB, CNY)
CURRENCIES = {"USD": 431, "EUR": 451, "RUB": 456, "CNY": 508}

# Файлы для хранения данных
DATA_FILE = "exchange_rates.json"
LOG_FILE = "exchange_rate_changes.log"

# Интервал проверки (10 минут) и рабочие часы (9:00 - 16:00)
CHECK_INTERVAL = 600  # 600 секунд = 10 минут
START_HOUR = 9
END_HOUR = 16

def fetch_exchange_rates():
    """Запрашивает текущие курсы валют через API НБ РБ."""
    print("Запрос данных с API...")
    response = requests.get(API_URL)
    if response.status_code == 200:
        print("Данные успешно получены.")
        data = response.json()
        rates = {}
        for currency, cur_id in CURRENCIES.items():
            for item in data:
                if item["Cur_ID"] == cur_id:
                    rates[currency] = item["Cur_OfficialRate"]  # Извлекаем курс валюты
                    break
        print("Полученные курсы валют:", rates)
        return rates
    print("Ошибка при запросе данных с API.")
    return None

def load_previous_rates():
    """Загружает сохранённые курсы валют из локального файла."""
    try:
        with open(DATA_FILE, "r") as file:
            print("Загрузка предыдущих курсов валют...")
            return json.load(file)  # Загружаем JSON-данные
    except (FileNotFoundError, json.JSONDecodeError):
        print("Файл с курсами отсутствует или поврежден. Используется пустой словарь.")
        return {}  # Если файл не найден или повреждён, возвращаем пустой словарь

def save_rates(rates):
    """Сохраняет текущие курсы валют в локальный файл."""
    with open(DATA_FILE, "w") as file:
        json.dump(rates, file, indent=4)  # Записываем данные в формате JSON
    print("Курсы валют сохранены.")

def log_change(currency, old_rate, new_rate):
    """Фиксирует изменение курса валюты в лог-файл."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Получаем текущее время
    log_entry = f"[{timestamp}] {currency}: {old_rate} -> {new_rate}\n"
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry)  # Записываем лог изменений
    print(f"Зафиксировано изменение курса: {log_entry.strip()}")

def monitor_exchange_rates():
    """Запускает мониторинг курсов валют в рабочие часы."""
    print("Запуск мониторинга курсов валют...")
    previous_rates = load_previous_rates()  # Загружаем предыдущие курсы
    if not previous_rates:
        print("Сохранение начальных курсов валют...")
        previous_rates = fetch_exchange_rates()
        if previous_rates:
            save_rates(previous_rates)  # Если данные получены, сохраняем их
        else:
            print("Ошибка при получении данных с API НБ РБ.")
        return

    while True:
        now = datetime.now()
        if START_HOUR <= now.hour < END_HOUR:  # Проверяем, в рабочие ли часы выполняется проверка
            print("Проверка курсов валют...")
            current_rates = fetch_exchange_rates()
            if current_rates:
                for currency, new_rate in current_rates.items():
                    old_rate = previous_rates.get(currency)
                    if old_rate and new_rate != old_rate:
                        log_change(currency, old_rate, new_rate)  # Фиксируем изменение курса
                        previous_rates[currency] = new_rate  # Обновляем сохранённые данные
                save_rates(previous_rates)  # Сохраняем обновленные курсы
        else:
            print("Вне рабочего времени. Ожидание...")
        time.sleep(CHECK_INTERVAL)  # Ожидаем заданное время перед следующей проверкой

if __name__ == "__main__":
    monitor_exchange_rates()  # Запускаем мониторинг
