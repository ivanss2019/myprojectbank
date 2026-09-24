"""Функции маскировки номеров банковских карт и счетов."""

import logging
import os

LOG_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs"
)
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "masks.log")

logger = logging.getLogger("masks")
logger.setLevel(logging.DEBUG)
logger.propagate = False
_file_handler = logging.FileHandler(LOG_FILE, mode="w", encoding="utf-8")
_file_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)
logger.addHandler(_file_handler)


def get_mask_card_number(card_number: str) -> str:
    """Возвращает замаскированный номер банковской карты.

    Видны первые 6 и последние 4 цифры, номер разбит по блокам
    из 4 символов, разделенным пробелами: "XXXX XX** **** XXXX".

    Пример:
        >>> get_mask_card_number("7000792289606361")
        '7000 79** **** 6361'

    Args:
        card_number: номер карты в виде строки цифр.

    Returns:
        Замаскированный номер карты.
    """
    number = str(card_number)
    first_block = number[:4]
    second_block = number[4:6]
    last_block = number[-4:]
    masked = f"{first_block} {second_block}** **** {last_block}"
    logger.info("Номер карты успешно замаскирован")
    return masked


def get_mask_account(account_number: str) -> str:
    """Возвращает замаскированный номер банковского счета.

    Видны только последние 4 цифры, перед ними — две звездочки:
    "**XXXX".

    Пример:
        >>> get_mask_account("73654108430135874305")
        '**4305'

    Args:
        account_number: номер счета в виде строки цифр.

    Returns:
        Замаскированный номер счета.
    """
    number = str(account_number)
    masked = f"**{number[-4:]}"
    logger.info("Номер счета успешно замаскирован")
    return masked
