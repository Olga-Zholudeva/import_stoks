from functools import wraps

from settings import logger


def log_import(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info("Start import")
        try:
            result = func(*args, **kwargs)
            logger.info(result)
            return result
        except Exception as e:
            logger.exception(e)
            raise

    return wrapper
