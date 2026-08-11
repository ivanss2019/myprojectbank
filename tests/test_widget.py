"""Тесты для модуля src.widget."""

import pytest

from src.widget import get_date, mask_account_card


@pytest.mark.parametrize(
    "info, expected",
    [
        ("Visa Platinum 7000792289606361", "Visa Platinum 7000 79** **** 6361"),
        ("Maestro 1596837868705199", "Maestro 1596 83** **** 5199"),
        ("MasterCard 7158300734726758", "MasterCard 7158 30** **** 6758"),
        ("Visa Classic 6831982476737658", "Visa Classic 6831 98** **** 7658"),
        ("Visa Platinum 8990922113665229", "Visa Platinum 8990 92** **** 5229"),
        ("Visa Gold 5999414228426353", "Visa Gold 5999 41** **** 6353"),
        ("Счет 73654108430135874305", "Счет **4305"),
        ("Счет 64686473678894779589", "Счет **9589"),
        ("Счет 35383033474447895560", "Счет **5560"),
    ],
)
def test_mask_account_card(info: str, expected: str) -> None:
    """Проверяет маскировку и карт, и счетов одной функцией."""
    assert mask_account_card(info) == expected


@pytest.mark.parametrize(
    "date_string, expected",
    [
        ("2024-03-11T02:26:18.671407", "11.03.2024"),
        ("2019-07-03T18:35:29.512364", "03.07.2019"),
        ("2000-01-01T00:00:00.000000", "01.01.2000"),
    ],
)
def test_get_date(date_string: str, expected: str) -> None:
    """Проверяет преобразование ISO-даты в формат ДД.ММ.ГГГГ."""
    assert get_date(date_string) == expected
