"""Запуск курсовой: python -m src.main --help."""

import argparse
import logging
from typing import Optional, Sequence

from dotenv import load_dotenv

from src.analysis_utils import (
    ROOT,
    PathLike,
    dataframe_records,
    load_user_settings,
    read_excel_transactions,
)
from src.reports import build_category_report, save_report
from src.services import phone_search, profitable_cashback_categories, simple_search
from src.views import events_page, home_page


def main(
    date_time: str,
    file_path: PathLike = ROOT / "data" / "operations.xlsx",
    settings_path: PathLike = ROOT / "user_settings.json",
) -> str:
    """Принимает дату и время, читает файлы и возвращает JSON главной страницы."""
    load_dotenv(ROOT / ".env")
    transactions = read_excel_transactions(file_path)
    settings = load_user_settings(settings_path)
    return home_page(date_time, transactions, settings)


def cli(argv: Optional[Sequence[str]] = None) -> None:
    """Выбирает страницу, поиск или отчёт; ошибки ввода выводит без traceback."""
    parser = argparse.ArgumentParser(description="Анализ банковских транзакций")
    parser.add_argument("--file", default=str(ROOT / "data" / "operations.xlsx"))
    commands = parser.add_subparsers(dest="command", required=True)
    home = commands.add_parser("home", help="JSON главной страницы")
    home.add_argument("date", help="YYYY-MM-DD HH:MM:SS")
    home.add_argument("--settings", default=str(ROOT / "user_settings.json"))
    events = commands.add_parser("events", help="JSON страницы События")
    events.add_argument("date", help="YYYY-MM-DD")
    events.add_argument("--range", choices=["W", "M", "Y", "ALL"], default="M")
    events.add_argument("--settings", default=str(ROOT / "user_settings.json"))
    commands.add_parser("phones", help="Поиск операций с мобильными телефонами")
    cashback = commands.add_parser("cashback", help="Выгодные категории кешбэка")
    cashback.add_argument("year", type=int)
    cashback.add_argument("month", type=int)
    cashback.add_argument("--rate", type=float, default=5.0)
    search = commands.add_parser("search", help="Поиск по описанию и категории")
    search.add_argument("query")
    report = commands.add_parser("report", help="Траты по категории в Excel")
    report.add_argument("category")
    report.add_argument("--date", help="YYYY-MM-DD (по умолчанию сегодня)")
    report.add_argument(
        "--output", default=str(ROOT / "reports" / "spending_by_category.xlsx")
    )
    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
    )
    try:
        if args.command == "home":
            print(main(args.date, args.file, args.settings))
        elif args.command == "events":
            load_dotenv(ROOT / ".env")
            print(
                events_page(
                    args.date,
                    read_excel_transactions(args.file),
                    load_user_settings(args.settings),
                    args.range,
                )
            )
        elif args.command in {"search", "phones", "cashback"}:
            data = dataframe_records(read_excel_transactions(args.file))
            if args.command == "search":
                print(simple_search(args.query, data))
            elif args.command == "phones":
                print(phone_search(data))
            else:
                print(
                    profitable_cashback_categories(
                        data, args.year, args.month, args.rate
                    )
                )
        else:
            # Переопределяем имя файла без повторного сохранения отчёта по умолчанию.
            report_function = save_report(filename=args.output)(build_category_report)
            result = report_function(
                read_excel_transactions(args.file), args.category, args.date
            )
            print(f"Отчёт сохранён: {args.output}. Операций: {len(result)}")
    except (OSError, ValueError, ImportError) as error:
        parser.exit(1, f"Ошибка: {error}\n")


if __name__ == "__main__":
    cli()
