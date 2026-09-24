"""Тесты для модуля src.utils."""

from unittest.mock import MagicMock, mock_open, patch

from src.utils import read_transactions_json


class TestReadTransactionsJson:
    """Тесты для функции read_transactions_json."""

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"id": 1, "state": "EXECUTED"}]',
    )
    def test_reads_valid_json_list(self, mock_file: MagicMock) -> None:
        """Из корректного JSON-файла со списком возвращается тот же
        список словарей."""
        result = read_transactions_json("data/operations.json")

        assert result == [{"id": 1, "state": "EXECUTED"}]
        mock_file.assert_called_once_with("data/operations.json", "r", encoding="utf-8")

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_file_not_found_returns_empty_list(self, mock_file: MagicMock) -> None:
        """Если файла по указанному пути не существует, возвращается
        пустой список."""
        result = read_transactions_json("no_such_file.json")

        assert result == []

    @patch("builtins.open", new_callable=mock_open, read_data="")
    def test_empty_file_returns_empty_list(self, mock_file: MagicMock) -> None:
        """Если файл существует, но пуст (0 байт), возвращается пустой
        список."""
        result = read_transactions_json("empty.json")

        assert result == []

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='{"id": 1, "state": "EXECUTED"}',
    )
    def test_json_not_a_list_returns_empty_list(self, mock_file: MagicMock) -> None:
        """Если в файле корректный JSON, но не список (например,
        словарь), возвращается пустой список."""
        result = read_transactions_json("not_a_list.json")

        assert result == []

    @patch("builtins.open", new_callable=mock_open, read_data="{not valid json")
    def test_invalid_json_returns_empty_list(self, mock_file: MagicMock) -> None:
        """Если содержимое файла — не валидный JSON, возвращается пустой
        список, а не исключение."""
        result = read_transactions_json("broken.json")

        assert result == []

    @patch("builtins.open", new_callable=mock_open, read_data="[]")
    def test_empty_json_list_returns_empty_list(self, mock_file: MagicMock) -> None:
        """Пустой список [] в файле корректно возвращается как есть."""
        result = read_transactions_json("empty_list.json")

        assert result == []

    @patch(
        "builtins.open",
        new_callable=mock_open,
        read_data='[{"id": 1, "operationAmount": {"currency": {"code": "USD"}}}]',
    )
    def test_returns_list_of_dicts(self, mock_file: MagicMock) -> None:
        """Возвращаемый список — список словарей, пригодный для
        дальнейшей обработки (например, через filter_by_currency)."""
        result = read_transactions_json("data/operations.json")

        assert isinstance(result, list)
        assert all(isinstance(item, dict) for item in result)
