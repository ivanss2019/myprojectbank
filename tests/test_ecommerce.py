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
    assert category.products == [product]
    assert category.products[0] is product
    assert category.category_count == category.product_count == 1


def test_shared_counts(product: Product) -> None:
    first = Category("Первая", "", [product])
    second = Category("Вторая", "", [product, Product("ТВ", "", 10.0, 50)])
    empty = Category("Пустая", "", [])
    assert first.category_count == second.category_count == empty.category_count == 3
    assert first.product_count == second.product_count == Category.product_count == 3
    assert "category_count" not in vars(first)
    assert "product_count" not in vars(first)
    assert empty.products == []


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
        assert len(category.products) == len(data["products"])
        for product, expected in zip(category.products, data["products"]):
            assert isinstance(product, Product)
            assert vars(product) == expected
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


def test_homework_main(capsys: pytest.CaptureFixture[str]) -> None:
    path = Path(__file__).resolve().parents[1] / "main.py"
    runpy.run_path(str(path), run_name="__main__")
    lines = capsys.readouterr().out.splitlines()
    assert lines[0] == "Samsung Galaxy S23 Ultra"
    assert lines[-2:] == ["2", "4"]
    assert Category.category_count == 2
    assert Category.product_count == 4
