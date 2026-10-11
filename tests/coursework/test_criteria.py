"""Проверки по присланным критериям приёмки курсовой работы."""

import json
import re
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd
import pytest

from src.analysis_utils import (
    ROOT,
    dataframe_records,
    load_user_settings,
    read_excel_transactions,
)
from src.main import cli
from src.services import phone_search, profitable_cashback_categories
from src.views import event_period, events_page, get_greeting, home_page


@pytest.mark.parametrize(
    "time, expected",
    [
        ("05:59", "Доброй ночи"),
        ("06:00", "Доброе утро"),
        ("11:59", "Доброе утро"),
        ("12:00", "Добрый день"),
        ("17:59", "Добрый день"),
        ("18:00", "Добрый вечер"),
        ("22:59", "Добрый вечер"),
        ("23:00", "Доброй ночи"),
    ],
)
def test_exact_greeting_boundaries(time, expected):
    assert get_greeting(datetime.fromisoformat("2021-12-31T" + time)) == expected


def test_home_acceptance_all_configured_quotes():
    settings = load_user_settings(ROOT / "user_settings.json")
    frame = read_excel_transactions(ROOT / "data" / "operations.xlsx")
    currency_response = Mock(
        content=b"<ValCurs><Valute><CharCode>USD</CharCode>"
        b"<Nominal>1</Nominal><Value>90,0</Value></Valute>"
        b"<Valute><CharCode>EUR</CharCode><Nominal>1</Nominal>"
        b"<Value>100,0</Value></Valute></ValCurs>"
    )
    stock_response = Mock()
    stock_response.json.return_value = {"Global Quote": {"05. price": "150.12"}}
    with (
        patch.dict("os.environ", {"ALPHA_VANTAGE_API_KEY": "test-key"}),
        patch(
            "src.market_data.requests.get",
            side_effect=[currency_response]
            + [stock_response] * len(settings["user_stocks"]),
        ),
    ):
        result = json.loads(home_page("2021-12-31 23:59:59", frame, settings))
    assert len(result["cards"]) >= 1
    top = result["top_transactions"]
    assert len(top) == 5
    assert [item["amount"] for item in top] == sorted(
        (item["amount"] for item in top), reverse=True
    )
    for item in top:
        assert set(item) == {"date", "amount", "category", "description"}
        assert re.fullmatch(r"\d{2}\.\d{2}\.\d{4}", item["date"])
    assert [item["currency"] for item in result["currency_rates"]] == settings[
        "user_currencies"
    ]
    assert [item["stock"] for item in result["stock_prices"]] == settings["user_stocks"]
    for item in result["currency_rates"]:
        assert isinstance(item["rate"], float) and item["rate"] > 0
    for item in result["stock_prices"]:
        assert isinstance(item["stock"], str)
        assert isinstance(item["price"], float) and item["price"] > 0


@pytest.mark.parametrize(
    "period, start",
    [
        ("W", "2020-05-18"),
        ("M", "2020-05-01"),
        ("Y", "2020-01-01"),
    ],
)
def test_periods(period, start):
    begin, end = event_period("2020-05-20", period)
    assert begin == pd.Timestamp(start)
    assert end == pd.Timestamp("2020-05-21")


def test_invalid_period():
    with pytest.raises(ValueError, match="Диапазон"):
        event_period("2020-05-20", "invalid")


def test_events_totals_top7_and_other():
    rows = [
        {
            "Дата операции": "20.05.2020 23:59:59",
            "Сумма платежа": -value,
            "Категория": f"Категория {index}",
        }
        for index, value in enumerate([100.25, 90, 80, 70, 60, 50, 40, 30, 20])
    ]
    rows += [
        {
            "Дата операции": "20.05.2020",
            "Сумма платежа": -0.25,
            "Категория": "Категория 0",
        },
        {"Дата операции": "20.05.2020", "Сумма платежа": -15, "Категория": "Переводы"},
        {"Дата операции": "20.05.2020", "Сумма платежа": -25, "Категория": "Наличные"},
        {
            "Дата операции": "20.05.2020",
            "Сумма платежа": 1000.4,
            "Категория": "Зарплата",
        },
        {"Дата операции": "20.05.2020", "Сумма платежа": 100, "Категория": None},
        {
            "Дата операции": "21.05.2020",
            "Сумма платежа": -99999,
            "Категория": "Будущее",
        },
    ]
    result = json.loads(
        events_page(
            "2020-05-20", pd.DataFrame(rows), {"user_currencies": [], "user_stocks": []}
        )
    )
    assert set(result) == {"expenses", "income", "currency_rates", "stock_prices"}
    assert result["expenses"]["total_amount"] == 581
    assert len(result["expenses"]["main"]) == 8
    assert result["expenses"]["main"][0] == {"category": "Категория 0", "amount": 101}
    assert result["expenses"]["main"][-1] == {"category": "Остальное", "amount": 50}
    assert result["expenses"]["transfers_and_cash"] == [
        {"category": "Наличные", "amount": 25},
        {"category": "Переводы", "amount": 15},
    ]
    assert result["income"] == {
        "total_amount": 1100,
        "main": [
            {"category": "Зарплата", "amount": 1000},
            {"category": "Без категории", "amount": 100},
        ],
    }
    assert all(isinstance(item["amount"], int) for item in result["expenses"]["main"])


