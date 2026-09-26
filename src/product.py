"""Товар интернет-магазина."""


class Product:
    """Хранит название, описание, цену и остаток товара на складе."""

    def __init__(
        self, name: str, description: str, price: float, quantity: int
    ) -> None:
        self.name = name
        self.description = description
        self.price = price
        self.quantity = quantity
