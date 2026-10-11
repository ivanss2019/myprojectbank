"""Календарные границы отчёта и оба способа использования декоратора."""

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from src.reports import (
    build_category_report,
    save_report,
    spending_by_category,
    write_report,
)


def test_three_calendar_months():
    data = pd.DataFrame(
        {
            "Дата операции": [
                "19.02.2020 23:59:59",
                "20.02.2020 00:00:00",
                "20.05.2020 23:59:59",
                "21.05.2020 00:00:00",
                "01.05.2020",
                "01.05.2020",
                "01.05.2020",
            ],
            "Сумма платежа": [-10, -20, -30, -40, 50, -60, -70],
            "Категория": ["Еда"] * 6 + ["Такси"],
            "Статус": ["OK"] * 5 + ["FAILED", "OK"],
        }
    )
    original = data.copy(deep=True)
    result = build_category_report(data, "Еда", "2020-05-20")
    assert result["Сумма платежа"].tolist() == [-20, -30]
    assert_frame_equal(data, original)


def test_month_end_and_default_today():
    data = pd.DataFrame(
        {
            "Дата операции": ["28.02.2020", "29.02.2020"],
            "Сумма платежа": [-10, -20],
            "Категория": ["Еда", "Еда"],
        }
    )
    with patch("src.reports.datetime") as clock:
        clock.now.return_value = datetime(2020, 5, 31, 12)
        result = build_category_report(data, "Еда")
    assert result["Сумма платежа"].tolist() == [-20]


def test_default_report_filename(frame, tmp_path):
    with patch("src.reports.ROOT", tmp_path):
        result = spending_by_category(frame, "Еда", "2020-05-20")
    saved = pd.read_excel(tmp_path / "reports" / "spending_by_category.xlsx")
    assert saved["Сумма платежа"].tolist() == result["Сумма платежа"].tolist()
    assert spending_by_category.__name__ == "spending_by_category"


def test_named_decorator(frame, tmp_path):
    target = tmp_path / "nested" / "custom.xlsx"
    decorated = save_report(filename=target)(build_category_report)
    result = decorated(frame, "Несуществующая", "2020-05-20")
    assert result.empty
    assert pd.read_excel(target).columns.tolist() == result.columns.tolist()
    assert decorated.__name__ == "build_category_report"


def test_decorator_with_parentheses(frame, tmp_path):
    with patch("src.reports.ROOT", tmp_path):
        result = save_report()(build_category_report)(frame, "Еда", "2020-05-20")
    assert (tmp_path / "reports" / "build_category_report.xlsx").exists()
    assert not result.empty


def test_invalid_output_suffix(tmp_path):
    with pytest.raises(ValueError, match="xlsx"):
        write_report(pd.DataFrame(), tmp_path / "wrong.csv")


def test_failed_report_is_not_written(frame, tmp_path):
    path = tmp_path / "wrong.xlsx"
    with pytest.raises(ValueError):
        save_report(filename=path)(build_category_report)(frame, "Еда", "invalid")
    assert not path.exists()
