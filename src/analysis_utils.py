"""Чтение и подготовка данных курсовой работы по анализу транзакций."""

import json
import logging
import math
from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path
from typing import Any, Dict, Iterable, List, Union

import pandas as pd

logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parents[1]
PathLike = Union[str, Path]


def read_excel_transactions(file_path: PathLike) -> pd.DataFrame:
    """Читает Excel отдельно от бизнес-логики; ошибки не подменяет пустотой."""
    try:
        result = pd.read_excel(file_path)
    except (OSError, ValueError, ImportError):
        logger.error("Не удалось прочитать Excel-файл")
        raise
    logger.info("Прочитано операций: %d", len(result))
    return result


def load_user_settings(file_path: PathLike) -> Dict[str, List[str]]:
    """Читает настройки валют и тикеров, проверяет списки непустых строк."""
    with open(file_path, encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, dict):
        raise ValueError("Настройки должны быть JSON-объектом")
    result = {}
    for key in ("user_currencies", "user_stocks"):
        values = data.get(key)
        if not isinstance(values, list) or not all(
            isinstance(value, str) and value.strip() for value in values
        ):
            raise ValueError(f"{key} должен содержать список непустых строк")
        result[key] = list(dict.fromkeys(value.strip().upper() for value in values))
    return result


def parse_datetime(value: str) -> datetime:
    """Разбирает строго YYYY-MM-DD HH:MM:SS, без неоднозначных форматов."""
    result = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    if result.strftime("%Y-%m-%d %H:%M:%S") != value:
        raise ValueError("Ожидается дата в формате YYYY-MM-DD HH:MM:SS")
    return result


def prepare_transactions(
    transactions: pd.DataFrame, extra_columns: Iterable[str] = ()
) -> pd.DataFrame:
    """Возвращает копию с датами и числами, не изменяя исходный датафрейм.

    Поддерживает даты Excel, DD.MM.YYYY и ISO. Некорректные обязательные
    значения приводят к ValueError, чтобы не занижать итоги незаметно.
    """
    required = {"Дата операции", "Сумма платежа", *extra_columns}
    missing = required.difference(transactions.columns)
    if missing:
        raise ValueError("Отсутствуют столбцы: " + ", ".join(sorted(missing)))
    result = transactions.copy(deep=True)
    dates = pd.to_datetime(
        result["Дата операции"], format="mixed", dayfirst=True, errors="coerce"
    )
    amounts = pd.to_numeric(result["Сумма платежа"], errors="coerce")
    if dates.isna().any() or not amounts.map(math.isfinite).all():
        raise ValueError("Некорректная дата операции или сумма платежа")
    result["Дата операции"] = dates
    result["Сумма платежа"] = amounts
    return result


def successful_transactions(transactions: pd.DataFrame) -> pd.DataFrame:
    """Исключает FAILED; без столбца статуса данные считаются успешными."""
    if "Статус" not in transactions:
        return transactions.copy()
    return transactions.loc[transactions["Статус"].eq("OK")].copy()


def money(value: Decimal) -> float:
    """Округляет рубли до копеек по правилу ROUND_HALF_UP."""
    return float(value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def dataframe_records(transactions: pd.DataFrame) -> List[Dict[str, Any]]:
    """Преобразует NaN/NaT в null, даты в ISO, числа numpy в JSON-числа."""
    result: List[Dict[str, Any]] = json.loads(
        transactions.to_json(orient="records", force_ascii=False, date_format="iso")
    )
    return result
