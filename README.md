# Учебный проект: банковские операции и e-commerce

Бэкенд для виджета личного кабинета клиента, показывающего несколько
последних успешных банковских операций.

## Структура проекта

```
.
├── main.py            # проверочный пример e-commerce из задания 14.1
├── bank_main.py       # консольное меню банковских операций
├── pyproject.toml     # конфигурация Poetry, black, isort, mypy
├── .flake8            # конфигурация flake8
├── .env.template       # шаблон переменных окружения (скопировать в .env)
├── data/
│   ├── products.json   # каталог товаров из задания 14.1
│   ├── operations.json  # тестовый набор данных о транзакциях
│   ├── transactions.csv
│   └── transactions_excel.xlsx
├── logs/                # логи модулей (создаётся автоматически, .log в .gitignore)
├── src/
│   ├── __init__.py
│   ├── product.py       # класс Product
│   ├── category.py      # класс Category и общие счётчики
│   ├── catalog.py       # загрузка JSON в объекты
│   ├── masks.py         # маскировка номеров карт и счетов
│   ├── widget.py        # форматирование данных для отображения в виджете
│   ├── processing.py    # фильтрация и сортировка списка операций
│   ├── generators.py    # генераторы для обработки транзакций и номеров карт
│   ├── decorators.py    # декоратор log для логирования вызовов функций
│   ├── utils.py          # чтение транзакций из JSON
│   ├── file_operations.py # чтение транзакций из CSV и XLSX
│   └── external_api.py   # конвертация суммы транзакции в рубли
└── tests/
    ├── __init__.py
    ├── conftest.py
    ├── test_masks.py
    ├── test_widget.py
    ├── test_processing.py
    ├── test_search.py
    ├── test_ecommerce.py
    ├── test_bank_main.py
    ├── test_generators.py
    ├── test_decorators.py
    ├── test_utils.py
    ├── test_tabular_transactions.py
    └── test_external_api.py
```

## Установка

```bash
poetry install --with lint,test
```

Для работы модуля `src.external_api` (конвертация валют) нужен ключ
Exchange Rates Data API (apilayer.com):

```bash
cp .env.template .env
# затем укажите свой ключ в .env: API_KEY=...
```

## Проверка качества кода

```bash
# статический анализ стиля
poetry run flake8 main.py bank_main.py src tests

# проверка форматирования
poetry run black --check main.py bank_main.py src tests
poetry run isort --check-only main.py bank_main.py src tests

# проверка типов
poetry run mypy

# тесты
poetry run pytest

# тесты с отчетом о покрытии кода
poetry run pytest --cov --cov-report=term-missing

# тесты с HTML-отчетом о покрытии кода (открыть htmlcov/index.html в браузере)
poetry run pytest --cov --cov-report=html
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

## Модуль `src.generators`

Генераторы для поэлементной обработки списка транзакций и генерации
номеров карт, без загрузки всего результата в память сразу.

### `filter_by_currency(transactions, currency)`

Генератор, поочередно выдающий транзакции, у которых код валюты
(`operationAmount.currency.code`) совпадает с переданным.

```python
>>> from src.generators import filter_by_currency
>>> transactions = [
...     {"id": 1, "operationAmount": {"currency": {"code": "USD"}}},
...     {"id": 2, "operationAmount": {"currency": {"code": "RUB"}}},
... ]
>>> usd_transactions = filter_by_currency(transactions, "USD")
>>> next(usd_transactions)
{'id': 1, 'operationAmount': {'currency': {'code': 'USD'}}}
```

### `transaction_descriptions(transactions)`

Генератор, поочередно выдающий описание (`description`) каждой
транзакции.

```python
>>> from src.generators import transaction_descriptions
>>> transactions = [{"description": "Перевод организации"}]
>>> descriptions = transaction_descriptions(transactions)
>>> next(descriptions)
'Перевод организации'
```

### `card_number_generator(start, end)`

Генератор номеров банковских карт в формате `XXXX XXXX XXXX XXXX` для
диапазона от `start` до `end` включительно. Допустимый диапазон — от 1
(`0000 0000 0000 0001`) до 9999999999999999 (`9999 9999 9999 9999`).

```python
>>> from src.generators import card_number_generator
>>> numbers = card_number_generator(1, 2)
>>> next(numbers)
'0000 0000 0000 0001'
>>> next(numbers)
'0000 0000 0000 0002'
```

## Модуль `src.decorators`

### `log(filename=None)`

Декоратор, логирующий начало, конец и результат выполнения функции.
При успехе записывает имя функции и результат; при исключении — имя
функции, тип ошибки и входные параметры вызова, после чего пробрасывает
исключение дальше без изменений. Если `filename` не задан, лог выводится
в консоль; если задан — дописывается (append) в указанный файл.

```python
>>> from src.decorators import log
>>>
>>> @log()
... def add(a: int, b: int) -> int:
...     return a + b
>>> add(2, 3)
add started
add ok. Result: 5
5

