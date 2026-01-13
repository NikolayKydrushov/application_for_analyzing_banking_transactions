import pytest
import pandas as pd
from datetime import datetime, timedelta
import json
import os
from unittest.mock import patch, mock_open
from src.reports import report_writer, spending_by_category


def test_spending_by_category_basic_filtering(sample_transactions_df):
    """Тест базовой фильтрации по категории"""
    result = spending_by_category(sample_transactions_df, "Медицина", "31.12.2021")

    # Проверяем тип результата
    assert isinstance(result, pd.DataFrame)

    # Проверяем количество строк
    assert len(result) == 1

    # Проверяем, что все строки имеют правильную категорию
    assert all(result["Категория"] == "Медицина")

    # Проверяем, что все суммы отрицательные (расходы)
    assert all(result["Сумма операции"] < 0)

    # Проверяем конкретные значения
    assert result["Сумма операции"].iloc[0] == -7240.00


def test_spending_by_category_empty_result():
    """Тест функции с данными, не дающими результатов"""
    empty_df = pd.DataFrame(
        {
            "Дата операции": [],
            "Сумма операции": [],
            "Категория": [],
            "Номер карты": [],
            "Сумма платежа": [],
            "Описание": [],
        }
    )
    result = spending_by_category(empty_df, "Супермаркеты", "31.12.2021")
    assert len(result) == 0
    assert isinstance(result, pd.DataFrame)


def test_spending_by_category_positive_amounts(sample_transactions_df):
    """Тест с положительными суммами (доходы не должны попадать в результат)"""
    result = spending_by_category(sample_transactions_df, "Пополнение", "31.12.2021")
    assert len(result) == 0




# Этот тест нихуя не работает, нужно в фикстуру добавить еще категорию, но вряд ли это поможет
@pytest.mark.parametrize(
    "category, date, expected_count",
    [
        ("Супермаркеты", "31.12.2021", 1),
        ("Каршеринг", "31.12.2021", 1),
        ("Различные товары", "31.12.2021", 0),
        ("Медицина", "31.12.2021", 1),
        ("Несуществующая", "31.12.2021", 0),
        ("Супермаркеты", "06.12.2021", 0),
    ],
)
def test_spending_by_category_parametrized(
    extended_sample_transaction_df, category, date, expected_count
):
    """Параметризованный тест функции spending_by_category"""
    result = spending_by_category(extended_sample_transaction_df, category, date)
    assert len(result) == expected_count

    if expected_count > 0:
        # Проверяем, что все строки имеют правильную категорию
        assert all(result["Категория"] == category)
        # Проверяем, что все суммы отрицательные
        assert all(result["Сумма операции"] < 0)


def test_spending_by_category_sorting(sample_transactions_df):
    """Тест сортировки результатов по дате"""
    result = spending_by_category(sample_transactions_df, "Супермаркеты", "31.12.2021")

    # Проверяем, что данные отсортированы по убыванию даты
    dates = pd.to_datetime(result["Дата операции"])
    assert all(dates[i] >= dates[i + 1] for i in range(len(dates) - 1))


def test_report_writer_decorator_with_dataframe(extended_sample_transaction_df, tmp_path):
    """Тест декоратора report_writer с DataFrame"""

    # Создаем временный файл с использованием фикстуры tmp_path
    temp_json_file = tmp_path / "test_report.json"

    # Создаем декорированную функцию для теста
    @report_writer(filename=str(temp_json_file))
    def test_function():
        return spending_by_category(extended_sample_transaction_df, "Супермаркеты", "31.12.2021")

    # Вызываем функцию
    result = test_function()

    # Проверяем, что файл создан
    assert temp_json_file.exists()

    # Проверяем содержимое файла
    with open(temp_json_file, 'r', encoding='utf-8') as f:
        report_data = json.load(f)

    # Проверяем структуру отчета
    assert "report_name" in report_data
    assert "generated_at" in report_data
    assert "data" in report_data

    assert report_data["report_name"] == "test_function"

    # Проверяем данные
    assert len(report_data["data"]) == 1
    assert all(item["Категория"] == "Супермаркеты" for item in report_data["data"])

    # Проверяем, что datetime объекты преобразованы в строки
    for item in report_data["data"]:
        assert isinstance(item["Дата операции"], str)


def test_report_writer_decorator_with_dict(tmp_path):
    """Тест декоратора report_writer со словарем"""

    test_dict = {"key1": "value1", "key2": 123, "date": datetime(2023, 1, 1)}

    # Используем временный файл в директории tmp_path
    temp_file = tmp_path / "report_result.json"

    # Создаем декорированную функцию с указанием конкретного файла
    @report_writer(filename=str(temp_file))
    def test_function():
        return test_dict

    # Вызываем функцию
    result = test_function()

    # Проверяем, что файл создан
    assert temp_file.exists()

    # Проверяем содержимое файла
    with open(temp_file, 'r', encoding='utf-8') as f:
        report_data = json.load(f)

    # Проверяем преобразование datetime в строку
    assert isinstance(report_data["data"]["date"], str)
    assert report_data["data"]["date"] == "2023-01-01T00:00:00"


def test_spending_by_category_column_names(sample_transactions_df):
    """Тест сохранения имен столбцов в результате"""
    result = spending_by_category(sample_transactions_df, "Супермаркеты", "31.12.2021")

    expected_columns = ["Дата операции", "Номер карты", "Сумма операции",
                        "Сумма платежа", "Категория", "Описание"]

    assert list(result.columns) == expected_columns

def test_spending_by_category_reset_index(extended_sample_transaction_df):
    """Тест сброса индекса в результате"""
    result = spending_by_category(extended_sample_transaction_df, "Супермаркеты", "31.12.2021")

    # Проверяем, что индекс сброшен и начинается с 0
    assert list(result.index) == [0]

