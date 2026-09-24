"""Поиск подстроки и подсчёт категорий банковских операций."""

from copy import deepcopy
from typing import Any, Dict, List

import pytest

from src.processing import process_bank_operations, process_bank_search


@pytest.fixture
def operations() -> List[Dict[str, Any]]:
    """Описания, включая некорректные и отсутствующие значения."""
    return [
        {"id": 1, "description": "Перевод организации"},
        {"id": 2, "description": "Открытие вклада"},
        {"id": 3, "description": "Перевод организации"},
        {"id": 4, "description": "Оплата (магазин) + бонус [1]."},
        {"id": 5},
        {"id": 6, "description": None},
        {"id": 7, "description": 123},
        {"id": 8, "description": ""},
    ]


@pytest.mark.parametrize(
    "query,ids",
    [
        ("ПЕРЕВОД", [1, 3]),
        ("вКлАд", [2]),
        ("организации", [1, 3]),
        ("(магазин)", [4]),
        ("[1].", [4]),
        ("+", [4]),
        (".*", []),
        ("[", [4]),
        ("несуществующее", []),
        ("", [1, 2, 3, 4, 8]),
    ],
)
def test_search(operations: List[Dict[str, Any]], query: str, ids: List[int]) -> None:
    """Поиск буквальный, регистронезависимый, сохраняет порядок операций."""
    before = deepcopy(operations)
    result = process_bank_search(operations, query)
    assert [row["id"] for row in result] == ids
    assert operations == before
    assert all(any(row is original for original in operations) for row in result)


def test_search_empty_data() -> None:
    """Пустой список не содержит совпадений."""
    assert process_bank_search([], "перевод") == []


def test_categories(operations: List[Dict[str, Any]]) -> None:
    """Учитываются точные названия, повторы и отсутствующие категории."""
    before = deepcopy(operations)
    categories = [
        "Перевод организации",
        "Открытие вклада",
        "Перевод",
        "Нет",
        "Перевод организации",
        "перевод организации",
        "",
    ]
    assert process_bank_operations(operations, categories) == {
        "Перевод организации": 2,
        "Открытие вклада": 1,
        "Перевод": 0,
        "Нет": 0,
        "перевод организации": 0,
        "": 1,
    }
    assert operations == before
    assert len(categories) == 7


def test_empty_categories_and_data(operations: List[Dict[str, Any]]) -> None:
    """Пустые входы дают пустой словарь либо нулевые счётчики."""
    assert process_bank_operations(operations, []) == {}
    assert process_bank_operations([], ["Перевод"]) == {"Перевод": 0}
