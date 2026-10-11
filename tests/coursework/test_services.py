"""Поиск без привязки к месяцу и корректность возвращаемого JSON."""

import json
from copy import deepcopy
from typing import Any, Dict, List

import pytest

from src.services import simple_search


@pytest.mark.parametrize(
    "query, expected",
    [
        ("МАГ", [1]),
        ("еда", [1, 2]),
        ("+7 (", [3]),
        (".", [3]),
        ("не найдено", []),
        ("", [1, 2, 3, 4]),
    ],
)
def test_search(query, expected):
    transactions: List[Dict[str, Any]] = [
        {"id": 1, "Описание": "Магнит", "Категория": "Еда"},
        {"id": 2, "Описание": "Обедать", "Категория": None},
        {"id": 3, "Описание": "Иван А. +7 (999)", "Категория": "Переводы"},
        {"id": 4},
    ]
    original = deepcopy(transactions)
    result = json.loads(simple_search(query, transactions))
    assert [item["id"] for item in result] == expected
    assert transactions == original


def test_empty_search_data():
    assert json.loads(simple_search("Магнит", [])) == []