>>> @log(filename="mylog.txt")
... def divide(a: int, b: int) -> float:
...     return a / b
>>> divide(10, 0)  # сообщение об ошибке и входных параметрах допишется в mylog.txt
Traceback (most recent call last):
    ...
ZeroDivisionError: division by zero
```

## Модуль `src.utils`

### `read_transactions_json(file_path)`

Читает список финансовых транзакций из JSON-файла (например,
`data/operations.json`). Если файл не найден, пуст или его содержимое —
не список, возвращает пустой список, а не исключение.

```python
>>> from src.utils import read_transactions_json
>>> read_transactions_json("data/operations.json")
[{'id': 441945886, 'state': 'EXECUTED', ...}, ...]
>>> read_transactions_json("no_such_file.json")
[]
```

## Модуль `src.external_api`

### `convert_to_rub(transaction)`

Возвращает сумму транзакции (`operationAmount.amount`) в рублях, тип —
`float`. Если валюта операции — рубли, сумма только приводится к
`float`. Если валюта — `USD` или `EUR`, для конвертации по текущему
курсу выполняется запрос к [Exchange Rates Data
API](https://apilayer.com/marketplace/exchangerates_data-api)
(apilayer.com); ключ доступа берётся из переменной окружения
`API_KEY` (см. `.env.template`).

```python
>>> from src.external_api import convert_to_rub
>>> transaction = {
...     "operationAmount": {
...         "amount": "31957.58",
...         "currency": {"name": "руб.", "code": "RUB"},
...     }
... }
>>> convert_to_rub(transaction)
31957.58
```

## Логирование

Модули `src.masks` и `src.utils` пишут логи в файлы `logs/masks.log` и
`logs/utils.log` соответственно (директория `logs/` создаётся
автоматически при импорте модуля). Формат записи:
`<время> - <модуль> - <уровень> - <сообщение>`. Файл лога
перезаписывается при каждом запуске приложения (`FileHandler` открыт
в режиме `"w"`).

```
2024-03-11 10:15:03,214 - masks - INFO - Номер карты успешно замаскирован
2024-03-11 10:15:03,215 - utils - WARNING - Файл data/typo.json не найден
```


## Чтение CSV и XLSX

Функции `read_transactions_csv(file_path)` и
`read_transactions_excel(file_path)` находятся в отдельном модуле `src.file_operations` и используют
`pandas`. Для XLSX установлен движок `openpyxl`; читается первый лист.
CSV читается в UTF-8 (в том числе с BOM), разделитель — `;`, как в файле задания.

```python
from src.file_operations import read_transactions_csv, read_transactions_excel

