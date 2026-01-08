import json
import logging
import os
from datetime import datetime, time
from typing import Dict, List

import pandas as pd
import requests
from dotenv import load_dotenv

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Загрузка пользовательских настроек

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USER_SETTINGS_PATH = os.path.join(BASE_DIR, "user_settings.json")

try:
    with open(USER_SETTINGS_PATH, "r", encoding="utf-8") as f:
        USER_SETTINGS = json.load(f)
except FileNotFoundError:
    USER_SETTINGS = {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL", "AMZN", "GOOGL", "MSFT", "TSLA"],
    }
    logger.warning(
        "Файл user_settings.json не найден. Используются настройки по умолчанию."
    )


# Конфигурация из .env
load_dotenv("../.env")

CURRENCY_API_URL = os.getenv("CURRENCY_API_URL")
CURRENCY_API_KEY = os.getenv("CURRENCY_API_KEY")

STOCKS_API_URL = os.getenv("STOCKS_API_URL")
STOCKS_API_KEY = os.getenv("STOCKS_API_KEY")


def time_response() -> str | None:
    """Возвращает приветствие в зависимости от времени суток"""
    date_hour = int(datetime.now().hour)

    if 6 < date_hour <= 12:
        return "Доброе утро"
    elif 12 < date_hour <= 18:
        return "Добрый день"
    elif 18 < date_hour <= 24:
        return "Добрый вечер"
    elif 0 <= date_hour <= 6:
        return "Доброй ночи"
    return None


def filter_data_by_date(df: pd.DataFrame, target_date: str) -> pd.DataFrame:
    """
    Фильтрует данные с начала месяца до указанной даты

    Args:
        df: DataFrame с данными операций
        target_date: Дата в формате 'YYYY-MM-DD HH:MM:SS'

    Returns:
        Отфильтрованный DataFrame
    """
    try:
        target_datetime = datetime.strptime(target_date, "%Y-%m-%d %H:%M:%S")
        start_of_month = target_datetime.replace(day=1)

        # Преобразуем даты в DataFrame
        df["Дата операции"] = pd.to_datetime(
            df["Дата операции"], format="%d.%m.%Y %H:%M:%S"
        )

        # Фильтруем данные
        mask = (df["Дата операции"] >= start_of_month) & (
            df["Дата операции"] <= target_datetime
        )
        return df[mask].copy()
    except Exception as e:
        logger.error(f"Ошибка при фильтрации данных: {e}")
        return df


def get_card_summary(filtered_df: pd.DataFrame) -> List[Dict]:
    """
    Рассчитывает статистику по картам

    Args:
        filtered_df: Отфильтрованный DataFrame с операциями

    Returns:
        Список словарей со статистикой по картам
    """
    card_stats = []

    # Убираем пустые номера карт
    df_with_cards = filtered_df[filtered_df["Номер карты"].notna()]

    if df_with_cards.empty:
        return card_stats

    # Группируем по картам
    for card_num in df_with_cards["Номер карты"].unique():
        card_data = df_with_cards[df_with_cards["Номер карты"] == card_num]

        # Фильтруем только расходы (отрицательные суммы)
        expenses = card_data[card_data["Сумма операции"] < 0]
        total_expenses = abs(expenses["Сумма операции"].sum())

        # Расчет кэшбэка (1 рубль на каждые 100 рублей расходов)
        cashback = total_expenses // 100

        card_stats.append(
            {
                "card_last_digits": (
                    str(card_num)[-4:] if len(str(card_num)) >= 4 else str(card_num)
                ),
                "total_expenses": round(total_expenses, 2),
                "cashback": int(cashback),
            }
        )

    return card_stats


def get_top_transactions(filtered_df: pd.DataFrame, top_n: int = 5) -> List[Dict]:
    """
    Возвращает топ-N транзакций по сумме платежа

    Args:
        filtered_df: Отфильтрованный DataFrame с операциями
        top_n: Количество топовых транзакций

    Returns:
        Список словарей с информацией о транзакциях
    """
    # Берем только расходы для анализа
    expenses_df = filtered_df[filtered_df["Сумма платежа"] < 0].copy()

    if expenses_df.empty:
        return []

    # Сортируем по абсолютной сумме платежа
    expenses_df["abs_amount"] = abs(expenses_df["Сумма платежа"])
    top_expenses = expenses_df.nlargest(top_n, "abs_amount")

    top_transactions = []
    for _, row in top_expenses.iterrows():
        transaction = {
            "date": row["Дата операции"].strftime("%d.%m.%Y %H:%M:%S"),
            "amount": round(abs(row["Сумма платежа"]), 2),
            "category": row["Категория"],
            "description": row["Описание"],
            "card_last_digits": (
                str(row["Номер карты"])[-4:] if pd.notna(row["Номер карты"]) else "N/A"
            ),
        }
        top_transactions.append(transaction)

    return top_transactions


