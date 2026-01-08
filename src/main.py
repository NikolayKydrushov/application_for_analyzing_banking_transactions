import json
import os
from pathlib import Path
import logging
from views import *
from services import investment_bank

if __name__ == "__main__":
    # Определяем путь к корневой директории проекта
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    OPERATIONS_FILE_PATH = DATA_DIR / "operations.xlsx"

    # Настройка логирования
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Загрузка данных из Excel
    try:
        df = pd.read_excel(OPERATIONS_FILE_PATH, sheet_name='Отчет по операциям')

        transactions = df[['Дата операции', 'Сумма операции']].to_dict('records')

        # Пример параметров для функции
        month = '2021-12'  # месяц в формате YYYY-MM
        limit = 10  # лимит округления

        # Вызов функции investment_bank
        investment_result = investment_bank(month, transactions, limit)
        print(f"\nРезультат работы investment_bank: {investment_result:.2f} ₽")

        # Тестовый вызов
        # test_date = '2021-12-31 23:59:59'
        # response = create_summary_json(df, test_date)
        #
        # print(json.dumps(response, ensure_ascii=False, indent=2))

    except FileNotFoundError:
        print(f"Файл не найден: {OPERATIONS_FILE_PATH}")
    except Exception as e:
        print(f"Ошибка: {e}")