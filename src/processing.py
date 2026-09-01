"""Функции обработки списка банковских операций."""

from datetime import datetime
from typing import Any, Dict, List


def filter_by_state(
    data: List[Dict[str, Any]], state: str = "EXECUTED"
) -> List[Dict[str, Any]]:
    """Отбирает операции с заданным статусом.

    Порядок элементов, соответствующих условию, сохраняется таким же,
    как в исходном списке.

    Пример:
        >>> operations = [
        ...     {"id": 1, "state": "EXECUTED", "date": "2019-07-03T18:35:29"},
        ...     {"id": 2, "state": "CANCELED", "date": "2018-09-12T21:27:25"},
        ... ]
        >>> filter_by_state(operations, "CANCELED")
        [{'id': 2, 'state': 'CANCELED', 'date': '2018-09-12T21:27:25'}]

    Args:
        data: список словарей с данными операций.
        state: значение ключа "state", по которому фильтруются операции.
            По умолчанию "EXECUTED".

    Returns:
        Новый список словарей, содержащий только операции с указанным
        статусом.
    """
    return [item for item in data if item.get("state") == state]


def sort_by_date(
    data: List[Dict[str, Any]], descending: bool = True
) -> List[Dict[str, Any]]:
    """Сортирует операции по дате.

    Пример:
        >>> operations = [
        ...     {"id": 1, "date": "2018-06-30T02:08:58"},
        ...     {"id": 2, "date": "2019-07-03T18:35:29"},
        ... ]
        >>> sort_by_date(operations)
        [{'id': 2, 'date': '2019-07-03T18:35:29'},
         {'id': 1, 'date': '2018-06-30T02:08:58'}]

    Args:
        data: список словарей с данными операций, каждый из которых
            содержит ключ "date" с датой в формате ISO 8601.
        descending: порядок сортировки. True (по умолчанию) — от самой
            новой операции к самой старой, False — наоборот.

    Returns:
        Новый список словарей, отсортированный по дате.
    """
    return sorted(
        data,
        key=lambda item: datetime.fromisoformat(item["date"]),
        reverse=descending,
    )
