import os

import pandas as pd
import logging
from dotenv import load_dotenv

load_dotenv("../.env")

PATH_FILE = os.getenv("PATH_FILE")

# PATH_FILE="C:/Skypro/application_for_analyzing_banking_transactions/data/operations.xlsx"


logger = logging.getLogger("utils")
logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("../logs/utils.log", mode="w", encoding="utf-8")
file_formatter = logging.Formatter(
    "%(asctime)s %(filename)s %(levelname)s: %(message)s"
)
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


def open_file(file_path: str) -> list[dict]:
    """
    Функция открытия и чтения файла operations.xlsx

    Args:
        file_path: Путь до файла operations.xlsx

    Returns:
        Возвращает список словарей с данными из указанного файла
    """
    try:
        reader_xlsx = pd.read_excel(file_path)
        logger.info('Успешное преобразование данных')
        return reader_xlsx.to_dict("records")
    except FileNotFoundError as fnf:
        logger.error(f"Ошибка {fnf}")
        return []
    except TypeError as te:
        logger.error(f"Ошибка {te}")
        return []
    except ValueError as ve:
        logger.error(f"Ошибка {ve}")
        return []

print(open_file(PATH_FILE))