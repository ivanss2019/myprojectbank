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
    ],
)
def test_mask_account_card_recognizes_card(info: str, expected: str) -> None:
    """Строки с типом карты маскируются как карты (get_mask_card_number),
    независимо от того, из скольких слов состоит название типа."""
    assert mask_account_card(info) == expected


@pytest.mark.parametrize(
    "info, expected",
    [
        ("Счет 73654108430135874305", "Счет **4305"),
        ("Счет 64686473678894779589", "Счет **9589"),
        ("Счет 35383033474447895560", "Счет **5560"),
        ("СЧЕТ 35383033474447895560", "СЧЕТ **5560"),
    ],
)
def test_mask_account_card_recognizes_account(info: str, expected: str) -> None:
    """Строки со словом "счет" (в любом регистре) маскируются как счета
    (get_mask_account)."""
    assert mask_account_card(info) == expected


@pytest.mark.parametrize(
    "invalid_info",
    [
        "",
        "   ",
        "OnlyTypeNoNumber",
    ],
)
def test_mask_account_card_invalid_input_raises(invalid_info: str) -> None:
    """Строка без номера (нет пробела, разделяющего тип и номер) не
    может быть разобрана и приводит к ValueError."""
    with pytest.raises(ValueError):
        mask_account_card(invalid_info)


@pytest.mark.parametrize(
    "date_string, expected",
    [
        ("2024-03-11T02:26:18.671407", "11.03.2024"),
        ("2019-07-03T18:35:29.512364", "03.07.2019"),
        ("2000-01-01T00:00:00.000000", "01.01.2000"),
        # Граничные даты
        ("2020-02-29T00:00:00.000000", "29.02.2020"),  # високосный год
        ("2019-12-31T23:59:59.999999", "31.12.2019"),
    ],
)
def test_get_date(date_string: str, expected: str) -> None:
    """Проверяет преобразование ISO-даты в формат ДД.ММ.ГГГГ, включая
    граничные даты (конец года, 29 февраля високосного года)."""
    assert get_date(date_string) == expected


@pytest.mark.parametrize(
    "invalid_date",
    ["", "not-a-date", "2024-13-40", "11.03.2024"],
)
def test_get_date_invalid_format_raises_value_error(invalid_date: str) -> None:
    """Строка, не являющаяся датой в формате ISO 8601, приводит
    к ValueError."""
    with pytest.raises(ValueError):
        get_date(invalid_date)


def test_get_date_missing_date_raises_type_error() -> None:
    """Отсутствующая дата (None вместо строки) приводит к TypeError."""
    with pytest.raises(TypeError):
        get_date(None)  # type: ignore[arg-type]
