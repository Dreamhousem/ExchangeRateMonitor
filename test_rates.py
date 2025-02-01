import unittest
from unittest.mock import patch, mock_open
import json
from datetime import datetime, timedelta
from exchange_rate_monitor import fetch_exchange_rates, load_previous_rates, save_rates, log_change

class TestExchangeRateMonitor(unittest.TestCase):
    """Тесты для проверки работы функций мониторинга курсов валют."""
    
    @patch("exchange_rate_monitor.requests.get")
    def test_fetch_exchange_rates(self, mock_get):
        """Тестирует получение курсов валют через API, проверяя корректность извлечённых данных."""
        # Имитация JSON-ответа от API
        mock_response = [
            {"Cur_ID": 431, "Cur_OfficialRate": 2.5},
            {"Cur_ID": 451, "Cur_OfficialRate": 3.0},
            {"Cur_ID": 456, "Cur_OfficialRate": 0.034},
            {"Cur_ID": 508, "Cur_OfficialRate": 0.39}
        ]
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_response
        
        # Ожидаемый результат
        expected_rates = {"USD": 2.5, "EUR": 3.0, "RUB": 0.034, "CNY": 0.39}
        
        # Проверяем, совпадают ли данные
        self.assertEqual(fetch_exchange_rates(), expected_rates)
    
    @patch("builtins.open", new_callable=mock_open, read_data='{"USD": 2.5, "EUR": 3.0}')
    def test_load_previous_rates(self, mock_file):
        """Тестирует загрузку сохранённых курсов валют из файла."""
        expected_data = {"USD": 2.5, "EUR": 3.0}
        self.assertEqual(load_previous_rates(), expected_data)

    @patch("builtins.open", new_callable=mock_open)
    def test_save_rates(self, mock_file):
        """Тестирует сохранение курсов валют в файл."""
        rates = {"USD": 2.6, "EUR": 3.1}
        
        # Ожидаемая структура файла с временной меткой
        expected_data = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "date": (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d"),
            "rates": rates
        }
        
        save_rates(rates)
        
        # Проверяем, что файл был записан корректно
        handle = mock_file()
        written_data = "".join(call.args[0] for call in handle.write.call_args_list)
        self.assertEqual(written_data, json.dumps(expected_data, indent=4))

    @patch("builtins.open", new_callable=mock_open)
    def test_log_change(self, mock_file):
        """Тестирует запись изменений курса валют в лог-файл."""
        log_change("USD", 2.5, 2.6)
        
        # Проверяем, что запись в файл была выполнена
        mock_file().write.assert_called()

    @patch("exchange_rate_monitor.fetch_exchange_rates")
    def test_simulated_10_days(self, mock_fetch):
        """Тестирует имитацию изменения курса в течение 10 дней, учитывая выходные."""
        base_rate = 3.5
        simulated_rates = []
        
        for i in range(10):
            date = datetime.today() + timedelta(days=i)
            weekday = date.weekday()

            # В четверг устанавливаем курс на пятницу, субботу и воскресенье
            if weekday == 3:  
                rate = base_rate + 0.05  
            elif weekday in [4, 5, 6]:  # Пятница, суббота, воскресенье - курс остается как в четверг
                rate = simulated_rates[-1] if simulated_rates else base_rate
            elif weekday == 0:  # В понедельник используется пятничный курс
                rate = simulated_rates[-1]
            else:  # Обычные дни (вторник, среда) — курс постепенно меняется
                rate = base_rate + 0.02 * i
            
            simulated_rates.append(rate)
            mock_fetch.return_value = {
                "USD": rate, "EUR": rate + 0.1, "RUB": rate - 0.1, "CNY": rate * 0.7
            }
            save_rates(mock_fetch.return_value)

        # Проверяем, что курс в субботу такой же, как в пятницу
        self.assertEqual(simulated_rates[5], simulated_rates[4])  # Суббота = Пятница
        self.assertEqual(simulated_rates[6], simulated_rates[4])  # Воскресенье = Пятница
        self.assertEqual(simulated_rates[0], simulated_rates[9])  # Последний день теста не должен сильно отличаться


if __name__ == "__main__":
    unittest.main()
