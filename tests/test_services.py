import pytest
from datetime import datetime

from src.services import investment_bank


# Тесты на базовую функциональность
@pytest.mark.parametrize("limit, expected", [
    (10, 9.11 + 6.00 + 1.00),  # 160.89->170(9.11), 64->70(6), 349->350(1)
    (50, 39.11 + 36.00 + 1.00),  # 160.89->200(39.11), 64->100(36), 349->350(1)
    (100, 39.11 + 36.00 + 51.00),  # 160.89->200(39.11), 64->100(36), 349->400(51)
    (1000, 839.11 + 936.00 + 651.00),  # 160.89->1000(839.11), 64->1000(936), 349->1000(651)
])
def test_investment_bank_basic_calculation(sample_transactions, limit, expected):
    """Тест базового расчета с корректными данными."""
    month = "2021-12"
    result = investment_bank(month, sample_transactions, limit)

    assert abs(result - expected) < 0.01  # Учитываем погрешность float


def test_investment_bank_different_month(sample_transactions):
    """Тест фильтрации по месяцу."""
    month = "2021-11"
    limit = 10
    result = investment_bank(month, sample_transactions, limit)

    # Только одна транзакция в ноябре 2021: 200.00->200(0.00) - кратно limit
    expected = 0.00
    assert result == expected


def test_investment_bank_empty_transactions():
    """Тест с пустым списком транзакций."""
    month = "2021-12"
    limit = 10
    result = investment_bank(month, [], limit)
    assert result == 0.00


def test_investment_bank_positive_amounts():
    """Тест с только положительными суммами (не должны учитываться)."""
    transactions = [
        {"Дата операции": "30.12.2021 17:50:30", "Сумма операции": 5046.00},
        {"Дата операции": "30.12.2021 17:50:17", "Сумма операции": 174000.00},
    ]
    month = "2021-12"
    limit = 10
    result = investment_bank(month, transactions, limit)
    assert result == 0.00


# Тесты на обработку некорректных данных
def test_investment_bank_invalid_transactions(invalid_transactions):
    """Тест обработки транзакций с некорректными данными."""
    month = "2021-12"
    limit = 10
    result = investment_bank(month, invalid_transactions, limit)
    assert result == 0.00


def test_investment_bank_mixed_valid_invalid(sample_transactions, invalid_transactions):
    """Тест всех возможных транзакций."""
    month = "2021-12"
    limit = 10
    all_transactions = invalid_transactions + sample_transactions

    # Должны обработаться только корректные транзакции
    result = investment_bank(month, all_transactions, limit)
    expected = 9.11 + 6.00 + 1.00
    assert abs(result - expected) < 0.01


# Тесты на обработку ошибок
@pytest.mark.parametrize("invalid_month", [ "2021", "2021-13", "декабрь 2021",
                                            "2021/12", "", "2021-12-01",
                                            ])
def test_investment_bank_invalid_month(invalid_month, sample_transactions):
    """Тест с некорректным форматом месяца."""
    limit = 10
    result = investment_bank(invalid_month, sample_transactions, limit)
    assert result == 0.00


def test_investment_bank_zero_limit(sample_transactions):
    """Тест с нулевым и отрицательным лимитом."""
    month = "2021-12"
    limit = 0

    result = investment_bank(month, sample_transactions, limit)
    assert result == 0.00

    limit = -10
    result = investment_bank(month, sample_transactions, limit)
    assert result == 0.00

