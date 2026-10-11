"""Ошибки ввода, Excel, настройки и нормализация типов JSON."""

import json

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.analysis_utils import (
    dataframe_records,
    load_user_settings,
    parse_datetime,
    prepare_transactions,
    read_excel_transactions,
)


def test_read_excel(frame, tmp_path):
    path = tmp_path / "data.xlsx"
    frame.to_excel(path, index=False)
    result = read_excel_transactions(path)
    assert len(result) == len(frame)
    assert result.columns.tolist() == frame.columns.tolist()


def test_missing_excel(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_excel_transactions(tmp_path / "missing.xlsx")


def test_invalid_excel(tmp_path):
    path = tmp_path / "broken.xlsx"
    path.write_text("not excel")
    with pytest.raises(ValueError):
        read_excel_transactions(path)


def test_settings(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(
            {"user_currencies": [" usd ", "USD", "eur"], "user_stocks": ["aapl"]}
        )
    )
    assert load_user_settings(path) == {
        "user_currencies": ["USD", "EUR"],
        "user_stocks": ["AAPL"],
    }


@pytest.mark.parametrize(
    "data",
    [
        [],
        {},
        {"user_currencies": "USD"},
        {"user_currencies": [None]},
        {"user_currencies": [""]},
        {"user_currencies": [], "user_stocks": [1]},
    ],
)
def test_invalid_settings(data, tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_user_settings(path)


@pytest.mark.parametrize("value", ["2020-5-1 00:00:00", "2020-02-30 12:00:00", "bad"])
def test_invalid_datetime(value):
    with pytest.raises(ValueError):
        parse_datetime(value)


def test_prepare_dates_and_copy():
    frame = pd.DataFrame(
        {
            "Дата операции": ["2020-05-01", "02.05.2020", pd.Timestamp("2020-05-03")],
            "Сумма платежа": ["-1.50", 0, 2],
        }
    )
    original = frame.copy(deep=True)
    result = prepare_transactions(frame)
    assert result["Дата операции"].dt.day.tolist() == [1, 2, 3]
    assert result["Сумма платежа"].tolist() == [-1.5, 0, 2]
    assert_frame_equal(frame, original)


@pytest.mark.parametrize(
    "column, value",
    [
        ("Дата операции", "bad"),
        ("Сумма платежа", "bad"),
        ("Сумма платежа", float("inf")),
        ("Сумма платежа", float("nan")),
    ],
)
def test_invalid_required_values(frame, column, value):
    frame[column] = value
    with pytest.raises(ValueError):
        prepare_transactions(frame)


def test_missing_columns():
    with pytest.raises(ValueError, match="Отсутствуют столбцы"):
        prepare_transactions(pd.DataFrame())


def test_dataframe_json_types():
    frame = pd.DataFrame(
        {"date": [pd.Timestamp("2020-01-01"), pd.NaT], "amount": [10.5, float("nan")]}
    )
    assert dataframe_records(frame) == [
        {"date": "2020-01-01T00:00:00.000", "amount": 10.5},
        {"date": None, "amount": None},
    ]
