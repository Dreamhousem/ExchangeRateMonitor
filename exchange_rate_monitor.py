import time
import json
import requests
from datetime import datetime, timedelta

# URL API Национального банка Республики Беларусь
API_URL = "https://api.nbrb.by/exrates/rates"

# Словарь с кодами валют (USD, EUR, RUB, CNY)
CURRENCIES = {"USD": 431, "EUR": 451, "RUB": 456, "CNY": 508}

# Файлы для хранения данных
DATA_FILE = "exchange_rates.json"
LOG_FILE = "exchange_rate_changes.log"

# Интервал проверки (10 минут) и рабочие часы (9:00 - 16:00)
CHECK_INTERVAL = 600  # 600 секунд = 10 минут
START_HOUR = 9
END_HOUR = 16

def fetch_exchange_rates(date=None):
    """Запрашивает курсы валют через API НБ РБ на указанную дату."""
    params = {"periodicity": 0}
    if date:
        params["ondate"] = date.strftime("%Y-%m-%d")
    
    print(f"Запрос данных с API на {params.get('ondate', 'сегодня')}...")
    response = requests.get(API_URL, params=params)
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
    dates = [today, tomorrow]
    
    if weekday == 4:  # Пятница, фиксируем курс на понедельник
        monday = today + timedelta(days=3)
        dates.append(monday)
    elif weekday == 3:  # Четверг, фиксируем курс на пятницу, субботу и воскресенье
        weekend = today + timedelta(days=3)
        dates.append(weekend)
    elif weekday in [5, 6]:  # Суббота или воскресенье, используем курс пятницы
        friday = today - timedelta(days=(weekday - 4))
        monday = today + timedelta(days=(7 - weekday))
        dates = [friday, today, monday]  
    
    return dates

def save_rates():
    """Сохраняет курсы валют с временной меткой в локальный файл на несколько дней вперёд."""
    target_dates = determine_target_dates()
    data = {"timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "rates": {}}
    
    for date in target_dates:
        rates = fetch_exchange_rates(date)
        if rates:
            data["rates"][date.strftime("%Y-%m-%d")] = rates
    
    with open(DATA_FILE, "w") as file:
        json.dump(data, file, indent=4)
    print("Курсы валют сохранены с временной меткой на несколько дней.")

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
    save_rates()
    while True:
        now = datetime.now()
        if START_HOUR <= now.hour < END_HOUR:
            print("Проверка курсов валют...")
            save_rates()
        else:
            print("Вне рабочего времени. Ожидание...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    monitor_exchange_rates()
