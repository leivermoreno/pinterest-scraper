import logging
from functools import wraps
from typing import Callable

from playwright.sync_api import Error as PlaywrightError
from settings import RETRY_TIMES
from tenacity import after_log, retry, retry_if_exception_type, stop_after_attempt

logger = logging.getLogger(__name__)


def default_retry(func: Callable) -> Callable:
    @wraps(func)
    @retry(
        retry=retry_if_exception_type(PlaywrightError),
        stop=stop_after_attempt(RETRY_TIMES),
        after=after_log(logger, logging.WARNING),
    )
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    return wrapper