def get_currency_rates() -> Dict[str, float]:
    """
    Получает курсы валют из API

    Returns:
        Словарь с курсами валют
    """

    try:

        url = f"{CURRENCY_API_URL}{CURRENCY_API_KEY}/latest/RUB"

        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            data = response.json()
            rates = data.get("rates", {})

            # Фильтруем только нужные валюты
            user_currencies = USER_SETTINGS.get("user_currencies", [])
            filtered_rates = {}

            for currency in user_currencies:
                if currency in rates:
                    # Конвертируем курс RUB к другой валюте
                    filtered_rates[currency] = round(1 / rates[currency], 4)

            logger.info(f"Получены курсы валют: {list(filtered_rates.keys())}")
            return filtered_rates

    except requests.exceptions.Timeout:
        logger.error("Таймаут при получении курсов валют")
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка соединения при получении курсов валют")
    except Exception as e:
        logger.error(f"Ошибка при получении курсов валют: {e}")

    return {}


def get_stock_prices() -> list:
    """
    Получает цены на акции из Financial Modeling Prep API
    Делает отдельный запрос для каждой акции

    Returns:
        Список словарей с информацией об акциях в формате:
        [
            {"stock": "AAPL", "price": 150.12},
            {"stock": "AMZN", "price": 3173.18},
            ...
        ]
    """
    stocks_list = []
    user_stocks = USER_SETTINGS.get("user_stocks", [])

    if not user_stocks:
        logger.warning("Нет акций для отслеживания в настройках")
        return stocks_list

    for stock in user_stocks:
        try:
            url = f"{STOCKS_API_URL}{stock}&apikey={STOCKS_API_KEY}"
            response = requests.get(url, timeout=20)

            if response.status_code == 200:
                data = response.json()

                if data and isinstance(data, list) and len(data) > 0:
                    stock_data = data[0]

                    stocks_list.append(
                        {"stock": stock, "price": round(stock_data.get("price", 0), 2)}
                    )

                    logger.debug(
                        f"Получена цена для {stock}: ${stocks_list[-1]['price']}"
                    )
                else:
                    logger.warning(f"Пустой ответ для акции {stock}")
                    stocks_list.append(
                        {"stock": stock, "price": 0, "error": "Данные не получены"}
                    )

            elif response.status_code == 429:
                logger.warning(f"Превышен лимит запросов для акции {stock}")
                stocks_list.append(
                    {"stock": stock, "price": 0, "error": "Превышен лимит запросов API"}
                )
                # Делаем паузу перед следующим запросом
                time.sleep(1)

        except requests.exceptions.Timeout:
            logger.error(f"Таймаут при запросе акции {stock}")
            stocks_list.append({"stock": stock, "price": 0})

        except requests.exceptions.ConnectionError:
            logger.error(f"Ошибка соединения для акции {stock}")
            stocks_list.append({"stock": stock, "price": 0})

        except Exception as e:
            logger.error(f"Неизвестная ошибка для акции {stock}: {e}")
            stocks_list.append({"stock": stock, "price": 0})

    # Логируем результат
    successful_stocks = [s for s in stocks_list if s["price"] > 0]
    logger.info(
        f"Успешно получены данные по {len(successful_stocks)} из {len(user_stocks)} акций"
    )

    return stocks_list


def create_summary_json(df: pd.DataFrame, target_date: str) -> Dict:
    """
    Создает JSON-ответ с сводной информацией

    Args:
        df: DataFrame с данными операций
        target_date: Дата в формате 'YYYY-MM-DD HH:MM:SS' для фильтрации

    Returns:
        Словарь с данными в требуемом формате
    """
    # Фильтруем данные по дате
    filtered_df = filter_data_by_date(df, target_date)

    # Получаем данные для JSON
    greeting = time_response()
    cards = get_card_summary(filtered_df)
    top_transactions = get_top_transactions(filtered_df)
    currency_rates_data = get_currency_rates()
    stock_prices_data = get_stock_prices()

    # Преобразуем данные в требуемый формат
    result = {
        "greeting": greeting,
        "cards": [],
        "top_transactions": top_transactions,
        "currency_rates": [],
        "stock_prices": stock_prices_data
    }

    # Форматируем данные карт
    for card in cards:
        result["cards"].append({
            "last_digits": card["card_last_digits"],
            "total_spent": round(card["total_expenses"], 2),
            "cashback": round(card["cashback"], 2)
        })

    # Форматируем курсы валют
    for currency, rate in currency_rates_data.items():
        result["currency_rates"].append({
            "currency": currency,
            "rate": rate
        })

    return result