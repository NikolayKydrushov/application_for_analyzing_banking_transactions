import math
from datetime import datetime
from typing import Dict, List, Any
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def investment_bank(month: str, transactions: List[Dict[str, Any]], limit: int) -> float:
    """
       Рассчитывает сумму для инвесткопилки через округление трат.

       Args:
           month: Месяц, для которого рассчитывается отложенная сумма, строка в формате 'DD.MM.YYYY HH:MM:SS'
           transactions: Список словарей с информацией о:
               - 'Дата операции': дата в формате 'DD.MM.YYYY HH:MM:SS'
               - 'Сумма операции': сумма транзакции в оригинальной валюте (число)
           limit: Предел для округления суммы операций - целое число (10, 50, 100 и т.д.)

       Returns:
           Сумма, которую удалось бы отложить в инвесткопилку
    """

    total_investment = 0.00

    try:
        # Проверяем корректность месяца
        datetime.strptime(month, '%Y-%m')
    except ValueError:
        logger.error(f"Неверный формат месяца: {month}. Ожидается 'DD.MM.YYYY HH:MM:SS'")
        return 0.00

    if limit <= 0:
        logger.warning(f"Лимит должен быть положительным числом. Получено: {limit}")
        return 0.00

    for transaction in transactions:
        try:
            # Проверяем необходимые поля
            if 'Дата операции' not in transaction or 'Сумма операции' not in transaction:
                logger.warning("Транзакция не содержит необходимых полей")
                continue

            # Парсим дату операции
            op_date = datetime.strptime(transaction['Дата операции'], '%d.%m.%Y %H:%M:%S')

            # Проверяем, относится ли транзакция к указанному месяцу
            if op_date.strftime('%Y-%m') != month:
                continue

            # Получаем сумму операции
            amount = float(transaction['Сумма операции'])

            # Если сумма отрицательная (трата), то округляем
            if amount < 0:
                # Берем абсолютное значение для округления
                abs_amount = abs(amount)

                # Округляем до ближайшего кратного limit
                rounded_amount = math.ceil(abs_amount / limit) * limit

                # Вычисляем разницу (инвестируемая сумма)
                investment = rounded_amount - abs_amount

                if investment > 0:
                    total_investment += investment
                    logger.debug(f"Транзакция {op_date.date()}: {abs_amount} ₽ -> {rounded_amount} ₽, отложено: {investment} ₽")

        except (ValueError, KeyError) as e:
            logger.warning(f"Ошибка обработки транзакции: {e}")
            continue

    logger.info(f"За месяц {month} с лимитом округления {limit} ₽ отложено: {total_investment:.2f} ₽")
    return round(total_investment, 2)