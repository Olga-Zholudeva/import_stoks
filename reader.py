import csv
from collections.abc import Iterator
from contextlib import contextmanager

from exceptions import ImportIOError
from settings import FILE_ERROR_TYPES


def read_data(file) -> Iterator[dict[int, list[str]]]:
    row_number = 0
    try:
        data = csv.reader(file)
        next(data)
        for row in data:
            row_number += 1
            yield {row_number: row}
    except FILE_ERROR_TYPES as error:
        raise ImportIOError from error
