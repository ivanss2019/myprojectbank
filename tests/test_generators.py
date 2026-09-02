"""Тесты для модуля src.generators."""

import inspect
from typing import Any, Dict, Iterator, List

import pytest

from src.generators import (
    card_number_generator,
    filter_by_currency,
    transaction_descriptions,
)


class TestFilterByCurrency:
    """Тесты для генератора filter_by_currency."""

    def test_returns_generator(self, transactions: List[Dict[str, Any]]) -> None:
        """Функция возвращает именно генератор, а не список."""
        result = filter_by_currency(transactions, "USD")
        assert inspect.isgenerator(result)

    @pytest.mark.parametrize(
        "currency, expected_ids",
        [
            ("USD", [939719570, 142264268]),
            ("RUB", [873106923, 594226727]),
            ("EUR", [615064591]),
            ("GBP", []),
        ],
    )
    def test_filters_by_various_currencies(
        self,
        transactions: List[Dict[str, Any]],
        currency: str,
        expected_ids: List[int],
    ) -> None:
        """Генератор поочередно выдает только транзакции с нужной валютой,
        а для валюты, которой нет среди транзакций, не выдает ничего."""
        result = list(filter_by_currency(transactions, currency))
        assert [item["id"] for item in result] == expected_ids

    def test_next_yields_items_one_by_one(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        """next() последовательно возвращает подходящие транзакции."""
        usd_transactions = filter_by_currency(transactions, "USD")
        assert next(usd_transactions)["id"] == 939719570
        assert next(usd_transactions)["id"] == 142264268

    def test_empty_transaction_list_does_not_raise(
        self, empty_transactions: List[Dict[str, Any]]
    ) -> None:
        """На пустом списке транзакций генератор не падает и не выдает
        ничего — сразу завершается."""
        result = filter_by_currency(empty_transactions, "USD")
        with pytest.raises(StopIteration):
            next(result)

    def test_no_matching_currency_raises_stop_iteration(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        """Если подходящих транзакций нет, генератор не падает с ошибкой,
        а корректно завершается через StopIteration."""
        result = filter_by_currency(transactions, "GBP")
        with pytest.raises(StopIteration):
            next(result)


class TestTransactionDescriptions:
    """Тесты для генератора transaction_descriptions."""

    def test_returns_generator(self, transactions: List[Dict[str, Any]]) -> None:
        """Функция возвращает именно генератор, а не список."""
        result = transaction_descriptions(transactions)
        assert inspect.isgenerator(result)

    def test_yields_descriptions_in_order(
        self, transactions: List[Dict[str, Any]]
    ) -> None:
        """Генератор выдает описания в том же порядке, что и транзакции."""
        result = list(transaction_descriptions(transactions))
        assert result == [
            "Перевод организации",
            "Перевод со счета на счет",
            "Перевод со счета на счет",
            "Перевод организации",
            "Перевод с карты на карту",
        ]

    @pytest.mark.parametrize("count", [1, 3, 5])
    def test_works_with_different_input_sizes(
        self, transactions: List[Dict[str, Any]], count: int
    ) -> None:
        """Генератор корректно работает при разном количестве транзакций
        на входе."""
        result = list(transaction_descriptions(transactions[:count]))
        assert len(result) == count

    def test_empty_transaction_list_yields_nothing(
        self, empty_transactions: List[Dict[str, Any]]
    ) -> None:
        """На пустом списке транзакций генератор не выдает ничего."""
        assert list(transaction_descriptions(empty_transactions)) == []


class TestCardNumberGenerator:
    """Тесты для генератора card_number_generator."""

    def test_returns_generator(self) -> None:
        """Функция возвращает именно генератор, а не список."""
        result = card_number_generator(1, 2)
        assert inspect.isgenerator(result)

    @pytest.mark.parametrize(
        "start, end, expected",
        [
            (1, 1, ["0000 0000 0000 0001"]),
            (
                1,
                3,
                ["0000 0000 0000 0001", "0000 0000 0000 0002", "0000 0000 0000 0003"],
            ),
            (
                9999,
                10001,
                ["0000 0000 0000 9999", "0000 0000 0001 0000", "0000 0000 0001 0001"],
            ),
        ],
    )
    def test_generates_correct_numbers_in_range(
        self, start: int, end: int, expected: List[str]
    ) -> None:
        """Генератор выдает правильные номера карт в заданном диапазоне."""
        assert list(card_number_generator(start, end)) == expected

    @pytest.mark.parametrize(
        "start, end",
        [(1, 1), (12345, 12345), (9999999999999999, 9999999999999999)],
    )
    def test_card_number_format(self, start: int, end: int) -> None:
        """Каждый номер карты имеет формат "XXXX XXXX XXXX XXXX"
        (4 блока по 4 цифры, разделенные пробелами)."""
        (number,) = list(card_number_generator(start, end))
        blocks = number.split(" ")
        assert len(blocks) == 4
        assert all(len(block) == 4 and block.isdigit() for block in blocks)

    def test_lower_boundary(self) -> None:
        """Нижняя граница диапазона (1) форматируется корректно."""
        assert next(card_number_generator(1, 1)) == "0000 0000 0000 0001"

    def test_upper_boundary(self) -> None:
        """Верхняя граница диапазона (9999999999999999) форматируется
        корректно."""
        assert next(card_number_generator(9999999999999999, 9999999999999999)) == (
            "9999 9999 9999 9999"
        )

    def test_generation_terminates_correctly(self) -> None:
        """После выдачи всех номеров в диапазоне генератор корректно
        завершается через StopIteration, не зацикливаясь."""
        generator: Iterator[str] = card_number_generator(1, 2)
        next(generator)
        next(generator)
        with pytest.raises(StopIteration):
            next(generator)

    def test_start_greater_than_end_yields_nothing(self) -> None:
        """Если начало диапазона больше конца, генератор не выдает
        ничего и не падает с ошибкой."""
        assert list(card_number_generator(5, 1)) == []
