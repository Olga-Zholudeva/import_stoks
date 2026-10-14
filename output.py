import os
from collections.abc import Iterator
from contextlib import contextmanager

from exceptions import ImportIOError
from settings import FILE_ERROR_TYPES


def _cleanup(file, temporary_path, exc):
    if file is not None:
        try:
            file.close()
        except FILE_ERROR_TYPES as close_error:
            if close_error is not exc:
                exc.add_note(f"Error in close file {close_error}")
    if temporary_path is not None and os.path.exists(temporary_path):
        try:
            os.remove(temporary_path)
        except FILE_ERROR_TYPES as remove_error:
            exc.add_note(f"Error in remove file {remove_error}")


@contextmanager
def atomic_output(result_path: str) -> Iterator:
    file = None
    try:
        result_path = os.path.abspath(result_path)
        dir_path = os.path.dirname(result_path)
        temporary_path = os.path.join(dir_path, f".{os.path.basename(result_path)}.tmp")
        file = open(temporary_path, "w")
        yield file
        file.close()
        os.replace(temporary_path, result_path)
    except FILE_ERROR_TYPES as e:
        _cleanup(file, temporary_path, e)
        raise ImportIOError(f"failed to write {result_path}") from e
    except Exception as e:
        _cleanup(file, temporary_path, e)
        raise
