import csv
import logging

logging.basicConfig(
    level=logging.INFO,
    filename="app.log",
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

FILE_ERROR_TYPES = (OSError, csv.Error, UnicodeDecodeError)
ORIGINAL_ERROR = Exception("Error")
