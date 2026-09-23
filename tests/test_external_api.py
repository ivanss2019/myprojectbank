"""Тесты для модуля src.external_api."""

from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
import requests

from src.external_api import convert_to_rub


@pytest.fixture
def rub_transaction() -> Dict[str, Any]:
    """Транзакция в рублях — конвертация не требуется."""
    return {
        "id": 441945886,
        "operationAmount": {
            "amount": "31957.58",
            "currency": {"name": "руб.", "code": "RUB"},
        },
    }


@pytest.fixture
def usd_transaction() -> Dict[str, Any]:
    """Транзакция в долларах — требует обращения к внешнему API."""
    return {
        "id": 41428829,
        "operationAmount": {
            "amount": "8221.37",
            "currency": {"name": "USD", "code": "USD"},
        },
    }


@pytest.fixture
def eur_transaction() -> Dict[str, Any]:
    """Транзакция в евро — требует обращения к внешнему API."""
    return {
        "id": 615064591,
        "operationAmount": {
            "amount": "10000.00",
            "currency": {"name": "EUR", "code": "EUR"},
        },
    }


class TestConvertToRubWithoutApiCall:
    """Для рублёвых транзакций внешний API не вызывается."""

    @patch("src.external_api.requests.get")
    def test_rub_transaction_returns_amount_as_float(
        self, mock_get: MagicMock, rub_transaction: Dict[str, Any]
    ) -> None:
        """Для валюты RUB сумма просто приводится к float."""
        result = convert_to_rub(rub_transaction)

        assert result == 31957.58
        assert isinstance(result, float)

    @patch("src.external_api.requests.get")
    def test_rub_transaction_does_not_call_external_api(
        self, mock_get: MagicMock, rub_transaction: Dict[str, Any]
    ) -> None:
        """Для валюты RUB запрос к внешнему API не выполняется."""
        convert_to_rub(rub_transaction)

        mock_get.assert_not_called()


class TestConvertToRubWithApiCall:
    """Для USD/EUR транзакций сумма конвертируется через внешний API
    (запрос замокан — реальные обращения в сеть не выполняются)."""

    @patch("src.external_api.requests.get")
    def test_usd_transaction_returns_converted_amount(
        self, mock_get: MagicMock, usd_transaction: Dict[str, Any]
    ) -> None:
        """Результат конвертации USD -> RUB берётся из ответа API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": 750345.12}
        mock_get.return_value = mock_response

        result = convert_to_rub(usd_transaction)

        assert result == 750345.12
        assert isinstance(result, float)

    @patch("src.external_api.requests.get")
    def test_eur_transaction_returns_converted_amount(
        self, mock_get: MagicMock, eur_transaction: Dict[str, Any]
    ) -> None:
        """Результат конвертации EUR -> RUB берётся из ответа API."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": 999999.99}
        mock_get.return_value = mock_response

        result = convert_to_rub(eur_transaction)

        assert result == 999999.99

    @patch("src.external_api.requests.get")
    def test_api_called_with_correct_params_and_headers(
        self, mock_get: MagicMock, usd_transaction: Dict[str, Any]
    ) -> None:
        """API вызывается с верными параметрами конвертации (from, to,
        amount) и API-ключом в заголовке."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"result": 1.0}
        mock_get.return_value = mock_response

        with patch("src.external_api.os.getenv", return_value="test_key"):
            convert_to_rub(usd_transaction)

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {
            "to": "RUB",
            "from": "USD",
            "amount": 8221.37,
        }
        assert kwargs["headers"] == {"apikey": "test_key"}

    @patch("src.external_api.requests.get")
    def test_api_response_status_is_checked(
        self, mock_get: MagicMock, usd_transaction: Dict[str, Any]
    ) -> None:
        """При ошибочном HTTP-статусе исключение из raise_for_status
        пробрасывается наружу."""
        mock_response = MagicMock()
        mock_response.raise_for_status.side_effect = requests.HTTPError(
            "401 Unauthorized"
        )
        mock_get.return_value = mock_response

        with pytest.raises(requests.HTTPError):
            convert_to_rub(usd_transaction)

    @patch("src.external_api.requests.get")
    def test_missing_result_in_response_raises_value_error(
        self, mock_get: MagicMock, usd_transaction: Dict[str, Any]
    ) -> None:
        """Если внешний API не вернул ключ result (например, из-за
        ошибки конвертации), выбрасывается ValueError с понятным
        сообщением."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": False, "error": "boom"}
        mock_get.return_value = mock_response

        with pytest.raises(ValueError, match="USD"):
            convert_to_rub(usd_transaction)
