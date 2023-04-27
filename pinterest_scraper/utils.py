import logging
import time
from functools import wraps

logger = logging.getLogger(f"scraper.{__name__}")


def time_perf(log_str: str):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            start = time.perf_counter()
            result = f(*args, **kwargs)
            end = time.perf_counter()
            elapsed_min = (end - start) / 60
            logger.info(f"Took {elapsed_min:.2f} minutes to {log_str}.")

            return result

        return wrapper

    return decorator
