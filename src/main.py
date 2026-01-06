import json
import os
from pathlib import Path
from views import *

if __name__ == "__main__":
    # Определяем путь к корневой директории проекта
    PROJECT_ROOT = Path(__file__).parent.parent
    DATA_DIR = PROJECT_ROOT / "data"
    OPERATIONS_FILE_PATH = DATA_DIR / "operations.xlsx"

    # Загрузка данных из Excel
    try:
        df = pd.read_excel(OPERATIONS_FILE_PATH, sheet_name='Отчет по операциям')

        # Тестовый вызов
        test_date = '2021-12-31 23:59:59'
        response = create_summary_json(df, test_date)

        print(json.dumps(response, ensure_ascii=False, indent=2))

    except FileNotFoundError:
        print(f"Файл не найден: {OPERATIONS_FILE_PATH}")
    except Exception as e:
        print(f"Ошибка: {e}")