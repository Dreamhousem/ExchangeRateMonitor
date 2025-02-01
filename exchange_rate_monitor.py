import time
import json
import requests
from datetime import datetime, timedelta

# URL API Национального банка Республики Беларусь
API_URL = "https://api.nbrb.by/exrates/rates?periodicity=0"

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
    """Запрашивает курсы валют на завтрашний день через API НБ РБ."""
    print("Запрос данных с API...")
    response = requests.get(API_URL)
    if response.status_code == 200:
        print("Данные успешно получены.")
        data = response.json()
        rates = {}
        for currency, cur_id in CURRENCIES.items():
            currency_data = next((item for item in data if item.get("Cur_ID") == cur_id), None)
            if currency_data is None:
                print(f"Ошибка: Не найдены данные для {currency}. Полный ответ API: {data}")
                continue
            if "Cur_OfficialRate" not in currency_data:
                print(f"Ошибка: В данных для {currency} отсутствует ключ 'Cur_OfficialRate'. Ответ API: {currency_data}")
                continue
            rates[currency] = currency_data["Cur_OfficialRate"]
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
        print("Файл с курсами отсутствует или поврежден. Создаётся новый.")
        return {}  # Если файл не найден или повреждён, возвращаем пустой словарь

def save_rates(rates):
    """Сохраняет текущие курсы валют с временной меткой в локальный файл."""
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
        "rates": rates
    }
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)
    print("Курсы валют сохранены с временной меткой.")


def log_change(currency, old_rate, new_rate):
    """Фиксирует изменение курса валюты в лог-файл."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {currency}: {old_rate} -> {new_rate}\n"
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry)
    print(f"Зафиксировано изменение курса: {log_entry.strip()}")

def monitor_exchange_rates():
    """Запускает мониторинг курсов валют в рабочие часы."""
    print("Запуск мониторинга курсов валют...")
    previous_rates = load_previous_rates()
    if not previous_rates:
        print("Сохранение начальных курсов валют...")
        previous_rates = fetch_exchange_rates()
        if previous_rates:
            save_rates(previous_rates)
        else:
            print("Ошибка при получении данных с API НБ РБ.")
        return
    while True:
        now = datetime.now()
        if START_HOUR <= now.hour < END_HOUR:
            print("Проверка курсов валют...")
            current_rates = fetch_exchange_rates()
            if current_rates:
                for currency, new_rate in current_rates.items():
                    old_rate = previous_rates.get(currency)
                    if old_rate and new_rate != old_rate:
                        log_change(currency, old_rate, new_rate)
                        previous_rates[currency] = new_rate
                save_rates(previous_rates)
        else:
            print("Вне рабочего времени. Ожидание...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_exchange_rates()
