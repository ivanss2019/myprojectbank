"""Категории товаров и общие счётчики каталога."""

from typing import ClassVar, List

from src.product import Product


class Category:
    """Группирует товары и учитывает все созданные категории и позиции."""

    category_count: ClassVar[int] = 0
    product_count: ClassVar[int] = 0

    def __init__(self, name: str, description: str, products: List[Product]) -> None:
        self.name = name
        self.description = description
        self.products = products
        Category.category_count += 1
        Category.product_count += len(products)
