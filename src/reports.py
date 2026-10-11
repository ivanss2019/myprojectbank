"""Траты по категории за три календарных месяца и сохранение в Excel."""

import logging
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable, Optional, Union, overload

import pandas as pd

from src.analysis_utils import (
    ROOT,
    PathLike,
    prepare_transactions,
    successful_transactions,
)

logger = logging.getLogger(__name__)
ReportFunction = Callable[..., pd.DataFrame]


def write_report(report: pd.DataFrame, filename: PathLike) -> None:
    """Сохраняет отчёт в XLSX, создавая каталог при необходимости."""
    path = Path(filename)
    if path.suffix.lower() != ".xlsx":
        raise ValueError("Отчёт сохраняется в файл с расширением .xlsx")
    path.parent.mkdir(parents=True, exist_ok=True)
    report.to_excel(path, index=False, engine="openpyxl")
    logger.info("Excel-отчёт сохранён: строк %d", len(report))


@overload
def save_report(function: ReportFunction) -> ReportFunction: ...


@overload
def save_report(
    function: None = None, *, filename: Optional[PathLike] = None
) -> Callable[[ReportFunction], ReportFunction]: ...


def save_report(
    function: Optional[ReportFunction] = None, *, filename: Optional[PathLike] = None
) -> Union[ReportFunction, Callable[[ReportFunction], ReportFunction]]:
    """@save_report или @save_report(filename='...xlsx').

    По умолчанию: reports/<имя_функции>.xlsx относительно корня проекта.
    Существующий файл с тем же именем перезаписывается.
    """

    def decorate(func: ReportFunction) -> ReportFunction:
        @wraps(func)
        def wrapped(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result = func(*args, **kwargs)
            destination = filename or ROOT / "reports" / f"{func.__name__}.xlsx"
            write_report(result, destination)
            return result

        return wrapped

    return decorate(function) if function is not None else decorate


def build_category_report(
    transactions: pd.DataFrame, category: str, date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает успешные расходы категории за три месяца до даты включительно.

    Дата: YYYY-MM-DD, по умолчанию сегодня. Границы включены целиком:
    для 20.05.2020 — с 20.02.2020 00:00 до 20.05.2020 23:59:59.999999999.
    Возвращаются исходные столбцы; платежи сохраняют знак и валюту.
    """
    end = pd.Timestamp(datetime.strptime(date, "%Y-%m-%d") if date else datetime.now())
    end = end.normalize()
    start = end - pd.DateOffset(months=3)
    data = successful_transactions(prepare_transactions(transactions, ("Категория",)))
    mask = (
        data["Дата операции"].ge(start)
        & data["Дата операции"].lt(end + pd.Timedelta(days=1))
        & data["Категория"].eq(category)
        & data["Сумма платежа"].lt(0)
    )
    result = data.loc[mask].copy()
    logger.info("Сформирован отчёт по категории: строк %d", len(result))
    return result


@save_report
def spending_by_category(
    transactions: pd.DataFrame, category: str, date: Optional[str] = None
) -> pd.DataFrame:
    """Возвращает траты за три месяца и сохраняет reports/spending_by_category.xlsx."""
    return build_category_report(transactions, category, date)
