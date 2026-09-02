"""Тесты для модуля src.processing."""

from typing import Any, Dict, List

import pytest

from src.processing import filter_by_state, sort_by_date


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

    @pytest.mark.parametrize(
        "state, expected_ids",
        [
            ("EXECUTED", [41428829, 939719570]),
            ("CANCELED", [594226727, 615064591]),
            ("PENDING", [142589864]),
            ("DECLINED", []),
        ],
    )
    def test_filters_by_various_states(
        self,
        operations: List[Dict[str, Any]],
        state: str,
        expected_ids: List[int],
    ) -> None:
        """Функция корректно фильтрует по каждому из встречающихся статусов
        и возвращает пустой список, если такого статуса нет ни у одной
        операции."""
        result = filter_by_state(operations, state)
        assert [item["id"] for item in result] == expected_ids

    def test_empty_input_returns_empty_list(
        self, empty_operations: List[Dict[str, Any]]
    ) -> None:
        """На пустом списке функция возвращает пустой список."""
        assert filter_by_state(empty_operations) == []

    def test_does_not_mutate_input(self, operations: List[Dict[str, Any]]) -> None:
        """Исходный список операций не должен изменяться."""
        original_length = len(operations)
        filter_by_state(operations, "CANCELED")
        assert len(operations) == original_length

    def test_returns_new_list_object(self, operations: List[Dict[str, Any]]) -> None:
        """Функция возвращает новый объект списка, а не тот же самый."""
        assert filter_by_state(operations, "EXECUTED") is not operations


class TestSortByDate:
    """Тесты для функции sort_by_date."""

    def test_default_order_is_descending(
        self, operations: List[Dict[str, Any]]
    ) -> None:
        """По умолчанию операции сортируются от новых к старым."""
        result = sort_by_date(operations)
        assert [item["id"] for item in result] == [
            142589864,
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
            142589864,
        ]

    def test_stable_sort_with_duplicate_dates(
        self, operations_with_duplicate_dates: List[Dict[str, Any]]
    ) -> None:
        """При одинаковых датах порядок операций между собой сохраняется
        (сортировка стабильна), как и требуется по контракту sorted()."""
        result = sort_by_date(operations_with_duplicate_dates)
        assert [item["id"] for item in result] == [1, 2, 3]

    def test_empty_input_returns_empty_list(
        self, empty_operations: List[Dict[str, Any]]
    ) -> None:
        """На пустом списке функция возвращает пустой список."""
        assert sort_by_date(empty_operations) == []

    def test_does_not_mutate_input(self, operations: List[Dict[str, Any]]) -> None:
        """Исходный список операций не должен изменяться."""
        original_order = [item["id"] for item in operations]
        sort_by_date(operations)
        assert [item["id"] for item in operations] == original_order

    def test_returns_new_list_object(self, operations: List[Dict[str, Any]]) -> None:
        """Функция возвращает новый объект списка, а не тот же самый."""
        assert sort_by_date(operations) is not operations

    @pytest.mark.parametrize("bad_date", ["", "not-a-date", "2024-13-40"])
    def test_invalid_date_format_raises_value_error(self, bad_date: str) -> None:
        """Некорректный формат даты приводит к ValueError при парсинге."""
        with pytest.raises(ValueError):
            sort_by_date([{"id": 1, "state": "EXECUTED", "date": bad_date}])

    def test_missing_date_key_raises_key_error(self) -> None:
        """Отсутствие ключа date в одном из словарей вызывает KeyError."""
        with pytest.raises(KeyError):
            sort_by_date([{"id": 1, "state": "EXECUTED"}])
