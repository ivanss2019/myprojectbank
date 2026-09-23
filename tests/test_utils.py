"""Тесты для модуля src.utils."""

import json
from pathlib import Path
from typing import Any, Dict, List

from src.utils import read_transactions_json


class TestReadTransactionsJson:
    """Тесты для функции read_transactions_json."""

    def test_reads_valid_json_list(
        self, tmp_path: Path, transactions: List[Dict[str, Any]]
    ) -> None:
        """Из корректного JSON-файла со списком возвращается тот же
        список словарей."""
        json_file = tmp_path / "operations.json"
        json_file.write_text(
            json.dumps(transactions, ensure_ascii=False), encoding="utf-8"
        )

        result = read_transactions_json(str(json_file))

        assert result == transactions

    def test_file_not_found_returns_empty_list(self, tmp_path: Path) -> None:
        """Если файла по указанному пути не существует, возвращается
        пустой список."""
        missing_file = tmp_path / "no_such_file.json"

        result = read_transactions_json(str(missing_file))

        assert result == []

    def test_empty_file_returns_empty_list(self, tmp_path: Path) -> None:
        """Если файл существует, но пуст (0 байт), возвращается пустой
        список."""
        empty_file = tmp_path / "empty.json"
        empty_file.write_text("", encoding="utf-8")

        result = read_transactions_json(str(empty_file))

        assert result == []

    def test_json_not_a_list_returns_empty_list(self, tmp_path: Path) -> None:
        """Если в файле корректный JSON, но не список (например,
        словарь), возвращается пустой список."""
        dict_file = tmp_path / "not_a_list.json"
        dict_file.write_text(
            json.dumps({"id": 1, "state": "EXECUTED"}), encoding="utf-8"
        )

        result = read_transactions_json(str(dict_file))

        assert result == []

    def test_invalid_json_returns_empty_list(self, tmp_path: Path) -> None:
        """Если содержимое файла — не валидный JSON, возвращается пустой
        список, а не исключение."""
        broken_file = tmp_path / "broken.json"
        broken_file.write_text("{not valid json", encoding="utf-8")

        result = read_transactions_json(str(broken_file))

        assert result == []

    def test_empty_json_list_returns_empty_list(self, tmp_path: Path) -> None:
        """Пустой список [] в файле корректно возвращается как есть."""
        json_file = tmp_path / "empty_list.json"
        json_file.write_text("[]", encoding="utf-8")

        result = read_transactions_json(str(json_file))

        assert result == []

    def test_returns_new_list_not_reference_issue(self, tmp_path: Path) -> None:
        """Возвращаемый список — обычный список словарей, пригодный для
        дальнейшей обработки (например, через filter_by_currency)."""
        data = [{"id": 1, "operationAmount": {"currency": {"code": "USD"}}}]
        json_file = tmp_path / "operations.json"
        json_file.write_text(json.dumps(data), encoding="utf-8")

        result = read_transactions_json(str(json_file))

        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)
