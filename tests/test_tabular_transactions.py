"""Проверки чтения CSV/XLSX, включая настоящие файлы задания."""

from pathlib import Path
from typing import Any, Callable, Dict, List
from unittest.mock import Mock, patch
from zipfile import BadZipFile

import pandas as pd
import pytest

from src.file_operations import read_transactions_csv, read_transactions_excel

Reader = Callable[[str], List[Dict[str, Any]]]
READERS = [(read_transactions_csv, "csv"), (read_transactions_excel, "xlsx")]


@pytest.mark.parametrize("reader,extension", READERS)
def test_reads_real_table(reader: Reader, extension: str, tmp_path: Path) -> None:
    """Сохраняются данные, ведущие нули, кириллица и пропуски."""
    rows = [
        {
            "id": 1,
            "amount": 123.45,
            "currency_code": "RUB",
            "from": "00001234567890123456",
            "to": "Счет 123",
            "description": "Перевод; с карты\nна счет",
        },
        {
            "id": 2,
            "amount": 0.0,
            "currency_code": "USD",
            "from": None,
            "to": "Счет 456",
            "description": "Открытие вклада",
        },
    ]
    path = tmp_path / f"transactions.{extension}"
    table = pd.DataFrame(rows)
    if extension == "csv":
        table.to_csv(path, sep=";", index=False, encoding="utf-8-sig")
    else:
        table.to_excel(path, index=False, engine="openpyxl")
    assert reader(str(path)) == rows


@pytest.mark.parametrize("reader,extension", READERS)
def test_missing_file(reader: Reader, extension: str, tmp_path: Path) -> None:
    """Отсутствующий файл возвращает пустой список."""
    assert reader(str(tmp_path / f"missing.{extension}")) == []


@pytest.mark.parametrize("reader,extension", READERS)
def test_zero_byte_file(reader: Reader, extension: str, tmp_path: Path) -> None:
    """Файл без содержимого возвращает пустой список."""
    path = tmp_path / f"empty.{extension}"
    path.touch()
    assert reader(str(path)) == []


@pytest.mark.parametrize("reader,extension", READERS)
def test_headers_only(reader: Reader, extension: str, tmp_path: Path) -> None:
    """Таблица с заголовками без строк возвращает пустой список."""
    path = tmp_path / f"headers.{extension}"
    table = pd.DataFrame(columns=["id", "amount"])
    if extension == "csv":
        table.to_csv(path, sep=";", index=False)
    else:
        table.to_excel(path, index=False, engine="openpyxl")
    assert reader(str(path)) == []


def test_empty_excel_sheet(tmp_path: Path) -> None:
    """Пустой лист Excel возвращает пустой список."""
    path = tmp_path / "empty.xlsx"
    pd.DataFrame().to_excel(path, index=False, engine="openpyxl")
    assert read_transactions_excel(str(path)) == []


@pytest.mark.parametrize("content", [b'id;amount\n1;"unfinished', b"id;amount\n1;\xff"])
def test_invalid_csv(content: bytes, tmp_path: Path) -> None:
    """Повреждённый CSV или неверная кодировка обрабатываются."""
    path = tmp_path / "invalid.csv"
    path.write_bytes(content)
    assert read_transactions_csv(str(path)) == []


def test_invalid_excel(tmp_path: Path) -> None:
    """Файл, не являющийся XLSX, возвращает пустой список."""
    path = tmp_path / "invalid.xlsx"
    path.write_text("This is not an XLSX workbook", encoding="utf-8")
    assert read_transactions_excel(str(path)) == []


@pytest.mark.parametrize(
    "reader,method",
    [
        (read_transactions_csv, "read_csv"),
        (read_transactions_excel, "read_excel"),
    ],
)
def test_pandas_called(reader: Reader, method: str) -> None:
    """Mock и patch проверяют параметры чтения обоих форматов."""
    with patch(
        f"src.file_operations.pd.{method}",
        new_callable=Mock,
        return_value=pd.DataFrame([{"id": 7}]),
    ) as mock:
        assert reader("input") == [{"id": 7}]
    if method == "read_csv":
        mock.assert_called_once_with(
            "input", sep=";", encoding="utf-8-sig", dtype={"from": str, "to": str}
        )
    else:
        mock.assert_called_once_with(
            "input", engine="openpyxl", dtype={"from": str, "to": str}
        )


@pytest.mark.parametrize("error", [BadZipFile("broken"), ValueError("no worksheets")])
def test_excel_read_error(error: Exception) -> None:
    """Ошибки архива и структуры книги обрабатываются."""
    with patch("src.file_operations.pd.read_excel", side_effect=error):
        assert read_transactions_excel("broken.xlsx") == []


@pytest.mark.parametrize(
    "reader,method",
    [
        (read_transactions_csv, "read_csv"),
        (read_transactions_excel, "read_excel"),
    ],
)
def test_permission_error_propagates(reader: Reader, method: str) -> None:
    """Ошибка доступа передаётся вызывающему коду."""
    with patch(f"src.file_operations.pd.{method}", side_effect=PermissionError):
        with pytest.raises(PermissionError):
            reader("private")


@pytest.mark.parametrize(
    "reader,filename",
    [
        (read_transactions_csv, "transactions.csv"),
        (read_transactions_excel, "transactions_excel.xlsx"),
    ],
)
def test_reference_file(reader: Reader, filename: str) -> None:
    """Эталонный файл содержит ожидаемые строки и поля."""
    path = Path(__file__).resolve().parents[1] / "data" / filename
    rows = reader(str(path))
    assert len(rows) == 1000
    assert set(rows[0]) == {
        "id",
        "state",
        "date",
        "amount",
        "currency_name",
        "currency_code",
        "from",
        "to",
        "description",
    }
    assert all(isinstance(row, dict) for row in rows)
    assert any(row["from"] is None for row in rows)


def test_reference_formats_match() -> None:
    """Оба эталонных файла возвращают одинаковые транзакции."""
    data_dir = Path(__file__).resolve().parents[1] / "data"
    csv_rows = read_transactions_csv(str(data_dir / "transactions.csv"))
    excel_rows = read_transactions_excel(str(data_dir / "transactions_excel.xlsx"))
    assert csv_rows == excel_rows
    assert csv_rows[0] == {
        "id": 650703,
        "state": "EXECUTED",
        "date": "2023-09-05T11:30:32Z",
        "amount": 16210,
        "currency_name": "Sol",
        "currency_code": "PEN",
        "from": "Счет 58803664561298323391",
        "to": "Счет 39745660563456619397",
        "description": "Перевод организации",
    }
