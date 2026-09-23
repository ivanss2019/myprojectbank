"""Конвертация суммы транзакции в рубли через внешний API курсов валют.

Для USD и EUR используется Exchange Rates Data API (apilayer.com):
https://apilayer.com/marketplace/exchangerates_data-api
"""

import os
from typing import Any, Dict, Union

import requests
from dotenv import load_dotenv

load_dotenv()

EXCHANGE_RATES_API_URL = "https://api.apilayer.com/exchangerates_data/convert"


def convert_to_rub(transaction: Dict[str, Any]) -> float:
    """Возвращает сумму транзакции в рублях.

    Если валюта операции — рубли, сумма только приводится к float. Если
    валюта — USD или EUR, для конвертации по текущему курсу выполняется
    запрос к внешнему Exchange Rates Data API.

    Пример:
        >>> transaction = {
        ...     "operationAmount": {
        ...         "amount": "31957.58",
        ...         "currency": {"name": "руб.", "code": "RUB"},
        ...     }
        ... }
        >>> convert_to_rub(transaction)
        31957.58

    Args:
        transaction: словарь с данными транзакции. Должен содержать ключ
            "operationAmount" с суммой ("amount") и кодом валюты
            ("currency" -> "code").

    Returns:
        Сумма транзакции в рублях.

    Raises:
        requests.RequestException: если запрос к внешнему API завершился
            сетевой ошибкой или вернул ошибочный статус.
        ValueError: если ответ внешнего API не содержит результата
            конвертации.
    """
    operation_amount = transaction["operationAmount"]
    amount = float(operation_amount["amount"])
    currency_code = operation_amount["currency"]["code"]

    if currency_code == "RUB":
        return amount

    return _get_rub_amount(currency_code, amount)


def _get_rub_amount(currency_code: str, amount: float) -> float:
    """Запрашивает у внешнего API сумму в рублях по текущему курсу.

    Args:
        currency_code: код валюты, из которой конвертируется сумма
            (например, "USD" или "EUR").
        amount: сумма в исходной валюте.

    Returns:
        Сумма, сконвертированная в рубли.

    Raises:
        requests.RequestException: если запрос к внешнему API завершился
            сетевой ошибкой или вернул ошибочный статус.
        ValueError: если ответ внешнего API не содержит результата
            конвертации.
    """
    api_key = os.getenv("API_KEY")
    params: Dict[str, Union[str, float]] = {
        "to": "RUB",
        "from": currency_code,
        "amount": amount,
    }
    response = requests.get(
        EXCHANGE_RATES_API_URL,
        params=params,
        headers={"apikey": api_key},
    )
    response.raise_for_status()
    response_data = response.json()

    try:
        return float(response_data["result"])
    except (KeyError, TypeError) as error:
        raise ValueError(
            f"Внешний API не вернул результат конвертации {currency_code}"
            f" в RUB: {response_data}"
        ) from error
