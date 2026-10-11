"""Сервисы анализа транзакций: поиск по всему набору данных."""

import json
import logging
import math
import re
from datetime import datetime
from decimal import Decimal
from functools import reduce
from typing import Any, Dict, List

import pandas as pd

from src.analysis_utils import (
    dataframe_records,
    money,
    prepare_transactions,
    successful_transactions,
)

logger = logging.getLogger(__name__)


def simple_search(query: str, transactions: List[Dict[str, Any]]) -> str:
    """Ищет подстроку без учёта регистра в описании ИЛИ категории.

    Использует filter и lambda. Пустой запрос возвращает все операции;
    отсутствующие поля и null считаются пустыми строками. Запрос буквальный,
    а не регулярное выражение. Список должен содержать JSON-совместимые данные.
    """
    needle = query.casefold()
    matches = list(
        filter(
            lambda item: any(
                needle in str(item.get(field) or "").casefold()
                for field in ("Описание", "Категория")
            ),
            transactions,
        )
    )
    logger.info("Поиск завершён: совпадений %d", len(matches))
    return json.dumps(matches, ensure_ascii=False, allow_nan=False, indent=2)


def phone_search(transactions: List[Dict[str, Any]]) -> str:
    """Ищет российские мобильные номера +7/8/7 с кодом 9xx и 10 цифрами.

    Поддерживаются пробелы, скобки и дефисы; границы исключают совпадения
    внутри длинных числовых идентификаторов. Возвращает запись один раз.
    """
    pattern = re.compile(
        r"(?<![\w+])(?:\+7|8|7)[\s-]*(?:\(9\d{2}\)|9\d{2})"
        r"[\s-]*\d{3}[\s-]*\d{2}[\s-]*\d{2}(?!\w)"
    )
    matches = list(
        filter(
            lambda item: pattern.search(str(item.get("Описание") or "")) is not None,
            transactions,
        )
    )
    logger.info("Найдены операции с телефонами: %d", len(matches))
    return json.dumps(matches, ensure_ascii=False, allow_nan=False, indent=2)


def profitable_cashback_categories(
    data: List[Dict[str, Any]], year: int, month: int, cashback_rate: float = 5.0
) -> str:
    """Ранжирует категории по потенциальному кешбэку за месяц.

    Ставка — процент, по умолчанию 5 (в условии величина не задана).
    Считает успешные рублёвые расходы, исключая переводы и снятие наличных.
    Возвращает все категории по убыванию, без выдуманных категорий при <3.
    """
    start = pd.Timestamp(datetime(year, month, 1))
    if not math.isfinite(cashback_rate) or not 0 <= cashback_rate <= 100:
        raise ValueError("Ставка кешбэка должна быть от 0 до 100 процентов")
    if not data:
        return "{}"
    frame = successful_transactions(
        prepare_transactions(pd.DataFrame(data), ("Категория",))
    )
    frame = frame.loc[
        frame["Дата операции"].ge(start)
        & frame["Дата операции"].lt(start + pd.DateOffset(months=1))
        & frame["Сумма платежа"].lt(0)
        & frame["Категория"].notna()
        & ~frame["Категория"].isin(["Переводы", "Наличные"])
    ]
    if "Валюта платежа" in frame:
        frame = frame.loc[frame["Валюта платежа"].isin(["RUB", "RUR"])]

    def accumulate(
        totals: Dict[str, Decimal], item: Dict[str, Any]
    ) -> Dict[str, Decimal]:
        category = str(item["Категория"])
        amount = abs(Decimal(str(item["Сумма платежа"])))
        return {**totals, category: totals.get(category, Decimal(0)) + amount}

    totals: Dict[str, Decimal] = {}
    totals = reduce(accumulate, dataframe_records(frame), totals)
    ranked = sorted(totals.items(), key=lambda item: (-item[1], item[0]))
    rate = Decimal(str(cashback_rate)) / 100
    result = {category: money(amount * rate) for category, amount in ranked}
    logger.info("Анализ кешбэка завершён: категорий %d", len(result))
    return json.dumps(result, ensure_ascii=False, allow_nan=False, indent=2)
