"""Тесты для модуля src.processing."""

from typing import Any, Dict, List

import pytest

from src.processing import filter_by_state, sort_by_date


@pytest.fixture
def operations() -> List[Dict[str, Any]]:
    """Набор операций из условия задания для проверки функций."""
    return [
        {"id": 41428829, "state": "EXECUTED", "date": "2019-07-03T18:35:29.512364"},
        {"id": 939719570, "state": "EXECUTED", "date": "2018-06-30T02:08:58.425572"},
        {"id": 594226727, "state": "CANCELED", "date": "2018-09-12T21:27:25.241689"},
        {"id": 615064591, "state": "CANCELED", "date": "2018-10-14T08:21:33.419441"},
    ]


class TestFilterByState:
    """Тесты для функции filter_by_state."""

    def test_default_state_executed(self, operations: List[Dict[str, Any]]) -> None:
        """По умолчанию отбираются операции со статусом EXECUTED."""
        result = filter_by_state(operations)
        assert result == [
            {
                "id": 41428829,
                "state": "EXECUTED",
                "date": "2019-07-03T18:35:29.512364",
            },
            {
                "id": 939719570,
                "state": "EXECUTED",
                "date": "2018-06-30T02:08:58.425572",
            },
        ]

    def test_explicit_state_canceled(self, operations: List[Dict[str, Any]]) -> None:
        """При явном указании статуса отбираются операции с ним."""
        result = filter_by_state(operations, "CANCELED")
        assert result == [
            {
                "id": 594226727,
                "state": "CANCELED",
                "date": "2018-09-12T21:27:25.241689",
            },
            {
                "id": 615064591,
                "state": "CANCELED",
                "date": "2018-10-14T08:21:33.419441",
            },
        ]

    def test_no_matching_state_returns_empty_list(
        self, operations: List[Dict[str, Any]]
    ) -> None:
        """Если подходящих операций нет, возвращается пустой список."""
        assert filter_by_state(operations, "PENDING") == []

    def test_empty_input_returns_empty_list(self) -> None:
        """На пустом списке функция возвращает пустой список."""
        assert filter_by_state([]) == []

    def test_does_not_mutate_input(self, operations: List[Dict[str, Any]]) -> None:
        """Исходный список операций не должен изменяться."""
        original_length = len(operations)
        filter_by_state(operations, "CANCELED")
        assert len(operations) == original_length


class TestSortByDate:
    """Тесты для функции sort_by_date."""

    def test_default_order_is_descending(
        self, operations: List[Dict[str, Any]]
    ) -> None:
        """По умолчанию операции сортируются от новых к старым."""
        result = sort_by_date(operations)
        assert [item["id"] for item in result] == [
            41428829,
            615064591,
            594226727,
            939719570,
        ]

    def test_ascending_order(self, operations: List[Dict[str, Any]]) -> None:
        """При descending=False операции сортируются от старых к новым."""
        result = sort_by_date(operations, descending=False)
        assert [item["id"] for item in result] == [
            939719570,
            594226727,
            615064591,
            41428829,
        ]

    def test_empty_input_returns_empty_list(self) -> None:
        """На пустом списке функция возвращает пустой список."""
        assert sort_by_date([]) == []

    def test_does_not_mutate_input(self, operations: List[Dict[str, Any]]) -> None:
        """Исходный список операций не должен изменяться."""
        original_order = [item["id"] for item in operations]
        sort_by_date(operations)
        assert [item["id"] for item in operations] == original_order
