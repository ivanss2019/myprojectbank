"""Функции для нового функционала виджета: маскировка "тип + номер" и даты."""

from datetime import datetime

from .masks import get_mask_account, get_mask_card_number


def mask_account_card(info: str) -> str:
    """Маскирует номер карты или счета в строке вида "Тип Номер".

    Строка приходит одним аргументом, например:
        "Visa Platinum 7000792289606361"
        "Maestro 7000792289606361"
        "Счет 73654108430135874305"

    Внутри строка разбирается на название и номер (это не два отдельных
    аргумента функции, а внутренняя логика), после чего номер маскируется
    подходящей функцией — get_mask_card_number для карт или
    get_mask_account для счетов.

    Пример:
        >>> mask_account_card("Visa Platinum 7000792289606361")
        'Visa Platinum 7000 79** **** 6361'
        >>> mask_account_card("Счет 73654108430135874305")
        'Счет **4305'

    Args:
        info: строка вида "<тип> <номер>".

    Returns:
        Строка с тем же типом и замаскированным номером.
    """
    name, number = info.rsplit(maxsplit=1)
    if "счет" in name.lower():
        masked_number = get_mask_account(number)
    else:
        masked_number = get_mask_card_number(number)
    return f"{name} {masked_number}"


def get_date(date_string: str) -> str:
    """Преобразует дату из ISO-формата в формат "ДД.ММ.ГГГГ".

    Пример:
        >>> get_date("2024-03-11T02:26:18.671407")
        '11.03.2024'

    Args:
        date_string: дата в формате ISO 8601,
            например "2024-03-11T02:26:18.671407".

    Returns:
        Дата в формате "ДД.ММ.ГГГГ".
    """
    parsed_date = datetime.fromisoformat(date_string)
    return parsed_date.strftime("%d.%m.%Y")
