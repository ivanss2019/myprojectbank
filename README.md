# Widget — виджет последних банковских операций

Бэкенд для виджета личного кабинета клиента, показывающего несколько
последних успешных банковских операций.

## Структура проекта

```
.
├── pyproject.toml     # конфигурация Poetry, black, isort, mypy
├── .flake8            # конфигурация flake8
├── src/
│   ├── __init__.py
│   └── masks.py       # маскировка номеров карт и счетов
└── tests/
    ├── __init__.py
    └── test_masks.py
```

## Установка

```bash
poetry install --with lint,test
```

## Проверка качества кода

```bash
# статический анализ стиля
poetry run flake8 src tests

# автоформатирование
poetry run black src tests
poetry run isort src tests

# проверка типов
poetry run mypy src

# тесты
poetry run pytest
```

## Модуль `src.masks`

- `get_mask_card_number(card_number: str) -> str` — маскирует номер карты
  в формат `XXXX XX** **** XXXX` (видны первые 6 и последние 4 цифры).
- `get_mask_account(account_number: str) -> str` — маскирует номер счета
  в формат `**XXXX` (видны только последние 4 цифры).

## Модуль `src.widget`

- `mask_account_card(info: str) -> str` — принимает одну строку вида
  `"<тип> <номер>"` (например, `"Visa Platinum 7000792289606361"` или
  `"Счет 73654108430135874305"`) и возвращает ту же строку с
  замаскированным номером, переиспользуя функции из `src.masks`.
- `get_date(date_string: str) -> str` — преобразует дату из ISO-формата
  (`"2024-03-11T02:26:18.671407"`) в формат `"ДД.ММ.ГГГГ"`.
