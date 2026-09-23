"""Функции для чтения исходных данных о транзакциях из файлов."""

import json
from typing import Any, Dict, List


def read_transactions_json(file_path: str) -> List[Dict[str, Any]]:
    """Читает список финансовых транзакций из JSON-файла.

    Пример:
        >>> import json
        >>> import tempfile
        >>> data = [{"id": 1, "state": "EXECUTED"}]
        >>> with tempfile.NamedTemporaryFile(
        ...     mode="w", suffix=".json", delete=False
        ... ) as tmp_file:
        ...     _ = json.dump(data, tmp_file)
        >>> read_transactions_json(tmp_file.name) == data
        True

    Args:
        file_path: путь к JSON-файлу с данными о транзакциях.

    Returns:
        Список словарей с данными транзакций. Если файл не найден, пуст
        или его содержимое — не список, возвращается пустой список.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as json_file:
            data = json.load(json_file)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

    if not isinstance(data, list):
        return []

    return data
