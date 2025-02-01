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
    """Запрашивает курсы валют через API НБ РБ."""
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

def determine_target_dates():
    """Определяет даты, на которые устанавливается курс, с учётом выходных и понедельника."""
    today = datetime.today()
    tomorrow = today + timedelta(days=1)
    weekday = today.weekday()
    
    if weekday == 4:  # Пятница, фиксируем курс на понедельник
        monday = today + timedelta(days=3)
        return [today.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d"), monday.strftime("%Y-%m-%d")]
    elif weekday == 3:  # Четверг, фиксируем курс на пятницу, субботу и воскресенье
        weekend = today + timedelta(days=3)
        return [today.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d"), weekend.strftime("%Y-%m-%d")]
    else:
        return [today.strftime("%Y-%m-%d"), tomorrow.strftime("%Y-%m-%d")]

def save_rates(rates):
    """Сохраняет курсы валют с временной меткой в локальный файл на несколько дней вперёд."""
    target_dates = determine_target_dates()
    data = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rates": {date: rates for date in target_dates}
    }
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)
    print("Курсы валют сохранены с временной меткой на несколько дней.")

def log_change(currency, old_rate, new_rate):
    """Фиксирует изменение курса валюты в лог-файл."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {currency}: {old_rate} -> {new_rate}\n"
    with open(LOG_FILE, "a") as log_file:
        log_file.write(log_entry)
    print(f"Зафиксировано изменение курса: {log_entry.strip()}\n")

def monitor_exchange_rates():
    """Запускает мониторинг курсов валют в рабочие часы."""
    print("Запуск мониторинга курсов валют...")
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
