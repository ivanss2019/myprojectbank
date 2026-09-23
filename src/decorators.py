"""Декораторы общего назначения для проекта."""

import functools
from typing import Any, Callable, Optional, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


def log(filename: Optional[str] = None) -> Callable[[F], F]:
    """Декоратор, логирующий начало, конец и результат работы функции.

    Перед вызовом оборачиваемой функции записывается сообщение о начале
    выполнения. После успешного выполнения записывается имя функции и
    результат. Если во время выполнения возникло исключение, записывается
    имя функции, тип ошибки и входные параметры (позиционные и именованные
    аргументы), после чего исключение пробрасывается дальше без изменений.

    Пример:
        >>> @log()
        ... def add(a: int, b: int) -> int:
        ...     return a + b
        >>> add(1, 2)
        3

    Args:
        filename: путь к файлу, в который будут записываться логи. Если
            не задан (значение по умолчанию — None), логи выводятся
            в консоль.

    Returns:
        Декоратор, который можно применить к любой функции.
    """

    def decorator(func: F) -> F:
        """Оборачивает функцию func логированием ее вызовов."""

        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            _write_log(f"{func.__name__} started", filename)
            try:
                result = func(*args, **kwargs)
            except Exception as error:
                _write_log(
                    f"{func.__name__} error: {type(error).__name__}. "
                    f"Inputs: args={args}, kwargs={kwargs}",
                    filename,
                )
                raise
            else:
                _write_log(f"{func.__name__} ok. Result: {result!r}", filename)
                return result

        return wrapper  # type: ignore[return-value]

    return decorator


def _write_log(message: str, filename: Optional[str]) -> None:
    """Записывает сообщение лога в файл или выводит его в консоль.

    Args:
        message: текст сообщения для записи.
        filename: путь к файлу для записи. Если None — сообщение
            выводится в консоль через print.
    """
    if filename:
        with open(filename, "a", encoding="utf-8") as log_file:
            log_file.write(message + "\n")
    else:
        print(message)
