"""Загрузка каталога интернет-магазина из JSON."""

import json
from pathlib import Path
from typing import List, Union

from src.category import Category
from src.product import Product


def load_categories(file_path: Union[str, Path]) -> List[Category]:
    """Читает UTF-8 JSON и превращает категории и вложенные товары в объекты.

    Ожидается список категорий с полями name, description, products.
    Ошибки чтения, JSON и отсутствующих полей передаются вызывающему коду.
    Каждый вызов создаёт новые категории и увеличивает общие счётчики.
    """
    with open(file_path, encoding="utf-8") as file:
        data = json.load(file)
    return [
        Category(
            name=item["name"],
            description=item["description"],
            products=[Product(**product) for product in item["products"]],
        )
        for item in data
    ]
