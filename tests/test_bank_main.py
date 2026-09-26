"""Сценарии консольной программы и совместимость источников данных."""

import runpy
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import patch

import bank_main as app
import pytest

from src.file_operations import normalize_transactions
from src.processing import sort_by_date
from src.widget import format_transaction, get_date


@pytest.fixture
def transactions() -> List[Dict[str, Any]]:
    """Набор с разными статусами, валютами и отсутствующим отправителем."""
    return [
        {
            "state": "EXECUTED",
            "date": "2019-12-08T10:00:00Z",
            "description": "Открытие вклада",
            "to": "Счет 12345678901234564321",
            "operationAmount": {"amount": "40542.00", "currency": {"code": "RUB"}},
        },
        {
            "state": "EXECUTED",
            "date": "2019-11-12T10:00:00Z",
            "description": "Перевод с карты на карту",
            "from": "MasterCard 7771271234563727",
            "to": "Visa Platinum 1293381234569203",
            "operationAmount": {"amount": "130", "currency": {"code": "USD"}},
        },
        {
            "state": "EXECUTED",
            "date": "2018-07-18T10:00:00Z",
            "description": "Перевод организации",
            "from": "Visa Platinum 7492651234567202",
            "to": "Счет 12345678901234560034",
            "operationAmount": {"amount": "8390.50", "currency": {"code": "RUB"}},
        },
        {
            "state": "CANCELED",
            "date": "2018-06-03T10:00:00Z",
            "description": "Перевод со счета на счет",
            "from": "Счет 12345678901234562935",
            "to": "Счет 12345678901234564321",
            "operationAmount": {"amount": "8200", "currency": {"code": "EUR"}},
        },
        {
            "state": "PENDING",
            "date": "2020-06-03T10:00:00Z",
            "description": "Ожидающий перевод",
            "to": "Счет 12345678901234564321",
            "operationAmount": {"amount": "0", "currency": {"code": "RUB"}},
        },
    ]


def test_normalize(transactions: List[Dict[str, Any]]) -> None:
    """Плоские и вложенные записи приводятся к общему виду без изменения входа."""
    flat = {
        "state": " executed ",
        "amount": 42.5,
        "currency_code": "RUB",
        "currency_name": "Ruble",
        "from": None,
    }
    data = [
        flat,
        transactions[0],
        {},
        {"state": None, "amount": None},
        {"description": "Без статуса"},
    ]
    before = deepcopy(data)
    result = normalize_transactions(data)
    assert len(result) == 3
    assert result[0]["state"] == "EXECUTED"
    assert result[0]["operationAmount"] == {
        "amount": 42.5,
        "currency": {"code": "RUB", "name": "Ruble"},
    }
    assert result[1] == transactions[0]
    assert result[1] is not transactions[0]
    assert result[2]["state"] == ""
    assert data == before
    assert normalize_transactions([]) == []


def test_formatting(transactions: List[Dict[str, Any]]) -> None:
    """Вывод соответствует примеру, реквизиты маскируются, сумма сохраняется."""
    assert format_transaction(transactions[0]) == (
        "08.12.2019 Открытие вклада\nСчет **4321\nСумма: 40542 руб."
    )
    assert format_transaction(transactions[1]) == (
        "12.11.2019 Перевод с карты на карту\n"
        "MasterCard 7771 27** **** 3727 -> Visa Platinum 1293 38** **** 9203\n"
        "Сумма: 130 USD"
    )
    assert "Сумма: 8390.5 руб." in format_transaction(transactions[2])
    assert "Счет **2935 -> Счет **4321\nСумма: 8200 EUR" in format_transaction(
        transactions[3]
    )
    assert "Сумма: 0 руб." in format_transaction(transactions[4])


def test_z_dates(transactions: List[Dict[str, Any]]) -> None:
    """Даты с UTC-суффиксом из CSV/XLSX поддерживаются в том числе на Python 3.9."""
    assert get_date("2023-09-05T11:30:32Z") == "05.09.2023"
    assert sort_by_date(transactions)[0] == transactions[4]
    assert sort_by_date(transactions, descending=False)[0] == transactions[3]


