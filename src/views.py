"""JSON-ответ страницы «Главная»; ввод файлов отделён от расчётов."""

import json
import logging
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Dict, List, Optional

import pandas as pd

from src.analysis_utils import (
    money,
    parse_datetime,
    prepare_transactions,
    successful_transactions,
)
from src.market_data import get_currency_rates, get_stock_prices

logger = logging.getLogger(__name__)


def get_greeting(now: Optional[datetime] = None) -> str:
    """Утро 06–11, день 12–17, вечер 18–22, ночь 23–05."""
    hour = (now or datetime.now()).hour
    if hour < 6 or hour >= 23:
        return "Доброй ночи"
    return ("Доброе утро", "Добрый день", "Добрый вечер")[(hour - 6) // 6]


def get_cards(transactions: pd.DataFrame) -> List[Dict[str, Any]]:
    """Считает расходы и 1% кешбэка по картам из подготовленных операций.

    Суммы платежей должны быть в рублях. Поступления не уменьшают расходы.
    Карта с одними поступлениями тоже показывается с нулевыми расходами.
    """
    cards = transactions["Номер карты"].astype("string").str.extract(r"(\d{4})$")[0]
    result = []
    for last_digits in sorted(cards.dropna().unique()):
        amounts = transactions["Сумма платежа"].loc[cards.eq(last_digits)]
        total = sum(
            (Decimal(str(-value)) for value in amounts.tolist() if value < 0),
            Decimal(0),
        )
        result.append(
            {
                "last_digits": str(last_digits),
                "total_spent": money(total),
                "cashback": money(total / 100),
            }
        )
    return result


def get_top_transactions(transactions: pd.DataFrame) -> List[Dict[str, Any]]:
    """До пяти транзакций по убыванию суммы платежа, с исходным знаком."""
    ranked = transactions.sort_values(
        "Сумма платежа", ascending=False, kind="stable"
    ).head(5)
    return [
        {
            "date": row["Дата операции"].strftime("%d.%m.%Y"),
            "amount": money(Decimal(str(row["Сумма платежа"]))),
            "category": "" if pd.isna(row["Категория"]) else row["Категория"],
            "description": "" if pd.isna(row["Описание"]) else row["Описание"],
        }
        for _, row in ranked.iterrows()
    ]


def home_page(
    date_time: str,
    transactions: pd.DataFrame,
    settings: Dict[str, List[str]],
    now: Optional[datetime] = None,
) -> str:
    """Генерирует JSON с начала месяца по заданную дату и время включительно.

    Расчёты выполняются по успешным рублёвым платежам. Если столбца валюты
    нет, суммы считаются рублёвыми. Котировки — текущие, приветствие — по now.
    """
    end = parse_datetime(date_time)
    start = end.replace(day=1, hour=0, minute=0, second=0)
    data = prepare_transactions(transactions, ("Номер карты", "Категория", "Описание"))
    data = successful_transactions(data)
    data = data.loc[data["Дата операции"].between(start, end)].copy()
    if "Валюта платежа" in data:
        rubles = data["Валюта платежа"].isin(["RUB", "RUR"])
        logger.info("Исключено нерублёвых платежей: %d", int((~rubles).sum()))
        data = data.loc[rubles]
    response = {
        "greeting": get_greeting(now),
        "cards": get_cards(data),
        "top_transactions": get_top_transactions(data),
        "currency_rates": get_currency_rates(settings["user_currencies"]),
        "stock_prices": get_stock_prices(settings["user_stocks"]),
    }
    logger.info("Сформирована главная страница: операций %d", len(data))
    return json.dumps(response, ensure_ascii=False, allow_nan=False, indent=2)


def event_period(date: str, date_range: str = "M") -> tuple[pd.Timestamp, pd.Timestamp]:
    """Начало W/M/Y/ALL и конец указанного дня; будущие даты исключаются."""
    end = pd.Timestamp(datetime.strptime(date, "%Y-%m-%d"))
    if date_range == "W":
        start = end - pd.Timedelta(days=end.weekday())
    elif date_range == "M":
        start = end.replace(day=1)
    elif date_range == "Y":
        start = end.replace(month=1, day=1)
    elif date_range == "ALL":
        start = pd.Timestamp.min
    else:
        raise ValueError("Диапазон должен быть W, M, Y или ALL")
    return start, end + pd.Timedelta(days=1)


def category_totals(transactions: pd.DataFrame) -> List[tuple[str, Decimal]]:
    """Агрегирует модули сумм по категориям, сохраняя копейки до округления."""
    totals: Dict[str, Decimal] = {}
    for _, row in transactions.iterrows():
        category = (
            "Без категории" if pd.isna(row["Категория"]) else str(row["Категория"])
        )
        totals[category] = totals.get(category, Decimal(0)) + abs(
            Decimal(str(row["Сумма платежа"]))
        )
    return sorted(totals.items(), key=lambda item: (-item[1], item[0]))


def rounded_categories(totals: List[tuple[str, Decimal]]) -> List[Dict[str, Any]]:
    """Округляет агрегированные суммы до целых рублей."""
    return [
        {
            "category": name,
            "amount": int(amount.quantize(Decimal(1), rounding=ROUND_HALF_UP)),
        }
        for name, amount in totals
    ]


def event_summary(transactions: pd.DataFrame) -> Dict[str, Any]:
    """Расходы и поступления: топ-7, остаток, переводы и наличные отдельно."""
    expenses = category_totals(transactions.loc[transactions["Сумма платежа"].lt(0)])
    incomes = category_totals(transactions.loc[transactions["Сумма платежа"].gt(0)])
    transfers = [item for item in expenses if item[0] in {"Переводы", "Наличные"}]
    main = [item for item in expenses if item[0] not in {"Переводы", "Наличные"}]
    top = main[:7]
    if len(main) > 7:
        top.append(("Остальное", sum((amount for _, amount in main[7:]), Decimal(0))))

    def total(items: List[tuple[str, Decimal]]) -> int:
        amount = sum((value for _, value in items), Decimal(0))
        return int(amount.quantize(Decimal(1), rounding=ROUND_HALF_UP))

    return {
        "expenses": {
            "total_amount": total(expenses),
            "main": rounded_categories(top),
            "transfers_and_cash": rounded_categories(transfers),
        },
        "income": {"total_amount": total(incomes), "main": rounded_categories(incomes)},
    }


def events_page(
    date: str,
    transactions: pd.DataFrame,
    settings: Dict[str, List[str]],
    date_range: str = "M",
) -> str:
    """JSON страницы «События»: успешные рублёвые платежи до конца даты."""
    start, end = event_period(date, date_range)
    data = successful_transactions(prepare_transactions(transactions, ("Категория",)))
    data = data.loc[data["Дата операции"].ge(start) & data["Дата операции"].lt(end)]
    if "Валюта платежа" in data:
        data = data.loc[data["Валюта платежа"].isin(["RUB", "RUR"])]
    response = event_summary(data)
    response["currency_rates"] = get_currency_rates(settings["user_currencies"])
    response["stock_prices"] = get_stock_prices(settings["user_stocks"])
    logger.info("Сформирована страница событий: операций %d", len(data))
    return json.dumps(response, ensure_ascii=False, allow_nan=False, indent=2)
