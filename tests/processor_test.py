import logging
import os
from collections.abc import Iterator
from functools import partial
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from exceptions import ImportIOError, TooManyInvalidRowsError
from output import atomic_output
from processor import import_inventory
from reader import read_data
from settings import INPUT_FILE, RESULT_FILE

TEST_DATA = [
    "sku,quantity",
    "A-100,12",
    "B-200,0",
    "C-300,abc",
    "D-400,-5",
    ",8",
    "E-500,3",
]


class UnexpectedError(Exception):
    pass


ORIGINAL_ERROR = UnexpectedError("unexpected error")


def _write_csv(path: Path, rows: list[str]):
    """Записываем тестовые данные во временный csv"""
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def test_successful_import(tmp_path: Path):
    """Успешный импорт, включая количество 0."""
    csv = tmp_path / INPUT_FILE
    _write_csv(csv, TEST_DATA)
    result = tmp_path / RESULT_FILE

    import_inventory(
        csv,
        lambda result_path: atomic_output(str(result)),
        max_errors=3,
    )

    assert result.read_text(encoding="utf-8").splitlines(keepends=True) == [
        "{'A-100': 12}\n",
        "{'B-200': 0}\n",
        "{'E-500': 3}\n",
    ]


def test_allowable_number_errors(tmp_path: Path):
    """Ровно допустимое число ошибок и превышение на одну."""
    csv = tmp_path / INPUT_FILE
    _write_csv(csv, TEST_DATA)
    result = tmp_path / RESULT_FILE

    with pytest.raises(TooManyInvalidRowsError) as exc:
        import_inventory(
            csv,
            lambda result_path: atomic_output(str(result)),
            max_errors=1,
        )
    assert str(exc.value) == "Max error count: 1.Current error count: 2"


def test_stop_with_zero_limit(tmp_path: Path):
    """Остановка на первой ошибке при нулевом лимите."""
    csv = tmp_path / INPUT_FILE
    _write_csv(csv, TEST_DATA)
    result = tmp_path / RESULT_FILE

    with pytest.raises(TooManyInvalidRowsError) as exc:
        import_inventory(
            csv,
            lambda result_path: atomic_output(str(result)),
            max_errors=0,
        )
    assert str(exc.value) == "Max error count: 0.Current error count: 1"


def test_no_read(tmp_path: Path, monkeypatch):
    """Отсутствие дальнейшего чтения после превышения лимита."""

    csv = tmp_path / INPUT_FILE
    _write_csv(csv, TEST_DATA)
    result = tmp_path / RESULT_FILE

    read_count = 0

    def counting_reader(file) -> Iterator:
        nonlocal read_count
        next(file)
        for row in file:
            read_count += 1
            yield {read_count: ["", ""]}

    import processor

    monkeypatch.setattr(processor, "read_data", counting_reader)

    with pytest.raises(TooManyInvalidRowsError) as exc:
        import_inventory(
            csv, lambda result_path: atomic_output(str(result)), max_errors=0
        )
    assert str(exc.value) == "Max error count: 0.Current error count: 1"
    assert read_count == 1


def test_saving_old_file_and_deleting_temporary(tmp_path: Path):
    """Сохранность старого файла.
    Удаление временного при сбое после частичной записи.
    """

    csv = tmp_path / INPUT_FILE
    _write_csv(csv, TEST_DATA)
    result = tmp_path / RESULT_FILE
    temporary = tmp_path / f".{RESULT_FILE}.tmp"

    import_inventory(
        csv,
        lambda result_path: atomic_output(str(result)),
        max_errors=3,
    )
    assert result.exists()

    with pytest.raises(TooManyInvalidRowsError):
        import_inventory(
            csv,
            lambda result_path: atomic_output(str(result)),
            max_errors=1,
        )

    assert result.read_text(encoding="utf-8").splitlines(keepends=True) == [
        "{'A-100': 12}\n",
        "{'B-200': 0}\n",
        "{'E-500': 3}\n",
    ]
    assert not temporary.exists()


def test_Connection_ImportIOError_vs_initial_error(tmp_path: Path):
    """Связь ImportIOError.__cause__ с исходной файловой ошибкой."""

    result = tmp_path / RESULT_FILE

    with pytest.raises(ImportIOError) as exc:
        import_inventory(
            "product_stoc.csv",
            lambda result_path: atomic_output(str(result)),
            max_errors=3,
        )
    assert str(exc.value.__cause__) is not None
    assert isinstance(exc.value.__cause__, FileNotFoundError)


def test_unexpected_exception_revealed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
):
    """Неожиданное исключение выходит наружу.
    Декоратор не подменяет его и не пишет об успехе.
    """
    csv = tmp_path / INPUT_FILE
    _write_csv(csv, TEST_DATA)
    result = tmp_path / RESULT_FILE

    import processor

    real_validate = processor.validate_data

    def failing_validate(row: dict[int, list[str]]) -> dict[str, int]:
        for row_number, row_content in row.items():
            if row_content[0] == "B-200":
                raise ORIGINAL_ERROR
        return real_validate(row)

    monkeypatch.setattr(processor, "validate_data", failing_validate)

    with caplog.at_level(logging.ERROR):
        with pytest.raises(UnexpectedError) as exc:
            import_inventory(
                csv,
                lambda result_path: atomic_output(str(result)),
                max_errors=1,
            )
    assert exc.value is ORIGINAL_ERROR
    assert any(record.exc_info is not None for record in caplog.records)
    assert "success" not in caplog.text.lower()
    assert not result.exists()


def test_unlimit_error(tmp_path: Path):
    """Тест без явно переданного лимита, с дефолтным max_errors=2"""
    csv = tmp_path / INPUT_FILE
    _write_csv(csv, TEST_DATA)
    result = tmp_path / RESULT_FILE

    with pytest.raises(TooManyInvalidRowsError) as exc:
        import_inventory(
            csv,
            lambda result_path: atomic_output(str(result)),
        )
    assert str(exc.value) == "Max error count: 2.Current error count: 3"


def test_failure_to_write_temporary_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
):
    """Сбой записи во временный файл."""

    csv = tmp_path / INPUT_FILE
    _write_csv(csv, TEST_DATA)

    def fake_read_data(file):
        yield {1: ["A-100", "12"]}
        yield {2: ["B-200", "5"]}

    import processor

    monkeypatch.setattr(processor, "read_data", fake_read_data)

    mock_am = MagicMock()
    mock_am.__enter__.return_value = mock_am
    mock_am.write.side_effect = OSError("Сбой записи: нет места на диске")

    def fake_destination(result_path):
        return mock_am

    monkeypatch.setattr(processor, "atomic_output", fake_destination)

    with pytest.raises(ImportIOError) as exc:
        processor.import_inventory(csv, fake_destination, max_errors=2)

    assert isinstance(exc.value.__cause__, OSError)
    assert str(exc.value.__cause__) == "Сбой записи: нет места на диске"
