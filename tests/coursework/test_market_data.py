"""Внешние API проверяются с mock: таймауты, HTTP, лимиты и ответы."""

from unittest.mock import Mock, patch

import pytest
import requests

from src.market_data import CBR_URL, STOCK_URL, get_currency_rates, get_stock_prices


def test_cbr_nominal_and_requested_order():
    response = Mock(
        content=b"<ValCurs><Valute><CharCode>JPY</CharCode>"
        b"<Nominal>100</Nominal><Value>61,2345</Value></Valute>"
        b"<Valute><CharCode>USD</CharCode><Nominal>1</Nominal>"
        b"<Value>90,5000</Value></Valute></ValCurs>"
    )
    with patch("src.market_data.requests.get", return_value=response) as request:
        result = get_currency_rates(["USD", "JPY", "RUB", "ZZZ"])
    assert result == [
        {"currency": "USD", "rate": 90.5},
        {"currency": "JPY", "rate": 0.6123},
        {"currency": "RUB", "rate": 1.0},
        {"currency": "ZZZ", "rate": None},
    ]
    request.assert_called_once_with(CBR_URL, timeout=10)
    response.raise_for_status.assert_called_once()


@pytest.mark.parametrize("error", [requests.Timeout(), requests.HTTPError()])
def test_currency_network_error(error):
    with patch("src.market_data.requests.get", side_effect=error):
        assert get_currency_rates(["EUR"]) == [{"currency": "EUR", "rate": None}]


@pytest.mark.parametrize(
    "body",
    [
        b"bad xml",
        b"<ValCurs><Valute/></ValCurs>",
        b"<ValCurs><Valute><Value>10</Value><Nominal>0</Nominal></Valute></ValCurs>",
    ],
)
def test_currency_bad_response(body):
    with patch("src.market_data.requests.get", return_value=Mock(content=body)):
        assert get_currency_rates(["USD"])[0]["rate"] is None


def test_currency_no_request_for_empty_or_rubles():
    with patch("src.market_data.requests.get") as request:
        assert get_currency_rates([]) == []
        assert get_currency_rates(["RUB"])[0]["rate"] == 1.0
    request.assert_not_called()


def test_stock_price():
    response = Mock()
    response.json.return_value = {"Global Quote": {"05. price": "150.126"}}
    with patch("src.market_data.requests.get", return_value=response) as request:
        assert get_stock_prices(["AAPL"], "test-key") == [
            {"stock": "AAPL", "price": 150.13}
        ]
    request.assert_called_once_with(
        STOCK_URL,
        params={"function": "GLOBAL_QUOTE", "symbol": "AAPL", "apikey": "test-key"},
        timeout=10,
    )
    response.raise_for_status.assert_called_once()


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"Note": "limit"},
        {"Information": "limit"},
        {"Global Quote": {}},
        {"Global Quote": {"05. price": "bad"}},
        {"Global Quote": {"05. price": "nan"}},
        {"Global Quote": {"05. price": -1}},
        None,
    ],
)
def test_stock_bad_response(payload):
    response = Mock()
    response.json.return_value = payload
    with patch("src.market_data.requests.get", return_value=response):
        assert get_stock_prices(["AAPL"], "key")[0]["price"] is None


def test_stock_partial_failure_and_no_secret_log(caplog):
    response = Mock()
    response.json.return_value = {"Global Quote": {"05. price": "15"}}
    with patch(
        "src.market_data.requests.get",
        side_effect=[requests.Timeout("url?apikey=secret"), response],
    ):
        assert get_stock_prices(["AAPL", "MSFT"], "secret") == [
            {"stock": "AAPL", "price": None},
            {"stock": "MSFT", "price": 15.0},
        ]
    assert "secret" not in caplog.text


def test_no_stock_key(monkeypatch):
    monkeypatch.delenv("ALPHA_VANTAGE_API_KEY", raising=False)
    with patch("src.market_data.requests.get") as request:
        assert get_stock_prices(["AAPL"])[0]["price"] is None
        assert get_stock_prices([]) == []
    request.assert_not_called()
