"""Общие фикстуры для тестов проекта."""

from typing import Any, Dict, List

import pytest


@pytest.fixture
def operations() -> List[Dict[str, Any]]:
    """Список операций с разными статусами и датами."""
    return [
        {"id": 41428829, "state": "EXECUTED", "date": "2019-07-03T18:35:29.512364"},
        {"id": 939719570, "state": "EXECUTED", "date": "2018-06-30T02:08:58.425572"},
        {"id": 594226727, "state": "CANCELED", "date": "2018-09-12T21:27:25.241689"},
        {"id": 615064591, "state": "CANCELED", "date": "2018-10-14T08:21:33.419441"},
        {"id": 142589864, "state": "PENDING", "date": "2020-01-15T10:00:00.000000"},
    ]


@pytest.fixture
def operations_with_duplicate_dates() -> List[Dict[str, Any]]:
    """Операции с одинаковой датой — для проверки стабильности сортировки."""
    return [
        {"id": 1, "state": "EXECUTED", "date": "2020-05-01T12:00:00.000000"},
        {"id": 2, "state": "EXECUTED", "date": "2020-05-01T12:00:00.000000"},
        {"id": 3, "state": "CANCELED", "date": "2020-05-01T12:00:00.000000"},
    ]


@pytest.fixture
def empty_operations() -> List[Dict[str, Any]]:
    """Пустой список операций."""
    return []