@pytest.mark.parametrize(
    "period, amounts",
    [
        ("W", [-200, -999]),
        ("M", [-100.5, -200, -999, 80, -7.94, -500, 10]),
        ("Y", [-900, -100.5, -200, -999, 80, -7.94, -500, 10]),
        ("ALL", [-900, -100.5, -200, -999, 80, -7.94, -500, 10]),
    ],
)
def test_events_actual_period_filter(frame, period, amounts):
    result = json.loads(
        events_page(
            "2020-05-20", frame, {"user_currencies": [], "user_stocks": []}, period
        )
    )
    assert result["expenses"]["total_amount"] == round(
        -sum(x for x in amounts if x < 0)
    )
    assert result["income"]["total_amount"] == sum(x for x in amounts if x > 0)


def test_empty_events(frame):
    result = json.loads(
        events_page("2000-01-01", frame, {"user_currencies": [], "user_stocks": []})
    )
    assert result["expenses"] == {
        "total_amount": 0,
        "main": [],
        "transfers_and_cash": [],
    }
    assert result["income"] == {"total_amount": 0, "main": []}


@pytest.mark.parametrize(
    "description",
    [
        "+7 (900) 000-00-00",
        "89000000000",
        "+7 995 555-55-55",
        "7-981-333-44-55",
        "МТС: 8 (921) 111 22 33",
        "Два: +79000000000, 89990000000",
    ],
)
def test_mobile_formats(description):
    data = [{"Описание": description}]
    assert json.loads(phone_search(data)) == data


@pytest.mark.parametrize(
    "description",
    [
        None,
        "",
        "12389000000000123",
        "+7 (495) 000-00-00",
        "8900000000",
        "890000000000",
        "abc89000000000",
        "+8 900 000-00-00",
    ],
)
def test_non_mobile_numbers(description):
    assert json.loads(phone_search([{"Описание": description}])) == []


def test_cashback_top_categories():
    data = [
        {"Дата операции": "2021-12-01", "Категория": category, "Сумма платежа": amount}
        for category, amount in [
            ("Еда", -100),
            ("Еда", -100),
            ("Такси", -500),
            ("Одежда", -300),
            ("Переводы", -10000),
            ("Еда", 999),
        ]
    ]
    data.append(
        {"Дата операции": "2021-11-30", "Категория": "Еда", "Сумма платежа": -1000}
    )
    result = json.loads(profitable_cashback_categories(data, 2021, 12))
    assert list(result.items()) == [("Такси", 25.0), ("Одежда", 15.0), ("Еда", 10.0)]
    assert (
        json.loads(profitable_cashback_categories(data, 2021, 12, 10))["Такси"] == 50.0
    )


def test_cashback_real_file_and_filter(frame):
    result = json.loads(
        profitable_cashback_categories(dataframe_records(frame), 2020, 5)
    )
    assert result == {"Еда": 64.98, "Транспорт": 0.4}
    real = dataframe_records(read_excel_transactions(ROOT / "data" / "operations.xlsx"))
    result = json.loads(profitable_cashback_categories(real, 2021, 12))
    assert len(result) >= 3
    assert list(result.values()) == sorted(result.values(), reverse=True)


@pytest.mark.parametrize("rate", [-1, 101, float("nan"), float("inf")])
def test_invalid_cashback_rate(rate):
    with pytest.raises(ValueError):
        profitable_cashback_categories([], 2021, 12, rate)


def test_empty_cashback():
    assert json.loads(profitable_cashback_categories([], 2021, 12)) == {}
    with pytest.raises(ValueError):
        profitable_cashback_categories([], 2021, 13)


@pytest.mark.parametrize(
    "command",
    [
        ["events", "2020-05-20"],
        ["phones"],
        ["cashback", "2020", "5", "--rate", "5"],
    ],
)
def test_new_commands(frame, tmp_path, capsys, command):
    source = tmp_path / "operations.xlsx"
    settings = tmp_path / "settings.json"
    frame.to_excel(source, index=False)
    settings.write_text('{"user_currencies": [], "user_stocks": []}')
    if command[0] == "events":
        command = command + ["--settings", str(settings)]
    cli(["--file", str(source)] + command)
    json.loads(capsys.readouterr().out)
