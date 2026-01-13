
import pytest
import pandas as pd
from unittest.mock import patch, Mock, MagicMock


from src import views



# Тесты для time_response()
@pytest.mark.parametrize("hour,expected", [
    ("", None),  # Граничное значение
    (12, "Доброе утро"),  # Граничное значение
    (18, "Добрый день"),  # Граничное значение
    (24, "Добрый вечер"),  # Граничное значение
    (0, "Доброй ночи"),  # Граничное значение
    ])
def test_time_response(hour,expected):
    """Тест для утреннего приветствия"""
    with patch('src.views.datetime') as mock_datetime:
        mock_datetime.now.return_value.hour = hour
        result = views.time_response()
        assert result == expected


# Тесты для filter_data_by_date()
def test_filter_data_by_date_valid(sample_transactions_df):
    """Тест фильтрации данных по валидной дате"""
    target_date = "2021-12-31 23:59:59"
    result = views.filter_data_by_date(sample_transactions_df, target_date)

    # Проверяем, что отфильтрованы только транзакции января
    assert len(result) == 4
    # result["Дата операции"] = pd.to_datetime(result["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    assert all(result["Дата операции"].dt.month == 12)


def test_filter_data_by_date_invalid_format(sample_transactions_df):
    """Тест фильтрации с неверным форматом даты"""
    target_date = "invalid-date-format"
    result = views.filter_data_by_date(sample_transactions_df, target_date)

    # При ошибке должна вернуться исходная таблица
    assert len(result) == len(sample_transactions_df)


def test_filter_data_by_date_empty_df(empty_transactions_df):
    """Тест фильтрации пустого DataFrame"""
    target_date = "2021-12-31 23:59:59"
    result = views.filter_data_by_date(empty_transactions_df, target_date)
    assert len(result) == 0


