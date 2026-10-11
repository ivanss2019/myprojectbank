"""Границы месяца, траты, кешбэк, сортировка и JSON страницы."""

import json
from datetime import datetime
from unittest.mock import patch

import pytest
from pandas.testing import assert_frame_equal

from src.views import get_greeting, home_page


@pytest.mark.parametrize(
    "hour, expected",
    [
        (0, "Доброй ночи"),
        (5, "Доброй ночи"),
        (6, "Доброе утро"),
        (11, "Доброе утро"),
        (12, "Добрый день"),
        (17, "Добрый день"),
        (18, "Добрый вечер"),
        (22, "Добрый вечер"),
        (23, "Доброй ночи"),
    ],
)
def test_greeting(hour, expected):
    assert get_greeting(datetime(2020, 1, 1, hour)) == expected


def test_greeting_uses_current_time():
    with patch("src.views.datetime") as clock:
        clock.now.return_value = datetime(2026, 10, 11, 19)
        assert get_greeting() == "Добрый вечер"


def test_home_page(frame):
    original = frame.copy(deep=True)
    currencies = [{"currency": "USD", "rate": 90.0}]
    stocks = [{"stock": "AAPL", "price": 150.0}]
    with (
        patch("src.views.get_currency_rates", return_value=currencies) as rates,
        patch("src.views.get_stock_prices", return_value=stocks) as prices,
    ):
        result = json.loads(
            home_page(
                "2020-05-20 12:00:00",
                frame,
                {"user_currencies": ["USD"], "user_stocks": ["AAPL"]},
                now=datetime(2026, 10, 11, 7),
            )
        )
    assert result["greeting"] == "Доброе утро"
    assert result["cards"] == [
        {"last_digits": "0001", "total_spent": 0.0, "cashback": 0.0},
        {"last_digits": "1234", "total_spent": 300.5, "cashback": 3.01},
        {"last_digits": "5678", "total_spent": 7.94, "cashback": 0.08},
    ]
    top = result["top_transactions"]
    assert [item["amount"] for item in top] == [80, 10, -7.94, -100.5, -200]
    assert top[0] == {
        "date": "15.05.2020",
        "amount": 80,
        "category": "Возврат",
        "description": "Возврат",
    }
    assert result["currency_rates"] == currencies
    assert result["stock_prices"] == stocks
    rates.assert_called_once_with(["USD"])
    prices.assert_called_once_with(["AAPL"])
    assert_frame_equal(frame, original)


def test_empty_period(frame):
    result = json.loads(
        home_page(
            "2010-01-01 00:00:00", frame, {"user_currencies": [], "user_stocks": []}
        )
    )
    assert result["cards"] == result["top_transactions"] == []


def test_empty_table(frame):
    result = json.loads(
        home_page(
            "2020-05-01 00:00:00",
            frame.iloc[:0],
            {"user_currencies": [], "user_stocks": []},
        )
    )
    assert result["cards"] == result["top_transactions"] == []


def test_optional_currency_and_status(frame):
    data = frame.iloc[[1]].drop(columns=["Валюта платежа", "Статус"])
    data.loc[:, "Описание"] = None
    result = json.loads(
        home_page(
            "2020-05-01 00:00:00", data, {"user_currencies": [], "user_stocks": []}
        )
    )
    assert result["cards"][0]["total_spent"] == 100.5
    assert result["top_transactions"][0]["description"] == ""


def test_invalid_date_does_not_call_api(frame):
    with patch("src.views.get_currency_rates") as api, pytest.raises(ValueError):
        home_page("20.05.2020", frame, {"user_currencies": [], "user_stocks": []})
    api.assert_not_called()
