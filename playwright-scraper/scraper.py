import logging
import urllib.parse
from typing import Iterable, Iterator

import fire
from browser import BrowserManager
from db import Url as UrlModel
from db import setup_db
from settings import OUTPUT_DIR
from sqlalchemy import Engine
from sqlalchemy.orm import Session
from utils import default_retry
from views.board_grid import BoardGridView
from views.pin_grid import PinGridView


class Scraper:
    def __init__(self, query: str, skip_process_clean: bool = False) -> None:
        self.query = urllib.parse.quote_plus(query)
        self.base_url = "https://www.pinterest.com"
        self.initial_url = f"{self.base_url}/search/boards/?q={self.query}&rs=typed"
        self.output_dir = OUTPUT_DIR
        self.skip_process_clean = skip_process_clean
        self.engine: Engine
        self.session: Session
        self.proxy_list: Iterator
        self.browser_manager: BrowserManager
        self.logger = logging.getLogger(__name__)

    def setup(self) -> None:
        self.output_dir.mkdir(exist_ok=True)
        self.engine = setup_db()
        self.session = Session(self.engine)
        self.browser_manager = BrowserManager(clean_process=not self.skip_process_clean)
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
            datefmt="%m-%d %H:%M:%S",
        )
        self.logger.info("Scraper setup complete")

    def join_urls(self, urls: Iterable) -> list[str]:
        return [urllib.parse.urljoin(self.base_url, url) for url in urls]

    @default_retry
    def scrape_board_urls(self) -> list[str]:
        browser = self.browser_manager.get_browser(self.initial_url)
        with browser as page:
            self.logger.info(f"Scraping board urls from {self.initial_url}")
            view = BoardGridView(page=page)
            view.start_view()

        urls = view.get_board_urls()
        processed_urls = self.join_urls(urls)
        processed_urls = UrlModel.exclude_duplicates(
            self.session, urls=processed_urls, is_board=True
        )
        self.logger.info(f"Found {len(processed_urls)} board urls")

        return processed_urls

    @default_retry
    def scrape_board_pins(self, url: str) -> list[str]:
        browser = self.browser_manager.get_browser(url)
        with browser as page:
            self.logger.info(f"Scraping board {url}")
            view = PinGridView(page=page)
            view.start_view()

        urls = view.get_pin_urls()
        processed_urls = self.join_urls(urls)
        processed_urls = UrlModel.exclude_duplicates(self.session, processed_urls)
        self.logger.info(f"Found {len(processed_urls)} pin urls for board {url}")

        return processed_urls

    def scrape_boards(self, urls: list[str]) -> None:
        for url in urls:
            pin_urls = self.scrape_board_pins(url)
            self.session.add_all(
                [
                    UrlModel(
                        pin_url=pin_url,
                        board_url=url,
                        query=self.query,
                        scraped=False,
                    )
                    for pin_url in pin_urls
                ]
            )
            self.session.commit()

    def run(self) -> None:
        try:
            self.setup()
            board_urls = self.scrape_board_urls()
            self.scrape_boards(board_urls)
        finally:
            if self.session is not None:
                self.session.close()


if __name__ == "__main__":
    fire.Fire(Scraper)
