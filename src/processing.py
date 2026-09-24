"""Функции обработки списка банковских операций."""

import re
from collections import Counter
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
        key=lambda item: datetime.fromisoformat(item["date"].replace("Z", "+00:00")),
        reverse=descending,
    )


def process_bank_search(
    data: List[Dict[str, Any]], search: str
) -> List[Dict[str, Any]]:
    """Ищет буквальную подстроку в description через re без учёта регистра.

    Спецсимволы не интерпретируются как регулярное выражение. Операции
    без строкового описания пропускаются. Пустой запрос выбирает все
    строковые описания. Порядок и исходные словари не изменяются.
    """
    pattern = re.compile(re.escape(search), re.IGNORECASE)
    return [
        operation
        for operation in data
        if isinstance(operation.get("description"), str)
        and pattern.search(operation["description"]) is not None
    ]


def process_bank_operations(
    data: List[Dict[str, Any]], categories: List[str]
) -> Dict[str, int]:
    """Считает операции с точным совпадением description и названия категории.

    Возвращает все запрошенные категории, включая отсутствующие (0).
    Повторяющиеся категории не увеличивают счётчик. Регистр учитывается.
    Операции без строкового описания пропускаются, входные данные не меняются.
    """
    counts = Counter(
        operation["description"]
        for operation in data
        if isinstance(operation.get("description"), str)
    )
    return {category: counts[category] for category in categories}
