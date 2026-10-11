"""Инициализация сущностей, общие счётчики и чтение каталога."""

import json
import runpy
from pathlib import Path

import pytest

from src.catalog import load_categories
from src.category import Category
from src.product import Product


@pytest.fixture(autouse=True)
def reset_counts(monkeypatch: pytest.MonkeyPatch) -> None:
    """Изолирует счётчики и восстанавливает исходные значения после теста."""
    monkeypatch.setattr(Category, "category_count", 0)
    monkeypatch.setattr(Category, "product_count", 0)


@pytest.fixture
def product() -> Product:
    return Product("Телефон", "Серый, 256GB", 12345.5, 100)


def test_product_initialization(product: Product) -> None:
    assert (product.name, product.description, product.price, product.quantity) == (
        "Телефон",
        "Серый, 256GB",
        12345.5,
        100,
    )
    assert Category.category_count == Category.product_count == 0


def test_category_initialization(product: Product) -> None:
    category = Category("Смартфоны", "Средства связи", [product])
    assert category.name == "Смартфоны"
    assert category.description == "Средства связи"
    assert category.products == "Телефон, 12345.5 руб. Остаток: 100 шт.\n"
    assert category.category_count == category.product_count == 1


def test_shared_counts(product: Product) -> None:
    first = Category("Первая", "", [product])
    second = Category("Вторая", "", [product, Product("ТВ", "", 10.0, 50)])
    empty = Category("Пустая", "", [])
    assert first.category_count == second.category_count == empty.category_count == 3
    assert first.product_count == second.product_count == Category.product_count == 3
    assert "category_count" not in vars(first)
    assert "product_count" not in vars(first)
    assert empty.products == ""


def test_load_provided_catalog() -> None:
    path = Path(__file__).resolve().parents[1] / "data" / "products.json"
    categories = load_categories(path)
    raw = json.loads(path.read_text(encoding="utf-8"))
    assert len(categories) == Category.category_count == 2
    assert Category.product_count == 4
    for category, data in zip(categories, raw):
        assert isinstance(category, Category)
        assert category.name == data["name"]
        assert category.description == data["description"]
        expected_lines = [
            f"{item['name']}, {item['price']} руб. Остаток: {item['quantity']} шт."
            for item in data["products"]
        ]
        assert category.products.splitlines() == expected_lines
    again = load_categories(str(path))
    assert again[0] is not categories[0]
    assert Category.category_count == 4
    assert Category.product_count == 8


@pytest.mark.parametrize(
    "content, count",
    [
        ("[]", 0),
        ('[{"name": "Пустая", "description": "Нет товаров", "products": []}]', 1),
    ],
)
def test_load_empty_catalog(tmp_path: Path, content: str, count: int) -> None:
    path = tmp_path / "catalog.json"
    path.write_text(content, encoding="utf-8")
    assert len(load_categories(path)) == count
    assert Category.category_count == count
    assert Category.product_count == 0


def test_missing_file(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError):
        load_categories(tmp_path / "missing.json")


