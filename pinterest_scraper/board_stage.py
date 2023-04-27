import logging
import urllib.parse
from typing import Callable
from urllib.parse import urljoin

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC

from pinterest_scraper.pin_stage import PinStage
from pinterest_scraper.stage import Stage
from pinterest_scraper.utils import time_perf
from settings import MAX_RETRY

logger = logging.getLogger(f"scraper.{__name__}")
URL = "https://www.pinterest.com/search/boards/?q={}&rs=typed"


class BoardStage(Stage):
    @time_perf("scroll to end of boards page")
    def _scroll_and_scrape(self, fn: Callable) -> None:
        super()._scroll_and_scrape(fn)

    def _scrape_urls(self, urls: set):
        boards = self._wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div[role=listitem] a")
            )
        )
        board_relative_urls = [board.get_attribute("href") for board in boards]
        urls.update(board_relative_urls)

    def _scrape(self):
        board_urls = set()

        self._scroll_and_scrape(lambda: self._scrape_urls(board_urls))

        rows = [
            (self._job["id"], urljoin(self._driver.current_url, url))
            for url in board_urls
        ]
        logger.info(f'Found {len(rows)} boards for {self._job["query"]}.')
        self._db.create_many_board(rows)

    def start_scraping(self) -> None:
        super().start_scraping()

        query = urllib.parse.quote_plus(self._job["query"])
        url = URL.format(query)

        for i in range(0, MAX_RETRY + 1):
            try:
                self._driver.get(url)
                self._scrape()
                break
            except TimeoutException:
                if i == MAX_RETRY:
                    raise
            finally:
                logger.exception(
                    f"Timeout exception scraping boards from {url}, retrying..."
                )

        self._db.update_job_stage(self._job["id"], "pin")
        logger.info("Finished scraping of boards. Starting pins stage.")
        PinStage(self._job, self._driver, self._headless).start_scraping()
