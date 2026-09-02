"""Тесты для модуля src.masks."""

import pytest

from src.masks import get_mask_account, get_mask_card_number


@pytest.mark.parametrize(
    "card_number, expected",
    [
        ("7000792289606361", "7000 79** **** 6361"),
        ("1234567812345678", "1234 56** **** 5678"),
        ("4444555566667777", "4444 55** **** 7777"),
    ],
)
def test_get_mask_card_number(card_number: str, expected: str) -> None:
    """Проверяет корректность маскировки номера карты."""
    assert get_mask_card_number(card_number) == expected


@pytest.mark.parametrize(
    "card_number, expected",
    [
        # Ровно 4 цифры — первый и последний блок пересекаются
        ("1234", "1234 ** **** 1234"),
        # Меньше 4 цифр — короткий номер карты, нестандартная длина
        ("12", "12 ** **** 12"),
        # Длиннее стандартных 16 цифр
        ("12345678901234567890", "1234 56** **** 7890"),
    ],
)
def test_get_mask_card_number_boundary_lengths(card_number: str, expected: str) -> None:
    """Проверяет поведение на нестандартных длинах номера карты."""
    assert get_mask_card_number(card_number) == expected


def test_get_mask_card_number_empty_string() -> None:
    """Если номер карты отсутствует (пустая строка), функция не падает
    и возвращает шаблон с пустыми блоками вместо цифр."""
    assert get_mask_card_number("") == " ** **** "


@pytest.mark.parametrize(
    "account_number, expected",
    [
        ("73654108430135874305", "**4305"),
        ("12345678901234567890", "**7890"),
        ("00000000000000000001", "**0001"),
    ],
)
def test_get_mask_account(account_number: str, expected: str) -> None:
    """Проверяет корректность маскировки номера счета."""
    assert get_mask_account(account_number) == expected


@pytest.mark.parametrize(
    "account_number, expected",
    [
        # Номер короче ожидаемых 4 цифр в хвосте
        ("123", "**123"),
        ("1", "**1"),
    ],
)
def test_get_mask_account_shorter_than_expected(
    account_number: str, expected: str
) -> None:
    """Проверяет поведение, когда номер счета короче 4 цифр."""
    assert get_mask_account(account_number) == expected


def test_get_mask_account_empty_string() -> None:
    """Если номер счета отсутствует (пустая строка), функция не падает
    и возвращает только маску без цифр."""
    assert get_mask_account("") == "**"
