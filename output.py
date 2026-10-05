import os
from contextlib import contextmanager

from exceptions import ImportIOError
from settings import FILE_ERROR_TYPES


@contextmanager
def atomic_output(temporary_file):
    file = open(temporary_file, "a")
    try:
        yield file
        file.close()
        os.replace(temporary_file, "result.txt")
    except FILE_ERROR_TYPES as e:
        file.close()
        if os.path.exists(temporary_file):
            os.remove(temporary_file)
        raise ImportIOError from e
    except Exception:
        file.close()
        if os.path.exists(temporary_file):
            os.remove(temporary_file)
        raise
