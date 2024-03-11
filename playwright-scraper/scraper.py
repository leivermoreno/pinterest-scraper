import logging
import urllib.parse
from typing import Iterator

import settings
from sqlalchemy import Engine
from sqlalchemy.orm import Session


class Scraper:
    def __init__(self, query: str) -> None:
        query = urllib.parse.quote_plus(query)
        self.base_url = "https://www.pinterest.com"
        self.initial_url = f"{self.base_url}/search/boards/?q={query}&rs=typed"
        self.output_dir = settings.OUTPUT_DIR
        self.proxy_list_path = settings.PROXY_LIST_PATH
        self.engine: Engine
        self.session: Session
        self.proxy_list: Iterator
        self.logger = logging.getLogger(__name__)

    def run(self) -> None:
        pass
