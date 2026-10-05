import csv
from collections.abc import Iterator

from exceptions import ImportIOError
from settings import FILE_ERROR_TYPES, ORIGINAL_ERROR


def read_data(path) -> Iterator[dict[int, list[str]]]:
    row_number = 0
    try:
        with open(path, "r", encoding="utf-8") as file:
            data = csv.reader(file)
            next(data)
            for row in data:
                row_number += 1
                yield {row_number: row}
    except FILE_ERROR_TYPES as error:
        raise ImportIOError from error
    except StopIteration:
        raise ORIGINAL_ERROR


# Тест 1: Успешный импорт, включая количество 0
if __name__ == "__main__":
    test_read = read_data("product_stock.csv")
    assert next(test_read) == {1: ["A-100", "12"]}
    assert next(test_read) == {2: ["B-200", "0"]}
    assert next(test_read) == {3: ["C-300", "abc"]}
