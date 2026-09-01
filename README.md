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
│   ├── masks.py        # маскировка номеров карт и счетов
│   ├── widget.py        # форматирование данных для отображения в виджете
│   └── processing.py    # фильтрация и сортировка списка операций
└── tests/
    ├── __init__.py
    ├── test_masks.py
    ├── test_widget.py
    └── test_processing.py
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

## Модуль `src.processing`

Функции для фильтрации и сортировки списка операций. Операция — это
словарь с ключами `id`, `state` и `date` (дата в формате ISO 8601).

### `filter_by_state(data, state="EXECUTED")`

Возвращает новый список словарей, содержащий только операции с указанным
статусом (по умолчанию `"EXECUTED"`), сохраняя исходный порядок.

```python
>>> from src.processing import filter_by_state
>>> operations = [
...     {"id": 41428829, "state": "EXECUTED", "date": "2019-07-03T18:35:29.512364"},
...     {"id": 594226727, "state": "CANCELED", "date": "2018-09-12T21:27:25.241689"},
... ]
>>> filter_by_state(operations, "CANCELED")
[{'id': 594226727, 'state': 'CANCELED', 'date': '2018-09-12T21:27:25.241689'}]
```

### `sort_by_date(data, descending=True)`

Возвращает новый список словарей, отсортированный по дате. По умолчанию
сортировка идёт от самой новой операции к самой старой; чтобы получить
обратный порядок, передайте `descending=False`.

```python
>>> from src.processing import sort_by_date
>>> operations = [
...     {"id": 1, "date": "2018-06-30T02:08:58"},
...     {"id": 2, "date": "2019-07-03T18:35:29"},
... ]
>>> sort_by_date(operations)
[{'id': 2, 'date': '2019-07-03T18:35:29'}, {'id': 1, 'date': '2018-06-30T02:08:58'}]
```
