import os

from exceptions import ImportIOError, InvalidRowError, TooManyInvalidRowsError
from log import log_import
from output import atomic_output
from reader import read_data
from settings import FILE_ERROR_TYPES, logger
from validator import validate_data


@log_import
def import_inventory(source, destination, *, max_errors=2):

    if max_errors < 0:
        raise ValueError(
            f"Max_errors must be greater than zero. Current value:{max_errors}"
        )

    rejected = 0
    accepted = 0
    try:
        with open(source, "r", encoding="utf-8") as file:
            data = read_data(file)
            with destination(result_path="result.txt") as am:
                for row in data:
                    try:
                        valid_row = validate_data(row)
                        accepted += 1
                        try:
                            am.write(f"{valid_row}\n")
                        except FILE_ERROR_TYPES as e:
                            raise ImportIOError from e
                    except InvalidRowError:
                        rejected += 1
                        if rejected <= max_errors:
                            continue
                        else:
                            raise TooManyInvalidRowsError(max_errors, rejected)
        return {"read": accepted + rejected, "accepted": accepted, "rejected": rejected}
    except FILE_ERROR_TYPES as error:
        raise ImportIOError from error

