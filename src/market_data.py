"""Текущие курсы ЦБ и последние доступные котировки Alpha Vantage."""

import logging
import math
import os
from typing import Dict, List, Optional, Union
from xml.etree import ElementTree

import requests

logger = logging.getLogger(__name__)
CBR_URL = "https://www.cbr.ru/scripts/XML_daily.asp"
STOCK_URL = "https://www.alphavantage.co/query"
Quote = Dict[str, Union[str, float, None]]


def get_currency_rates(currencies: List[str]) -> List[Quote]:
    """Возвращает рубли за единицу валюты; при ошибке rate равен null."""
    if not currencies:
        return []
    rates: Dict[str, Optional[float]] = {"RUB": 1.0, "RUR": 1.0}
    if any(currency not in rates for currency in currencies):
        try:
            response = requests.get(CBR_URL, timeout=10)
            response.raise_for_status()
            root = ElementTree.fromstring(response.content)
            for item in root.findall("Valute"):
                code = item.findtext("CharCode")
                value = float((item.findtext("Value") or "").replace(",", "."))
                nominal = float(item.findtext("Nominal") or "")
                rate = value / nominal
                if code and math.isfinite(rate) and rate > 0:
                    rates[code] = round(rate, 4)
        except (
            requests.RequestException,
            ElementTree.ParseError,
            ValueError,
            ZeroDivisionError,
        ):
            logger.warning("Курсы валют недоступны")
    for currency in currencies:
        if currency not in rates:
            logger.warning("Нет курса для валюты %s", currency)
    return [
        {"currency": currency, "rate": rates.get(currency)} for currency in currencies
    ]


def get_stock_prices(stocks: List[str], api_key: Optional[str] = None) -> List[Quote]:
    """Получает GLOBAL_QUOTE в USD; не выдаёт ошибки API за нулевую цену."""
    key = api_key or os.getenv("ALPHA_VANTAGE_API_KEY")
    if stocks and not key:
        logger.warning("Не задан ALPHA_VANTAGE_API_KEY: котировки недоступны")
        return [{"stock": stock, "price": None} for stock in stocks]
    result: List[Quote] = []
    for stock in stocks:
        price: Optional[float] = None
        try:
            response = requests.get(
                STOCK_URL,
                params={"function": "GLOBAL_QUOTE", "symbol": stock, "apikey": key},
                timeout=10,
            )
            response.raise_for_status()
            value = float(response.json()["Global Quote"]["05. price"])
            if not math.isfinite(value) or value <= 0:
                raise ValueError("Некорректная цена")
            price = round(value, 2)
        except (requests.RequestException, KeyError, TypeError, ValueError):
            # Текст исключения может содержать URL с API-ключом: не логируем его.
            logger.warning("Котировка %s недоступна", stock)
        result.append({"stock": stock, "price": price})
    return result
