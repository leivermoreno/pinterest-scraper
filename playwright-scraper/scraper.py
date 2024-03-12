import logging
import urllib.parse
from typing import Iterable, Iterator

from browser import BrowserManager
from db import Url as UrlModel
from db import setup_db
from settings import OUTPUT_DIR
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from views.board_grid import BoardGridView


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

    def join_urls(self, urls: Iterable) -> list[str]:
        return [urllib.parse.urljoin(self.base_url, url) for url in urls]

    def scrape_board_urls(self) -> list[str]:
        browser = self.browser_manager.get_browser(self.initial_url)
        with browser as page:
            self.logger.info(f"Scraping board urls from {self.initial_url}")
            view = BoardGridView(page=page)
            view.start_view()

        urls = view.get_board_urls()
        processed_urls = self.join_urls(urls)
        processed_urls = UrlModel.exclude_duplicates(self.session, processed_urls)
        self.logger.info(f"Found {len(processed_urls)} board urls")

        return processed_urls

    def run(self) -> None:
        try:
            self.setup()
            board_urls = self.scrape_board_urls()
        finally:
            if self.session is not None:
                self.session.close()
