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
