import logging
from typing import Callable
from urllib.parse import urljoin

from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec

from pinterest_scraper.download_stage import DownloadStage
from pinterest_scraper.stage import Stage
from pinterest_scraper.utils import time_perf
from settings import MAX_RETRY

logger = logging.getLogger(f"scraper.{__name__}")


class PinStage(Stage):
    @time_perf("scroll to end of board and get all pins")
    def _scroll_and_scrape(self, fn: Callable) -> None:
        super()._scroll_and_scrape(fn)

    def _scrape_urls(self, urls: set) -> None:
        pin_selector = '.qDf > .Hsu .Hsu > .a3i div.wsz.zmN > div[data-test-id="deeplink-wrapper"] a'
        pins = self._wait.until(
            ec.presence_of_all_elements_located((By.CSS_SELECTOR, pin_selector))
        )
        for pin in pins:
            pin_url = pin.get_attribute("href")
            pin_img = pin.find_element(By.TAG_NAME, "img")
            pin_img_url = pin_img.get_attribute("src")
            pin_data = (pin_url, pin_img_url)
            urls.add(pin_data)

    def _scrape(self) -> None:
        pin_urls = set()

        get_sections = lambda: self._wait.until(
            ec.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div[data-test-id=board-section]")
            )
        )

        try:
            # there may be sections or not
            # there is no need to scroll since all sections are in dom at first
            sections = get_sections()
        except TimeoutException:
            pass
        else:
            n_sections = len(sections)
            for section_n in range(n_sections):
                # re-selecting since on every section click els are removed
                sections = get_sections()
                sections[section_n].click()
                self._scroll_and_scrape(lambda: self._scrape_urls(pin_urls))
                self._driver.back()

        # time to get the pins that are in main page
        self._scroll_and_scrape(lambda: self._scrape_urls(pin_urls))

        pin_urls = list(pin_urls)

        rows = [
            (self._job["id"], urljoin(self._driver.current_url, urls[0]), urls[1])
            for urls in pin_urls
        ]
        logger.info(
            f'Found {len(rows)} pins for board {self._driver.current_url}, query: {self._job["query"]}.'
        )
        self._db.create_many_pin(rows)

    def start_scraping(self) -> None:
        super().start_scraping()

        retries = 0
        while True:
            try:
                # retrieve boards here to not re-scrape boards
                # successfully scraped before error
                boards = self._db.get_all_board_or_pin_by_job_id(
                    "board", self._job["id"]
                )
                for board in boards:
                    url = board["url"]
                    self._driver.get(url)
                    self._scrape()
                    self._db.update_board_or_pin_done_by_url("board", url, 1)
                    retries = 0
                    logger.info(f"Successfully scraped board {url}.")

                break

            except TimeoutException:
                if retries == MAX_RETRY:
                    raise

                # noinspection PyUnboundLocalVariable
                logger.exception(f"Timeout scraping boards from {url}, retrying...")
                retries += 1

        self._db.update_job_stage(self._job["id"], "download")
        logger.info("Finished scraping of pins, starting download stage.")
        DownloadStage(self._job, self._driver, self._headless).start_scraping()
