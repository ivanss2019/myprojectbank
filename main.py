"""Консольная программа для отбора и просмотра банковских транзакций."""

from pathlib import Path
from typing import Any, Callable, Dict, List

from src.file_operations import (
    normalize_transactions,
    read_transactions_csv,
    read_transactions_excel,
)
from src.generators import filter_by_currency
from src.processing import filter_by_state, process_bank_search, sort_by_date
from src.utils import read_transactions_json
from src.widget import format_transaction

DATA_DIR = Path(__file__).resolve().parent / "data"


def _ask_choice(prompt: str, choices: Dict[str, str]) -> str:
    """Повторяет вопрос до допустимого ответа, игнорируя регистр и пробелы."""
    while True:
        answer = input(prompt + "\n").strip().casefold()
        if answer in choices:
            return choices[answer]
        print("Недопустимый ответ. Попробуйте ещё раз.")


def _ask_yes_no(prompt: str) -> bool:
    """Запрашивает ответ Да/Нет без учёта регистра."""
    return _ask_choice(prompt + " Да/Нет", {"да": "yes", "нет": "no"}) == "yes"


def _choose_transactions() -> List[Dict[str, Any]]:
    """Выбирает источник данных и приводит транзакции к общей структуре."""
    sources: Dict[str, tuple[str, str, Callable[[str], List[Dict[str, Any]]]]] = {
        "1": ("JSON", "operations.json", read_transactions_json),
        "2": ("CSV", "transactions.csv", read_transactions_csv),
        "3": ("XLSX", "transactions_excel.xlsx", read_transactions_excel),
    }
    choice = _ask_choice(
        "Выберите необходимый пункт меню:\n"
        "1. Получить информацию о транзакциях из JSON-файла\n"
        "2. Получить информацию о транзакциях из CSV-файла\n"
        "3. Получить информацию о транзакциях из XLSX-файла",
        {"1": "1", "2": "2", "3": "3"},
    )
    label, filename, reader = sources[choice]
    print(f"Для обработки выбран {label}-файл.")
    return normalize_transactions(reader(str(DATA_DIR / filename)))


def _choose_status() -> str:
    """Запрашивает корректный статус и возвращает его в верхнем регистре."""
    while True:
        answer = input(
            "Введите статус, по которому необходимо выполнить фильтрацию.\n"
            "Доступные для фильтровки статусы: EXECUTED, CANCELED, PENDING\n"
        ).strip()
        if answer.upper() in {"EXECUTED", "CANCELED", "PENDING"}:
            return answer.upper()
        print(f'Статус операции "{answer}" недоступен.')


def main() -> None:
    """Читает операции, уточняет фильтры и печатает итоговую выборку."""
    print("Привет! Добро пожаловать в программу работы с банковскими транзакциями.")
    transactions = _choose_transactions()
    state = _choose_status()
    transactions = filter_by_state(transactions, state)
    print(f'Операции отфильтрованы по статусу "{state}"')

    if _ask_yes_no("Отсортировать операции по дате?"):
        direction = _ask_choice(
            "Отсортировать по возрастанию или по убыванию?",
            {
                "по возрастанию": "asc",
                "возрастанию": "asc",
                "по убыванию": "desc",
                "убыванию": "desc",
            },
        )
        transactions = sort_by_date(transactions, descending=direction == "desc")
    if _ask_yes_no("Выводить только рублевые транзакции?"):
        transactions = list(filter_by_currency(transactions, "RUB"))
    if _ask_yes_no(
        "Отфильтровать список транзакций по определенному слову в описании?"
    ):
        search = input("Введите строку поиска в описании:\n").strip()
        transactions = process_bank_search(transactions, search)

    print("Распечатываю итоговый список транзакций...")
    if not transactions:
        print("Не найдено ни одной транзакции, подходящей под ваши условия фильтрации")
        return
    print(f"Всего банковских операций в выборке: {len(transactions)}")
    for transaction in transactions:
        print("\n" + format_transaction(transaction))


if __name__ == "__main__":
    main()
