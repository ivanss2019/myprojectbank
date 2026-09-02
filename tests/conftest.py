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


@pytest.fixture
def transactions() -> List[Dict[str, Any]]:
    """Список транзакций с разными валютами — для тестов generators."""
    return [
        {
            "id": 939719570,
            "state": "EXECUTED",
            "date": "2018-06-30T02:08:58.425572",
            "operationAmount": {
                "amount": "9824.07",
                "currency": {"name": "USD", "code": "USD"},
            },
            "description": "Перевод организации",
            "from": "Счет 75106830613657916952",
            "to": "Счет 11776614605963066702",
        },
        {
            "id": 142264268,
            "state": "EXECUTED",
            "date": "2019-04-04T23:20:05.206878",
            "operationAmount": {
                "amount": "79114.93",
                "currency": {"name": "USD", "code": "USD"},
            },
            "description": "Перевод со счета на счет",
            "from": "Счет 19708645243227258542",
            "to": "Счет 75651667383060284188",
        },
        {
            "id": 873106923,
            "state": "EXECUTED",
            "date": "2019-03-23T01:09:46.296404",
            "operationAmount": {
                "amount": "43318.34",
                "currency": {"name": "руб.", "code": "RUB"},
            },
            "description": "Перевод со счета на счет",
            "from": "Счет 44812258784861134719",
            "to": "Счет 74489636417521191160",
        },
        {
            "id": 594226727,
            "state": "CANCELED",
            "date": "2018-09-12T21:27:25.241689",
            "operationAmount": {
                "amount": "67314.70",
                "currency": {"name": "руб.", "code": "RUB"},
            },
            "description": "Перевод организации",
            "from": "Visa Classic 6831982476737658",
            "to": "Счет 41428829183848836862",
        },
        {
            "id": 615064591,
            "state": "EXECUTED",
            "date": "2018-10-14T08:21:33.419441",
            "operationAmount": {
                "amount": "10000.00",
                "currency": {"name": "EUR", "code": "EUR"},
            },
            "description": "Перевод с карты на карту",
            "from": "Maestro 1596837868705199",
            "to": "Visa Classic 6831982476737658",
        },
    ]


@pytest.fixture
def empty_transactions() -> List[Dict[str, Any]]:
    """Пустой список транзакций."""
    return []
