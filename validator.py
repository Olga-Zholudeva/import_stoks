from typing import Any

from exceptions import InvalidRowError
from settings import logger


def check_sku(row_number: int, sku: str) -> str:
    sku = sku.strip()
    if sku:
        return sku
    else:
        logger.error(f"Error in row_number {row_number}: sku is empty")
        raise InvalidRowError()


def check_quantity(
    row_number: int,
    quantity: Any,
) -> int:
    try:
        qty = int(quantity)
        if qty < 0:
            logger.error(f"Error in row_number {row_number}: quantity < 0")
            raise InvalidRowError(quantity=qty)
        return qty
    except ValueError:
        logger.error(f"Error in row_number {row_number}: quantity is not integer")
        raise InvalidRowError(quantity=quantity)


def validate_data(row: dict[int, list[str]]) -> dict[str, int]:
    for row_number, row_content in row.items():
        sku = check_sku(row_number, row_content[0])
        quantity = check_quantity(row_number, row_content[1])
        return {sku: quantity}
    return {}


