import pandas as pd
from typing import Optional, Callable
import json
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def report_writer(filename: Optional[str] = None):
    """
    Декоратор для записи результатов функций-отчетов в файлы.

    Args:
        filename: Имя файла для записи результатов.
                 Если None, генерируется имя на основе имени функции и даты.
    """

    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            # Выполняем функцию-отчет
            result = func(*args, **kwargs)

            # Определяем имя файла
            if filename:
                file_name = filename if filename.endswith('.json') else f"{filename}.json"
            else:
                # Генерация имени файла по умолчанию
                current_date = datetime.now().strftime("%Y%m%d_%H%M%S")
                file_name = f"{func.__name__}_{current_date}.json"

            # Записываем результат в файл
            try:
                if isinstance(result, pd.DataFrame):
                    # Для DataFrame преобразуем в список словарей
                    # Важно: преобразуем Timestamp в строки для сериализации
                    result_data = result.to_dict('records')

                    # Преобразуем все datetime объекты в строки
                    for record in result_data:
                        for key, value in record.items():
                            if pd.isna(value):
                                record[key] = None
                            elif isinstance(value, (pd.Timestamp, datetime)):
                                record[key] = value.isoformat()
                            elif isinstance(value, pd.Timedelta):
                                record[key] = str(value)
                elif isinstance(result, (dict, list)):
                    # Для словарей и списков используем как есть
                    result_data = result

                    # Рекурсивно преобразуем datetime объекты
                    def convert_datetime(obj):
                        if isinstance(obj, dict):
                            return {k: convert_datetime(v) for k, v in obj.items()}
                        elif isinstance(obj, list):
                            return [convert_datetime(item) for item in obj]
                        elif isinstance(obj, (pd.Timestamp, datetime)):
                            return obj.isoformat()
                        elif isinstance(obj, pd.Timedelta):
                            return str(obj)
                        elif pd.isna(obj):
                            return None
                        else:
                            return obj

                    result_data = convert_datetime(result_data)
                else:
                    # Для других типов оборачиваем в словарь
                    result_data = {"result": result}

                # Добавляем метаданные отчета
                report_with_metadata = {
                    "report_name": func.__name__,
                    "generated_at": datetime.now().isoformat(),
                    "data": result_data
                }

                # Сохраняем в JSON файл
                with open(file_name, 'w', encoding='utf-8') as f:
                    json.dump(report_with_metadata, f, ensure_ascii=False, indent=2)
                logger.info(f"Отчет сохранен в JSON файл: {file_name}")

            except Exception as e:
                logger.error(f"Ошибка при записи отчета в файл: {e}")
                import traceback
                logger.error(traceback.format_exc())

            return result

        return wrapper

    return decorator


@report_writer()  # Использование без параметра - файл будет создан автоматически
def spending_by_category(transactions: pd.DataFrame,
                         category: str,
                         date: Optional[str] = None) -> pd.DataFrame:
    """
        Функция возвращает траты по заданной категории за последние три месяца.

        Args:
            transactions: DataFrame с транзакциями
            category: Название категории для фильтрации
            date: Дата, от которой отсчитываются три месяца (в формате 'DD.MM.YYYY')
                  Если None, используется текущая дата

        Returns:
            DataFrame с транзакциями по указанной категории за последние три месяца
    """

    df = transactions.copy()

    # Преобразуем колонки с датами
    df['Дата операции'] = pd.to_datetime(df['Дата операции'], format='%d.%m.%Y %H:%M:%S', errors='coerce')

    # Определяем дату отсчета
    if date:
        end_date = pd.to_datetime(date, format='%d.%m.%Y')
    else:
        end_date = pd.to_datetime(datetime.now())

    # Вычисляем дату начала периода (три месяца назад)
    start_date = end_date - timedelta(days=90)

    # Фильтруем по дате (последние три месяца)
    mask_date = (df['Дата операции'] >= start_date) & (df['Дата операции'] <= end_date)

    # Фильтры
    mask_category = df['Категория'] == category
    mask_expense = df['Сумма операции'] < 0
    filtered_df = df[mask_date & mask_category & mask_expense].copy()

    # Сортируем по дате
    filtered_df = filtered_df.sort_values('Дата операции', ascending=False)

    # Сбрасываем индекс
    filtered_df = filtered_df.reset_index(drop=True)

    # Вычисляем общую сумму расходов по категории
    if len(filtered_df) > 0:
        total_spent = abs(filtered_df['Сумма операции'].sum())
        logger.info(f"Общая сумма расходов по категории '{category}' за последние 3 месяца: {total_spent:.2f} RUB")
        logger.info(f"Найдено {len(filtered_df)} транзакций")
    else:
        logger.info(f"Нет данных по категории '{category}' за последние 3 месяца")

    return filtered_df
