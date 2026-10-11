"""Проверка запуска приложения, реального Excel и конечных файлов отчёта."""

import json
import runpy
from unittest.mock import patch

import pandas as pd
import pytest

from src.analysis_utils import ROOT, read_excel_transactions
from src.main import cli, main


def test_main_on_provided_workbook(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text('{"user_currencies": [], "user_stocks": []}')
    result = json.loads(main("2021-12-31 23:59:59", settings_path=settings))
    assert set(result) == {
        "greeting",
        "cards",
        "top_transactions",
        "currency_rates",
        "stock_prices",
    }
    assert result["currency_rates"] == result["stock_prices"] == []
    assert len(result["top_transactions"]) == 5
    frame = read_excel_transactions(ROOT / "data" / "operations.xlsx")
    assert len(frame) == 6705
    dates = pd.to_datetime(frame["Дата операции"], format="%d.%m.%Y %H:%M:%S")
    monthly = frame.loc[
        (dates.dt.year == 2021)
        & (dates.dt.month == 12)
        & frame["Статус"].eq("OK")
        & frame["Валюта платежа"].eq("RUB")
    ]
    for card in result["cards"]:
        expenses = monthly.loc[
            monthly["Номер карты"].eq("*" + card["last_digits"])
            & monthly["Сумма платежа"].lt(0),
            "Сумма платежа",
        ]
        assert card["total_spent"] == pytest.approx(-expenses.sum())


def test_cli_home(frame, tmp_path, capsys):
    path = tmp_path / "data.xlsx"
    frame.to_excel(path, index=False)
    settings = tmp_path / "settings.json"
    settings.write_text('{"user_currencies": [], "user_stocks": []}')
    cli(
        [
            "--file",
            str(path),
            "home",
            "2020-05-20 12:00:00",
            "--settings",
            str(settings),
        ]
    )
    result = json.loads(capsys.readouterr().out)
    assert len(result["cards"]) == 3


def test_cli_search_whole_file(tmp_path, capsys):
    path = tmp_path / "data.xlsx"
    pd.DataFrame(
        {
            "Описание": ["Магнит", "МАГНИТ", "Такси"],
            "Категория": [None, "Еда", "Транспорт"],
            "Дата операции": ["2018-01-01", "2021-12-31", "2020-01-01"],
        }
    ).to_excel(path, index=False)
    cli(["--file", str(path), "search", "магнит"])
    assert len(json.loads(capsys.readouterr().out)) == 2


def test_cli_report(frame, tmp_path, capsys):
    source = tmp_path / "input.xlsx"
    output = tmp_path / "out" / "report.xlsx"
    frame.to_excel(source, index=False)
    cli(
        [
            "--file",
            str(source),
            "report",
            "Транспорт",
            "--date",
            "2020-05-20",
            "--output",
            str(output),
        ]
    )
    assert pd.read_excel(output)["Сумма платежа"].tolist() == [-7.94]
    assert "Операций: 1" in capsys.readouterr().out


def test_cli_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as error:
        cli(["--file", str(tmp_path / "missing.xlsx"), "search", "еда"])
    assert error.value.code == 1
    assert "Ошибка:" in capsys.readouterr().err


def test_module_entrypoint(capsys):
    with patch("sys.argv", ["src.main", "--help"]), pytest.raises(SystemExit) as error:
        runpy.run_path(str(ROOT / "src" / "main.py"), run_name="__main__")
    assert error.value.code == 0
    assert "Анализ банковских транзакций" in capsys.readouterr().out
