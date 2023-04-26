import logging
import urllib.parse
from typing import Callable
from urllib.parse import urljoin

from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from pinterest_scraper.pin_stage import PinStage
from pinterest_scraper.stage import Stage
from pinterest_scraper.utils import time_perf
from settings import MAX_RETRY

logger = logging.getLogger(f'scraper.{__name__}')
URL = "https://www.pinterest.com/search/boards/?q={}&rs=typed"


class BoardStage(Stage):

    @time_perf('scroll to end of boards page')
    def scroll_and_scrape(self, fn: Callable) -> None:
        super().scroll_and_scrape(fn)

    def scrape_urls(self, urls: set):
        boards = self.driver.find_elements(By.CSS_SELECTOR, 'div[role=listitem] a')
        board_relative_urls = [board.get_attribute('href') for board in boards]
        urls.update(board_relative_urls)

    def scrape(self):
        board_urls = set()

        self.scroll_and_scrape(lambda: self.scrape_urls(board_urls))

        rows = [
            (self.job['id'], urljoin(self.driver.current_url, url))
            for url in board_urls
        ]
        logger.info(f'Found {len(rows)} boards for {self.job["query"]}.')
        self.db.create_many_board(rows)

    def start_scraping(self) -> None:
        super().start_scraping()

        query = urllib.parse.quote_plus(self.job['query'])
        url = URL.format(query)

        for i in range(0, MAX_RETRY + 1):
            try:
                self.driver.get(url)
                self.scrape()
                break
            except (NoSuchElementException, TimeoutException) as e:
                if i == MAX_RETRY:
                    raise

                logger.exception(f'{e.__class__.__name__} scraping boards from {url}, retrying...')

        self.db.update_job_stage(self.job['id'], 'pin')
        logger.info('Finished scraping of boards. Starting pins stage.')
        PinStage(self.job, self.driver, self.headless).start_scraping()