def test_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{", encoding="utf-8")
    with pytest.raises(json.JSONDecodeError):
        load_categories(path)
    assert Category.category_count == Category.product_count == 0


@pytest.mark.parametrize("answer, expected_price", [("y", 800), ("n", 180000.0)])
def test_homework_main(capsys, monkeypatch, answer, expected_price):
    monkeypatch.setattr("builtins.input", lambda prompt: answer)
    path = Path(__file__).resolve().parents[1] / "main.py"
    namespace = runpy.run_path(str(path), run_name="__main__")
    output = capsys.readouterr().out
    assert "Samsung Galaxy S23 Ultra, 180000.0 руб. Остаток: 5 шт." in output
    assert output.count("Цена не должна быть нулевая или отрицательная") == 2
    assert namespace["new_product"].price == expected_price
    assert Category.category_count == 1
    assert Category.product_count == 4


def test_category_private_list_and_copy(product):
    source = [product]
    category = Category("Товары", "", source)
    source.clear()
    assert category.products == "Телефон, 12345.5 руб. Остаток: 100 шт.\n"
    assert "products" not in vars(category)
    with pytest.raises(AttributeError):
        getattr(category, "__products")
    with pytest.raises(AttributeError):
        setattr(category, "products", [])
    assert Category.product_count == 1


def test_add_product_updates_counts(product):
    first = Category("Первая", "", [])
    second = Category("Вторая", "", [])
    first.add_product(product)
    first.add_product(Product("Кабель", "", 80, 15))
    assert first.products == (
        "Телефон, 12345.5 руб. Остаток: 100 шт.\n" "Кабель, 80 руб. Остаток: 15 шт.\n"
    )
    assert second.products == ""
    assert first.product_count == second.product_count == 2
    assert Category.category_count == 2


def test_add_wrong_type():
    category = Category("", "", [])
    with pytest.raises(TypeError):
        category.add_product("не товар")  # type: ignore[arg-type]
    assert category.products == ""
    assert Category.product_count == 0


def test_price_is_private(product):
    assert "price" not in vars(product)
    with pytest.raises(AttributeError):
        getattr(product, "__price")
    assert product.price == 12345.5


@pytest.mark.parametrize("value", [0, -1, -100.5])
def test_invalid_price_keeps_old_value(product, value, capsys, monkeypatch):
    def unexpected_prompt(prompt):
        pytest.fail("Неверная цена не должна запрашивать подтверждение")

    monkeypatch.setattr("builtins.input", unexpected_prompt)
    product.price = value
    assert product.price == 12345.5
    assert capsys.readouterr().out == "Цена не должна быть нулевая или отрицательная\n"


@pytest.mark.parametrize(
    "answer, expected",
    [("y", 100), ("n", 12345.5), ("", 12345.5), ("yes", 12345.5), ("Y", 12345.5)],
)
def test_price_decrease(product, monkeypatch, answer, expected):
    monkeypatch.setattr("builtins.input", lambda prompt: answer)
    product.price = 100
    assert product.price == expected


@pytest.mark.parametrize("value", [12345.5, 15000.75])
def test_increased_or_same_price_does_not_prompt(product, monkeypatch, value):
    def unexpected_prompt(prompt):
        pytest.fail("Повышение цены не требует подтверждения")

    monkeypatch.setattr("builtins.input", unexpected_prompt)
    product.price = value
    assert product.price == value


def test_getter_uses_updated_price(product):
    category = Category("Товары", "", [product])
    product.price = 15000
    assert category.products == "Телефон, 15000 руб. Остаток: 100 шт.\n"


def test_new_product_creates_object():
    data = {"name": "Товар", "description": "Описание", "price": 20.5, "quantity": 3}
    result = Product.new_product(data)
    assert isinstance(result, Product)
    assert (result.name, result.description, result.price, result.quantity) == (
        "Товар",
        "Описание",
        20.5,
        3,
    )
    assert Category.product_count == 0


@pytest.mark.parametrize("new_price, expected_price", [(100, 12345.5), (20000, 20000)])
def test_duplicate_product(product, new_price, expected_price):
    data = {
        "name": " телефон ",
        "description": "Новое описание",
        "price": new_price,
        "quantity": 2,
    }
    products = [Product("Другой", "", 99999, 500), product]
    result = Product.new_product(data, products)
    assert result.quantity == 102
    assert result.price == expected_price
    assert result.description == "Новое описание"
    assert result is not product
    assert product.quantity == 100 and product.price == 12345.5
    assert data["quantity"] == 2 and len(products) == 2


def test_all_duplicates_combined(product):
    data = {"name": "Телефон", "description": "", "price": 100, "quantity": 2}
    result = Product.new_product(data, [product, Product("ТЕЛЕФОН", "", 15000, 3)])
    assert result.quantity == 105
    assert result.price == 15000


def test_new_product_uses_cls():
    class SpecialProduct(Product):
        pass

    result = SpecialProduct.new_product(
        {"name": "Товар", "description": "", "price": 100, "quantity": 1}
    )
    assert isinstance(result, SpecialProduct)
