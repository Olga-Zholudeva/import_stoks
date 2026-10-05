from exceptions import ImportIOError, InvalidRowError, TooManyInvalidRowsError
from log import log_import
from output import atomic_output
from reader import read_data
from settings import FILE_ERROR_TYPES, logger, ORIGINAL_ERROR
from validator import validate_data
import os

@log_import
def import_inventory(source, destination, *, max_errors=1):

    if max_errors < 0:
        raise ValueError(
            f"Max_errors must be greater than zero. Current value:{max_errors}"
        )

    rejected = 0
    accepted = 0
    data = source()
    with destination(temporary_file="temporary_file.txt") as am:
        for row in data:
            try:
                valid_row = validate_data(row)
                accepted += 1
                try:
                    am.write(f"{valid_row}\n")
                except FILE_ERROR_TYPES as e:
                    raise ImportError from e
            except InvalidRowError:
                rejected += 1
                if rejected <= max_errors:
                    continue
                else:
                    raise TooManyInvalidRowsError(max_errors, rejected)

    return {"read": accepted + rejected, "accepted": accepted, "rejected": rejected}


# Тест 2: Ровно допустимое число ошибок и превышение на одну.
try:
    import_inventory(lambda: read_data("product_stock.csv"), atomic_output, max_errors=1)
except TooManyInvalidRowsError as e:
    assert str(e) == "Max error count: 1.Current error count: 2"
else:
    raise AssertionError("TooManyInvalidRowsError не был вызван")


# Тест 3:  Остановка на первой ошибке при нулевом лимите.
try:
    import_inventory(lambda: read_data("product_stock.csv"), atomic_output, max_errors=0)
except TooManyInvalidRowsError as e:
    assert str(e) == "Max error count: 0.Current error count: 1"
else:
    raise AssertionError("TooManyInvalidRowsError не был вызван")


# Test 4: Отсутствие дальнейшего чтения после превышения лимита.
def test_no_read():
    yield_count = 0
    def failing_sourse():
        nonlocal yield_count
        while True:
            yield_count += 1
            yield {yield_count: ["", ""]}
    
    try:
        import_inventory(failing_sourse, atomic_output, max_errors=0)
    except TooManyInvalidRowsError as e:
        assert str(e) == "Max error count: 0.Current error count: 1"
        assert yield_count == 1
    else:
        raise AssertionError("TooManyInvalidRowsError не был вызван")
test_no_read()


# Тест 5: Сохранность старого файла и удаление временного при сбое после частичной записи.
try:
    import_inventory(lambda: read_data("product_stock.csv"), atomic_output, max_errors=3)
    import_inventory(lambda: read_data("product_stock.csv"), atomic_output, max_errors=1)
except TooManyInvalidRowsError as e:
    with open("result.txt", "r") as file:
        assert file.readlines() == ["{'A-100': 12}\n", "{'B-200': 0}\n", "{'E-500': 3}\n"]
    assert not os.path.exists("temporary_file.txt")


# Тест 6: Связь ImportIOError.__cause__ с исходной файловой ошибкой.
try:
    import_inventory(lambda: read_data("product_stoc.csv"), atomic_output, max_errors=3)
except ImportIOError as e:
    assert e.__cause__ is not None
    assert isinstance(e.__cause__, FileNotFoundError)
else:
    raise AssertionError("Отсутвует обработка исключения типа ImportIOError")


# Тест 7: Неожиданное исключение выходит наружу;
# декоратор не подменяет его и не пишет об успехе.

try:
    import_inventory(lambda: read_data("test_7.csv"), atomic_output, max_errors=1)
except Exception as curr_error:
    assert curr_error is ORIGINAL_ERROR





