"""Функции для чтения исходных данных о транзакциях из файлов."""

import json
import logging
import os
from typing import Any, Dict, List

LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "utils.log")

logger = logging.getLogger("utils")
logger.setLevel(logging.DEBUG)
logger.propagate = False

file_formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
file_handler.setFormatter(file_formatter)
logger.addHandler(file_handler)


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
    except FileNotFoundError:
        logger.error("Файл %s не найден", file_path)
        return []
    except json.JSONDecodeError:
        logger.error("Файл %s не содержит валидный JSON", file_path)
        return []

    if not isinstance(data, list):
        logger.error("Файл %s не содержит список транзакций", file_path)
        return []

    logger.info("Из файла %s прочитано транзакций: %d", file_path, len(data))
    return data
