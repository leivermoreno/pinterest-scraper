import logging
import math
import time
from sqlite3 import Row
from typing import Callable, Optional

from fake_useragent import UserAgent
from selenium import webdriver
from selenium.common import StaleElementReferenceException, NoSuchElementException
from selenium.webdriver import ActionChains
from selenium.webdriver.support.wait import WebDriverWait

from pinterest_scraper import db
from settings import TIMEOUT, SCROLL_DELAY, MAX_RETRY

# todo revert this
# import undetected_chromedriver as webdriver

logger = logging.getLogger(f"scraper.{__name__}")


class Stage:
    def __init__(
        self, job: Row | dict, driver: webdriver.Chrome = None, headless: bool = True
    ) -> None:
        self._db = db
        self._job = job
        self._driver = driver
        self._wait: Optional[WebDriverWait] = None
        self._headless = headless

    def __init_driver(self) -> None:
        # init driver if not already provided
        if isinstance(self._driver, webdriver.Chrome):
            self._wait = WebDriverWait(self._driver, TIMEOUT)
            return

        ua = UserAgent(browsers=["chrome", "edge", "firefox", "safari", "opera"])
        ua = ua.random
        options = webdriver.ChromeOptions()
        if self._headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-logging")
        options.add_argument("--log-level=3")
        options.add_argument(f"user-agent={ua}")
        options.add_argument("--blink-settings=imagesEnabled=false")
        self._driver = webdriver.Chrome(options=options)
        self._driver.set_window_size(1280, 1024)
        self._driver.set_page_load_timeout(TIMEOUT)
        self._wait = WebDriverWait(self._driver, TIMEOUT)
        logger.debug("Driver set up.")

    def start_scraping(self) -> None:
        logger.debug("Starting scraping.")
        self.__init_driver()

    def close(self) -> None:  # todo when?
        self._driver.quit()
        logger.debug("Driver closed.")

    def __get_scroll_height(self) -> int:
        return self._driver.execute_script("return document.body.scrollHeight")

    def _scroll_and_scrape(self, fn: Callable) -> None:
        logger.debug("Starting to scroll.")
        # old_body_height = self.get_scroll_height()
        inner_height = self._driver.execute_script("return window.innerHeight")
        scroll_amount = int(inner_height * 0.2)
        seconds_sleep = 0
        while True:
            # exec fn in every scroll step
            for i in range(MAX_RETRY + 1):
                try:
                    fn()
                except (StaleElementReferenceException, NoSuchElementException):
                    if i == MAX_RETRY:
                        raise
                    logger.debug("Element stale or not present, retrying...")

            # scroll 20% of viewport height since dom is dynamically populated,
            # removing els not in viewport and adding new ones
            ActionChains(self._driver).scroll_by_amount(0, scroll_amount).perform()
            # a short delay that also gives chance to load more els
            time.sleep(SCROLL_DELAY)
            seconds_sleep += SCROLL_DELAY

            new_body_height = self.__get_scroll_height()
            scroll_y = self._driver.execute_script("return window.scrollY")
            end_of_page = (
                math.ceil(inner_height + scroll_y) >= new_body_height
            )  # round up due to precision loss
            if end_of_page and seconds_sleep >= TIMEOUT:
                logger.debug("End of page reached.")
                break

            if not end_of_page:
                seconds_sleep = 0

            # check if more like this el enters viewport
            el_top = self._driver.execute_script(
                """
            const el = document.querySelector("h2.GTB");
            if (!el) {
                return null
            }
            const elTop = el.getBoundingClientRect().top;
            return elTop;
            """
            )
            if el_top is None:
                continue

            is_in_viewport = el_top - inner_height <= 0
            if is_in_viewport:
                break
