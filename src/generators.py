"""Генераторы для обработки данных о транзакциях и номеров карт."""

from typing import Any, Dict, Iterator, List


def filter_by_currency(
    transactions: List[Dict[str, Any]], currency: str
) -> Iterator[Dict[str, Any]]:
    """Отбирает транзакции с заданной валютой операции.

    Валюта сравнивается по коду (`operationAmount.currency.code`).

    Пример:
        >>> transactions = [
        ...     {
        ...         "id": 1,
        ...         "operationAmount": {"currency": {"code": "USD"}},
        ...     },
        ...     {
        ...         "id": 2,
        ...         "operationAmount": {"currency": {"code": "RUB"}},
        ...     },
        ... ]
        >>> usd_transactions = filter_by_currency(transactions, "USD")
        >>> next(usd_transactions)["id"]
        1

    Args:
        transactions: список словарей с данными транзакций.
        currency: код валюты, по которому нужно отфильтровать транзакции
            (например, "USD").

    Yields:
        Транзакции, у которых код валюты совпадает с переданным.
    """
    for transaction in transactions:
        if transaction["operationAmount"]["currency"]["code"] == currency:
            yield transaction


def transaction_descriptions(transactions: List[Dict[str, Any]]) -> Iterator[str]:
    """Поочередно выдает описания транзакций.

    Пример:
        >>> transactions = [{"description": "Перевод организации"}]
        >>> descriptions = transaction_descriptions(transactions)
        >>> next(descriptions)
        'Перевод организации'

    Args:
        transactions: список словарей с данными транзакций.

    Yields:
        Значение ключа "description" каждой транзакции по очереди.
    """
    for transaction in transactions:
        yield transaction["description"]


def card_number_generator(start: int, end: int) -> Iterator[str]:
    """Генерирует номера банковских карт в заданном диапазоне.

    Номера выдаются в формате "XXXX XXXX XXXX XXXX" (16 цифр, разбитых
    по 4). Диапазон допустимых значений — от 1 (0000 0000 0000 0001)
    до 9999999999999999 (9999 9999 9999 9999), границы включительно.

    Пример:
        >>> numbers = card_number_generator(1, 2)
        >>> next(numbers)
        '0000 0000 0000 0001'
        >>> next(numbers)
        '0000 0000 0000 0002'

    Args:
        start: начальное значение диапазона (включительно).
        end: конечное значение диапазона (включительно).

    Yields:
        Номер карты в виде строки "XXXX XXXX XXXX XXXX".
    """
    for number in range(start, end + 1):
        digits = f"{number:016d}"
        yield f"{digits[0:4]} {digits[4:8]} {digits[8:12]} {digits[12:16]}"
