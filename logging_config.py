import logging.handlers
import os
from os import path

import colorlog

from settings import LOG_LEVEL, OUTPUT_FOlDER

logs_path = path.join(OUTPUT_FOlDER, "logs")
os.makedirs(logs_path, exist_ok=True)

log_format = "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s"
date_format = "%m-%d %H:%M:%S"


def configure():
    scraper_logger = logging.getLogger("scraper")
    scraper_logger.setLevel(LOG_LEVEL)

    stream_handler = logging.StreamHandler()
    stream_handler.setLevel("DEBUG")
    stream_handler_formatter = colorlog.ColoredFormatter(
        "%(log_color)s" + log_format, date_format
    )
    stream_handler.setFormatter(stream_handler_formatter)
    scraper_logger.addHandler(stream_handler)

    filename = path.join(logs_path, "logs.log")
    file_handler = logging.handlers.TimedRotatingFileHandler(
        filename=filename, when="midnight", interval=1, encoding="utf-8", backupCount=3
    )
    file_handler.suffix = "%m-%d"
    file_handler.setLevel("DEBUG")
    file_handler_formatter = logging.Formatter(log_format, date_format)
    file_handler.setFormatter(file_handler_formatter)
    scraper_logger.addHandler(file_handler)
