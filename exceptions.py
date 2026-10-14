class InvalidRowError(Exception):
    def __init__(
        self,
        quantity: int | None = None,
        row_number: int | None = None,
        data_type: str | None = None,
    ):
        self.quantity = quantity
        self.row_number = row_number
        self.data_type = data_type

    def __str__(self):
        if self.quantity is not None:
            return (
                f"Quantity must be a positive integer. Curr quantity: {self.quantity}"
            )
        if self.row_number is not None:
            if self.data_type == "sku":
                return f"Row_number: {self.row_number} does not contain sku"
            if self.data_type == "quantity":
                return (f"Row_number: {self.row_number} does not contain quantity")
        return f"Empty sku."


class TooManyInvalidRowsError(Exception):
    def __init__(self, max_errors: int, curr_error_count: int):
        self.max_errors = max_errors
        self.curr_error_count = curr_error_count

    def __str__(self):
        return f"Max error count: {self.max_errors}.Current error count: {self.curr_error_count}"


class ImportIOError(Exception):
    pass