@pytest.mark.parametrize(
    "choice,label,reader,filename",
    [
        ("1", "JSON", "read_transactions_json", "operations.json"),
        ("2", "CSV", "read_transactions_csv", "transactions.csv"),
        ("3", "XLSX", "read_transactions_excel", "transactions_excel.xlsx"),
    ],
)
def test_sources(
    choice: str,
    label: str,
    reader: str,
    filename: str,
    transactions: List[Dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Все пункты меню вызывают нужную функцию чтения и показывают выбор."""
    with (
        patch("builtins.input", side_effect=[choice, "Executed", "нет", "нет", "нет"]),
        patch(f"bank_main.{reader}", return_value=transactions) as mock,
    ):
        app.main()
    mock.assert_called_once_with(str(app.DATA_DIR / filename))
    out = capsys.readouterr().out
    assert f"Для обработки выбран {label}-файл." in out
    assert 'Операции отфильтрованы по статусу "EXECUTED"' in out
    assert "Всего банковских операций в выборке: 3" in out
    assert "130 USD" in out
    assert "8200 EUR" not in out


def test_all_filters(
    transactions: List[Dict[str, Any]], capsys: pytest.CaptureFixture[str]
) -> None:
    """Ошибочный ввод повторяется, затем применяются все выбранные фильтры."""
    answers = [
        "9",
        "1",
        "test",
        " executed ",
        "maybe",
        " Да ",
        "ошибка",
        "ПО ВОЗРАСТАНИЮ",
        "да",
        "да",
        "ПЕРЕВОД",
    ]
    with (
        patch("builtins.input", side_effect=answers),
        patch("bank_main.read_transactions_json", return_value=transactions),
    ):
        app.main()
    out = capsys.readouterr().out
    assert 'Статус операции "test" недоступен.' in out
    assert out.count("Недопустимый ответ") == 3
    assert "Всего банковских операций в выборке: 1" in out
    assert "18.07.2018 Перевод организации" in out
    assert "130 USD" not in out
    assert "08.12.2019 Открытие вклада" not in out


@pytest.mark.parametrize(
    "direction,first,last",
    [
        ("по возрастанию", "18.07.2018", "08.12.2019"),
        ("по убыванию", "08.12.2019", "18.07.2018"),
    ],
)
def test_sort_menu(
    direction: str,
    first: str,
    last: str,
    transactions: List[Dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Меню сортирует операции в обоих направлениях."""
    with (
        patch(
            "builtins.input",
            side_effect=["1", "EXECUTED", "да", direction, "нет", "нет"],
        ),
        patch("bank_main.read_transactions_json", return_value=transactions),
    ):
        app.main()
    out = capsys.readouterr().out
    assert out.index(first) < out.index(last)


@pytest.mark.parametrize(
    "status,expected", [("canceled", "8200 EUR"), ("PeNdInG", "Сумма: 0 руб.")]
)
def test_other_statuses(
    status: str,
    expected: str,
    transactions: List[Dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Все разрешённые статусы распознаются независимо от регистра."""
    with (
        patch("builtins.input", side_effect=["1", status, "нет", "нет", "нет"]),
        patch("bank_main.read_transactions_json", return_value=transactions),
    ):
        app.main()
    out = capsys.readouterr().out
    assert "Всего банковских операций в выборке: 1" in out
    assert expected in out


@pytest.mark.parametrize("empty_source", [True, False])
def test_empty_result(
    empty_source: bool,
    transactions: List[Dict[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Пустой файл и отсутствие совпадений выводят понятное сообщение."""
    with (
        patch(
            "builtins.input",
            side_effect=["1", "EXECUTED", "нет", "нет", "да", "ничего"],
        ),
        patch(
            "bank_main.read_transactions_json",
            return_value=[] if empty_source else transactions,
        ),
    ):
        app.main()
    assert (
        "Не найдено ни одной транзакции, подходящей под ваши условия фильтрации"
        in capsys.readouterr().out
    )


@pytest.mark.parametrize("choice", ["1", "2", "3"])
def test_real_files(choice: str, capsys: pytest.CaptureFixture[str]) -> None:
    """Настоящие файлы проходят весь сценарий, включая нормализацию и маскировку."""
    with patch(
        "builtins.input",
        side_effect=[choice, "EXECUTED", "да", "по убыванию", "да", "нет"],
    ):
        app.main()
    out = capsys.readouterr().out
    assert "Всего банковских операций в выборке:" in out
    assert "Сумма:" in out
    assert " USD" not in out
    assert " EUR" not in out


def test_entrypoint(
    capsys: pytest.CaptureFixture[str], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Банковский сценарий находит data независимо от текущей папки."""
    path = Path(app.__file__).resolve()
    monkeypatch.chdir(tmp_path)
    with patch("builtins.input", side_effect=["1", "pending", "нет", "нет", "нет"]):
        runpy.run_path(str(path), run_name="__main__")
    assert "Не найдено ни одной транзакции" in capsys.readouterr().out
