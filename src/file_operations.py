"""Чтение финансовых транзакций из CSV- и Excel-файлов."""

import logging
from typing import Any, Dict, List
from zipfile import BadZipFile

import pandas as pd

logger = logging.getLogger(__name__)


def _table_to_transactions(table: pd.DataFrame) -> List[Dict[str, Any]]:
    """Возвращает строки таблицы как словари, заменяя пропуски на None."""
    table = table.astype(object).where(pd.notna(table), None)
    return [
        {str(key): value for key, value in row.items()}
        for row in table.to_dict(orient="records")
    ]


def read_transactions_csv(file_path: str) -> List[Dict[str, Any]]:
    """Читает CSV в UTF-8 с разделителем «;» в список словарей.

    Ключи соответствуют заголовкам таблицы, пропуски заменяются на None.
    Отсутствующий, пустой или некорректный файл даёт пустой список.
    Ошибки доступа к файлу передаются вызывающему коду.
    """
    try:
        table = pd.read_csv(
            file_path, sep=";", encoding="utf-8-sig", dtype={"from": str, "to": str}
        )
    except (
        FileNotFoundError,
        pd.errors.EmptyDataError,
        pd.errors.ParserError,
        UnicodeDecodeError,
    ) as error:
        logger.error("Не удалось прочитать CSV %s: %s", file_path, error)
        return []

    transactions = _table_to_transactions(table)
    logger.info("Из файла %s прочитано транзакций: %d", file_path, len(transactions))
    return transactions


def read_transactions_excel(file_path: str) -> List[Dict[str, Any]]:
    """Читает первый лист XLSX в список словарей через pandas/openpyxl.

    Ключи соответствуют заголовкам таблицы, пропуски заменяются на None.
    Отсутствующий, пустой или некорректный файл даёт пустой список.
    Ошибки доступа к файлу передаются вызывающему коду.
    """
    try:
        table = pd.read_excel(
            file_path, engine="openpyxl", dtype={"from": str, "to": str}
        )
    except (FileNotFoundError, BadZipFile, ValueError) as error:
        logger.error("Не удалось прочитать XLSX %s: %s", file_path, error)
        return []

    transactions = _table_to_transactions(table)
    logger.info("Из файла %s прочитано транзакций: %d", file_path, len(transactions))
    return transactions


def normalize_transactions(data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Приводит плоские CSV/XLSX-строки к структуре JSON для общего меню.

    Создаёт новые словари, не изменяя исходные данные. Пустые строки
    пропускаются. Сумма и валюта помещаются в operationAmount, статус
    приводится к верхнему регистру. Вложенная структура JSON сохраняется.
    """
    transactions = []
    for row in data:
        if not row or not any(value is not None for value in row.values()):
            continue
        transaction = dict(row)
        transaction["state"] = str(row.get("state") or "").strip().upper()
        if "operationAmount" not in row:
            transaction["operationAmount"] = {
                "amount": row.get("amount"),
                "currency": {
                    "name": row.get("currency_name"),
                    "code": row.get("currency_code"),
                },
            }
        transactions.append(transaction)
    return transactions