csv_transactions = read_transactions_csv("data/transactions.csv")
excel_transactions = read_transactions_excel("data/transactions_excel.xlsx")
```

Результат — список словарей с ключами из заголовков таблицы:
`id`, `state`, `date`, `amount`, `currency_name`, `currency_code`,
`from`, `to`, `description`. Пропуски заменяются на `None`, номера отправителя
и получателя читаются как строки, чтобы сохранить ведущие нули.
Отсутствующие, пустые и нечитаемые файлы возвращают `[]` с записью ошибки
в стандартный журнал `src.file_operations`; ошибки доступа передаются вызывающему коду.
Таблица только с заголовками и пустой лист XLSX также дают `[]`.

Данные сохраняют плоскую структуру исходных таблиц. Для передачи в
`filter_by_currency` или `convert_to_rub`, ожидающие JSON-структуру
`operationAmount`, используйте `normalize_transactions` из
`src.file_operations`. Консольное меню выполняет это преобразование автоматически.

Эталонные файлы сохранены без изменений из репозитория
[skypro-008/transactions](https://github.com/skypro-008/transactions):
[CSV](https://github.com/skypro-008/transactions/blob/main/transactions.csv) и
[XLSX](https://github.com/skypro-008/transactions/blob/main/transactions_excel.xlsx).
Оба файла используются в интеграционных тестах; тестам не нужен доступ к сети.

Зависимости зафиксированы в `poetry.lock`. Версии pandas, NumPy и mypy ограничены
для сохранения заявленной проектом совместимости с Python 3.9.
`pandas-stubs` обеспечивает проверку типов вызовов pandas.


## Поиск и подсчёт категорий

В модуле `src.processing` добавлены две функции:

- `process_bank_search(data, search)` возвращает операции, содержащие строку
  поиска в `description`. Используется `re` с `re.IGNORECASE` и `re.escape`:
  поиск не зависит от регистра, а спецсимволы (`.`, `+`, `[`) считаются
  обычным текстом. Пустой запрос выбирает все строковые описания.
  Операции без строкового описания пропускаются; исходный порядок сохраняется.
- `process_bank_operations(data, categories)` возвращает словарь количества
  операций по запрошенным категориям. Категория — точное значение
  `description` с учётом регистра. Для отсутствующих категорий возвращается 0,
  дубли категорий не увеличивают счётчики. Используется `collections.Counter`.

```python
from src.processing import process_bank_operations, process_bank_search

operations = [
    {"description": "Перевод организации"},
    {"description": "Открытие вклада"},
    {"description": "Перевод организации"},
]
assert len(process_bank_search(operations, "ПЕРЕВОД")) == 2
assert process_bank_operations(operations, ["Перевод организации", "Оплата"]) == {
    "Перевод организации": 2,
    "Оплата": 0,
}
```

## Консольная программа

Запуск из корня проекта:

```bash
poetry run python bank_main.py
```

Функция `main()` в модуле `bank_main` связывает чтение, фильтрацию, сортировку
и форматирование операций:

1. Выберите JSON (1), CSV (2) или XLSX (3). Программа читает соответствующий
   файл из `data/`; пути вычисляются относительно `bank_main.py`.
2. Введите статус EXECUTED, CANCELED или PENDING в любом регистре.
   При неверном статусе программа сообщает об ошибке и повторяет вопрос.
3. Выберите, нужна ли сортировка по дате; если да — по возрастанию или
   по убыванию.
4. Выберите, оставлять ли только рублёвые операции.
5. Выберите, нужен ли поиск по описанию, и введите искомый текст.

Ответы «Да/Нет» и направление сортировки не зависят от регистра.
Неверный пункт меню или ответ повторно запрашивается. После фильтров выводится
количество операций и их список: дата ДД.ММ.ГГГГ, описание, замаскированные
реквизиты, сумма и валюта. Для открытия вклада без отправителя выводится
только счёт получателя. RUB обозначается «руб.», другие валюты — кодом валюты.
Конвертация валют и сетевые запросы при просмотре не выполняются.

Если совпадений нет, выводится:

```text
Не найдено ни одной транзакции, подходящей под ваши условия фильтрации
```

`normalize_transactions` из `src.file_operations` создаёт общий формат
`operationAmount` для табличных данных, нормализует статус и пропускает пустые
записи. Исходные данные и функции чтения не изменяются. Даты с суффиксом `Z`
поддерживаются при сортировке и форматировании, включая Python 3.9.
`format_transaction` из `src.widget` отвечает за вывод одной операции.

Тесты покрывают поиск, категории, все источники, статусы, оба направления
сортировки, сочетание фильтров, повторный ввод, маскировку и пустую выборку.
Полный сценарий также проверяется на реальных JSON/CSV/XLSX-файлах задания.
HTML-отчёт покрытия включает `src`, `main.py` и `bank_main.py`.


## E-commerce — задания 14.1 и 14.2

Запуск примера [14.2_main.py](https://drive.google.com/file/d/12eWJpouwNvyJ1yaUaOIXBCnkJyPE3q2R/view):

```bash
poetry run python main.py
```

В `main.py` сохранён сценарий предоставленного файла; добавлены импорты классов
и форматирование. При снижении цены введите `y` для согласия или `n` для отказа.
Любой ответ, кроме точного `y`, отменяет снижение.

`Product(name, description, price, quantity)` хранит название, описание, цену
и количество. Цена хранится в приватном `__price` и доступна через `price`.
Сеттер не принимает значения <= 0: выводит «Цена не должна быть нулевая или
отрицательная» и сохраняет прежнюю цену. Повышение и повторная установка той же
цены не требуют подтверждения. Конструктор сохраняет исходную цену напрямую;
проверка изменения цены реализована в сеттере согласно заданию.

`Category(name, description, products)` хранит собственную копию списка товаров
в приватном `__products`. Добавление выполняется методом `add_product(product)`;
он увеличивает общий счётчик `product_count` на одну позицию, независимо от
остатка товара. Общий `category_count` увеличивается при создании категории.
Объекты товаров не копируются, поэтому изменение цены товара видно в категории.

Геттер `category.products` возвращает **строку**, а не список объектов:

```text
Название продукта, 80 руб. Остаток: 15 шт.
```

Каждый товар занимает отдельную строку, включая завершающий перевод строки.
Пустая категория возвращает пустую строку. Представление цены сохраняет формат
числа: для `80.0` выводится `80.0`, для `80` — `80`. Сеттера `products` нет.

### Создание товара из словаря и дубликаты

```python
from src.product import Product

existing = Product("Телефон", "Описание", 100.0, 2)
product = Product.new_product(
    {"name": "Телефон", "description": "Новое описание", "price": 120.0, "quantity": 3},
    [existing],
)
assert product.price == 120.0
assert product.quantity == 5
```

`new_product(data, products=None)` — класс-метод, создающий объект через `cls`.
Совпадения ищутся по полному имени без учёта регистра и крайних пробелов.
Количество всех совпадений суммируется, выбирается максимальная цена.
Исходные словарь, список и товары не изменяются: метод возвращает новый объект,
а не добавляет его в категорию автоматически. Описание берётся из нового словаря.
Не следует добавлять объединённый результат рядом со старой позицией, если цель —
заменить её: это привело бы к двойному учёту остатков.

### Загрузка JSON

```python
from src.catalog import load_categories

categories = load_categories("data/products.json")
print(categories[0].name)
print(categories[0].products)
```

Функция читает UTF-8 JSON и создаёт объекты категорий с вложенными товарами.
Повторная загрузка увеличивает общие счётчики. Исходный каталог содержит
2 категории и 4 товарные позиции.

### Проверки

Тесты прошлого ДЗ сохранены и адаптированы там, где задание намеренно меняет
публичный интерфейс: `products` теперь строка, а `price` — свойство.
Добавлены проверки приватности, копирования исходного списка, добавления товара,
счётчиков, создания из словаря, объединения дубликатов, отказа от неверной цены
и подтверждения/отмены снижения. Пример из задания проверяется с ответами `y` и `n`.

```bash
poetry run black --check src tests main.py bank_main.py
poetry run isort --check-only src tests main.py bank_main.py
poetry run flake8 src tests main.py bank_main.py
poetry run mypy
poetry run pytest --cov --cov-report=term-missing
```


### Сверка с критериями 14.2

- Список `Category.__products` приватный; `add_product(self, product)` использует
  `append`, увеличивает `Category.product_count` на 1 и возвращает `None`.
- `@property products` возвращает все позиции строго в формате
  `Название, X руб. Остаток: X шт.\n`.
- `@classmethod new_product(cls, data)` создаёт экземпляр через `cls`.
  Необязательный `products=None` добавлен для дополнительного задания о дубликатах;
  основной вызов с одним словарём полностью поддерживается.
- `Product.__price` приватный, доступен через `@property price` и `@price.setter`.
  Неположительная новая цена отклоняется с точным сообщением из условия.
  Сеттер не возвращает значения. Подтверждение снижения — дополнительное задание.
- Полный набор: 193 теста, покрытие функционального кода — 100% (выше 75%).
  Актуальный HTML-отчёт расположен в [htmlcov/index.html](htmlcov/index.html)
  и подготовлен для включения в PR вместе с новыми страницами классов.

Обновление отчёта с проверкой порога:

```bash
poetry run pytest --cov --cov-report=term-missing --cov-report=html:htmlcov --cov-fail-under=76
```
