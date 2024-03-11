import logging
import urllib.parse
from typing import Iterator

from browser import BrowserManager
from db import setup_db
from settings import OUTPUT_DIR
from sqlalchemy import Engine
from sqlalchemy.orm import Session


class Scraper:
    def __init__(self, query: str) -> None:
        query = urllib.parse.quote_plus(query)
        self.base_url = "https://www.pinterest.com"
        self.initial_url = f"{self.base_url}/search/boards/?q={query}&rs=typed"
        self.output_dir = OUTPUT_DIR
        self.engine: Engine
        self.session: Session
        self.proxy_list: Iterator
        self.browser_manager: BrowserManager
        self.logger = logging.getLogger(__name__)

    def setup(self) -> None:
        self.output_dir.mkdir(exist_ok=True)
        self.engine = setup_db()
        self.session = Session(self.engine)
        self.browser_manager = BrowserManager()
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
            datefmt="%m-%d %H:%M:%S",
        )
        self.logger.info("Scraper setup complete")

    def run(self) -> None:
        try:
            self.setup()
        finally:
            if self.session is not None:
                self.session.close()
