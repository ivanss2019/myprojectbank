"""Тесты для модуля src.decorators."""

from pathlib import Path
from typing import Any

import pytest

from src.decorators import log


@log()
def add(a: int, b: int) -> int:
    """Складывает два числа — используется как подопытная функция."""
    return a + b


@log()
def fail(*args: Any, **kwargs: Any) -> None:
    """Всегда падает с ошибкой — используется как подопытная функция."""
    raise ValueError("boom")


class TestLogToConsole:
    """Тесты вывода лога в консоль (без filename)."""

    def test_successful_call_returns_correct_result(self) -> None:
        """Декорированная функция по-прежнему возвращает свой результат."""
        assert add(2, 3) == 5

    def test_successful_call_logs_start_and_result(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """При успешном вызове в консоль пишутся сообщения о начале
        выполнения и о результате с именем функции."""
        add(2, 3)
        captured = capsys.readouterr()
        assert "add started" in captured.out
        assert "add ok" in captured.out
        assert "5" in captured.out

    def test_failed_call_reraises_original_exception(self) -> None:
        """Исключение, возникшее внутри функции, пробрасывается дальше
        без изменений."""
        with pytest.raises(ValueError, match="boom"):
            fail(1, key="value")

    def test_failed_call_logs_error_and_inputs(
        self, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """При ошибке в консоль пишется имя функции, тип ошибки и
        входные параметры вызова."""
        with pytest.raises(ValueError):
            fail(1, key="value")
        captured = capsys.readouterr()
        assert "fail error" in captured.out
        assert "ValueError" in captured.out
        assert "1" in captured.out
        assert "key" in captured.out and "value" in captured.out

    @pytest.mark.parametrize(
        "a, b, expected",
        [(1, 1, 2), (0, 0, 0), (-5, 5, 0), (100, 200, 300)],
    )
    def test_various_inputs_are_logged_correctly(
        self, capsys: pytest.CaptureFixture[str], a: int, b: int, expected: int
    ) -> None:
        """Для разных входных данных декоратор логирует правильный
        результат каждой отдельной операции."""
        result = add(a, b)
        captured = capsys.readouterr()
        assert result == expected
        assert str(expected) in captured.out


class TestLogToFile:
    """Тесты записи лога в файл (с filename)."""

    def test_successful_call_writes_to_file(self, tmp_path: Path) -> None:
        """При успешном вызове с filename сообщения пишутся в файл,
        а не в консоль."""
        log_file = tmp_path / "success.log"

        @log(filename=str(log_file))
        def multiply(a: int, b: int) -> int:
            return a * b

        result = multiply(3, 4)
        content = log_file.read_text(encoding="utf-8")

        assert result == 12
        assert "multiply started" in content
        assert "multiply ok" in content
        assert "12" in content

    def test_failed_call_writes_error_to_file(self, tmp_path: Path) -> None:
        """При ошибке с заданным filename сообщение об ошибке и входные
        параметры пишутся в файл."""
        log_file = tmp_path / "errors.log"

        @log(filename=str(log_file))
        def divide(a: int, b: int) -> float:
            return a / b

        with pytest.raises(ZeroDivisionError):
            divide(10, 0)

        content = log_file.read_text(encoding="utf-8")
        assert "divide error" in content
        assert "ZeroDivisionError" in content
        assert "10" in content

    def test_multiple_calls_append_to_the_same_file(self, tmp_path: Path) -> None:
        """При нескольких вызовах подряд записи в файл добавляются
        (append), а не перезаписывают предыдущий лог."""
        log_file = tmp_path / "append.log"

        @log(filename=str(log_file))
        def increment(value: int) -> int:
            return value + 1

        increment(1)
        increment(2)
        content = log_file.read_text(encoding="utf-8")

        assert content.count("increment started") == 2

    def test_console_stays_empty_when_filename_is_set(
        self, capsys: pytest.CaptureFixture[str], tmp_path: Path
    ) -> None:
        """Если задан filename, в консоль ничего не выводится."""
        log_file = tmp_path / "quiet.log"

        @log(filename=str(log_file))
        def noop() -> None:
            return None

        noop()
        captured = capsys.readouterr()
        assert captured.out == ""


class TestLogPreservesFunctionMetadata:
    """Тесты, что декоратор не портит метаданные оборачиваемой функции."""

    def test_wraps_preserves_name_and_docstring(self) -> None:
        """functools.wraps сохраняет __name__ и __doc__ исходной функции."""
        assert add.__name__ == "add"
        assert add.__doc__ is not None
        assert "Складывает" in add.__doc__