# Тесты для get_card_summary()
def test_get_card_summary_valid(sample_transactions_df):
    """Тест расчета статистики по картам"""
    filtered_df = sample_transactions_df.copy()
    filtered_df["Дата операции"] = pd.to_datetime(filtered_df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    result = views.get_card_summary(filtered_df)

    assert len(result) == 3  # 3 уникальные карты

    # Проверяем данные для карты "7197"
    card1 = next(item for item in result if item["card_last_digits"] == "7197")
    assert card1["total_expenses"] == 7400.89  # 160.89 + 7240.00 (только отрицательные операции)
    assert card1["cashback"] == 74  # 7400.89 // 100

    # Проверяем данные для карты "5091"
    card2 = next(item for item in result if item["card_last_digits"] == "5091")
    assert card2["total_expenses"] == 571.07
    assert card2["cashback"] == 5

    # Проверяем данные для карты "4556"
    card3 = next(item for item in result if item["card_last_digits"] == "4556")
    assert card3["total_expenses"] == 0  # Только положительная операция (пополнение)
    assert card3["cashback"] == 0


def test_get_card_summary_no_cards(sample_transactions_df):
    """Тест расчета статистики при отсутствии номеров карт"""
    df_no_cards = sample_transactions_df.copy()
    df_no_cards["Номер карты"] = None

    result = views.get_card_summary(df_no_cards)
    assert result == []


def test_get_card_summary_empty_df(empty_transactions_df):
    """Тест расчета статистики для пустого DataFrame"""
    result = views.get_card_summary(empty_transactions_df)
    assert result == []



# Тесты для get_top_transactions()
def test_get_top_transactions_valid(sample_transactions_df):
    """Тест получения топовых транзакций"""
    filtered_df = sample_transactions_df.copy()
    filtered_df["Дата операции"] = pd.to_datetime(filtered_df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    result = views.get_top_transactions(filtered_df, top_n=2)

    assert len(result) == 2
    assert result[0]["amount"] == 7240.00  # Самая большая транзакция
    assert result[1]["amount"] == 564.00  # Вторая по величине


def test_get_top_transactions_no_expenses():
    """Тест получения топовых транзакций при отсутствии расходов"""
    data = {
        "Дата операции": ["01.01.2021 10:00:00"],
        "Сумма платежа": [100],  # Положительная сумма (доход)
        "Категория": ["Пополнение"],
        "Описание": ["Пополнение счета"],
        "Номер карты": ["1234567890123456"]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    result = views.get_top_transactions(df)
    assert result == []


def test_get_top_transactions_nan_card():
    """Тест с NaN номером карты"""
    data = {
        "Дата операции": ["01.01.2021 10:00:00"],
        "Сумма платежа": [-100],
        "Категория": ["Категория"],
        "Описание": ["Описание"],
        "Номер карты": [None]
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%d.%m.%Y %H:%M:%S")

    result = views.get_top_transactions(df)
    assert result[0]["card_last_digits"] == "N/A"


# Тесты для get_currency_rates()
def test_get_currency_rates_success(mock_user_settings):
    """Тест успешного получения курсов валют"""
    with patch.dict('src.views.USER_SETTINGS', mock_user_settings):
        with patch('src.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "rates": {
                    "USD": 0.011,  # 1 RUB = 0.011 USD
                    "EUR": 0.0095,  # 1 RUB = 0.0095 EUR
                    "GBP": 0.008  # Должна быть отфильтрована
                }
            }
            mock_get.return_value = mock_response

            result = views.get_currency_rates()

            assert "USD" in result
            assert "EUR" in result
            assert "GBP" not in result
            assert result["USD"] == round(1 / 0.011, 4)


def test_get_currency_rates_connection_error(mock_user_settings):
    """Тест ошибки соединения при получении курсов валют"""
    with patch.dict('src.views.USER_SETTINGS', mock_user_settings):
        with patch('src.views.requests.get', side_effect=views.requests.exceptions.ConnectionError):
            result = views.get_currency_rates()
            assert result == {}


def test_get_currency_rates_no_user_currencies():
    """Тест получения курсов валют без настроенных валют"""
    with patch.dict('src.views.USER_SETTINGS', {"user_currencies": []}):
        with patch('src.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"rates": {"USD": 0.011}}
            mock_get.return_value = mock_response

            result = views.get_currency_rates()
            assert result == {}


# Тесты для get_stock_prices()
def test_get_stock_prices_success(mock_user_settings):
    """Тест успешного получения цен на акции"""
    with patch.dict('src.views.USER_SETTINGS', mock_user_settings):
        with patch('src.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = [{"price": 150.25}]
            mock_get.return_value = mock_response

            result = views.get_stock_prices()

            assert len(result) == 3
            assert result[0]["stock"] == "AAPL"
            assert result[0]["price"] == 150.25


def test_get_stock_prices_rate_limit(mock_user_settings):
    """Тест превышения лимита запросов для акций"""
    with patch.dict('src.views.USER_SETTINGS', mock_user_settings):
        with patch('src.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 429  # Too Many Requests
            mock_get.return_value = mock_response

            result = views.get_stock_prices()

            assert len(result) == 6
            assert result[0]["error"] == "Превышен лимит запросов API"


def test_get_stock_prices_timeout(mock_user_settings):
    """Тест таймаута при запросе акций"""
    with patch.dict('src.views.USER_SETTINGS', mock_user_settings):
        with patch('src.views.requests.get', side_effect=views.requests.exceptions.Timeout):
            result = views.get_stock_prices()

            assert len(result) == 3
            assert result[0]["price"] == 0


def test_get_stock_prices_empty_response(mock_user_settings):
    """Тест пустого ответа от API акций"""
    with patch.dict('src.views.USER_SETTINGS', mock_user_settings):
        with patch('src.views.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = []  # Пустой список
            mock_get.return_value = mock_response

            result = views.get_stock_prices()

            assert len(result) == 3
            assert result[0]["error"] == "Данные не получены"

def test_get_stock_prices_no_user_stocks():
    """Тест получения цен на акции без настроенных акций"""
    with patch.dict('src.views.USER_SETTINGS', {"user_stocks": []}):
        result = views.get_stock_prices()
        assert result == []


# Тесты для create_summary_json()
def test_create_summary_json_valid(sample_transactions_df, mock_user_settings):
    """Тест создания JSON-сводки"""
    with patch.dict('src.views.USER_SETTINGS', mock_user_settings):
        with patch('src.views.time_response', return_value="Добрый день"):
            with patch('src.views.get_currency_rates', return_value={"USD": 91.5, "EUR": 100.2}):
                with patch('src.views.get_stock_prices', return_value=[
                    {"stock": "AAPL", "price": 150.25},
                    {"stock": "AMZN", "price": 175.50}
                ]):
                    target_date = "2021-12-31 23:59:59"
                    result = views.create_summary_json(sample_transactions_df, target_date)

                    # Проверяем структуру результата
                    assert "greeting" in result
                    assert "cards" in result
                    assert "top_transactions" in result
                    assert "currency_rates" in result
                    assert "stock_prices" in result

                    # Проверяем содержимое
                    assert result["greeting"] == "Добрый день"
                    assert len(result["cards"]) == 3
                    assert len(result["top_transactions"]) == 3
                    assert len(result["currency_rates"]) == 2
                    assert len(result["stock_prices"]) == 2


def test_create_summary_json_filter_error(sample_transactions_df):
    """Тест создания JSON при ошибке фильтрации"""
    with patch('src.views.filter_data_by_date', side_effect=Exception("Filter error")):
        with patch('src.views.logger') as mock_logger:
            target_date = "2024-01-25 23:59:59"
            result = views.create_summary_json(sample_transactions_df, target_date)

            # Должны быть вызваны остальные функции
            assert "greeting" in result
            assert "cards" in result
            mock_logger.error.assert_called()