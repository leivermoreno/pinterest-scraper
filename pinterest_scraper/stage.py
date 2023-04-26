import logging
import math
import time
from sqlite3 import Row
from typing import Callable

from selenium import webdriver
from selenium.webdriver import ActionChains

from pinterest_scraper import db
from settings import TIMEOUT, SCROLL_DELAY

# todo revert this
# import undetected_chromedriver as webdriver

logger = logging.getLogger(f'scraper.{__name__}')


class Stage:
    def __init__(
            self, job: Row | dict, driver: webdriver.Chrome = None, headless: bool = True
    ) -> None:
        self.db = db
        self.job = job
        self.driver = driver
        self.headless = headless

    def init_driver(self) -> None:
        # init driver if not already provided
        if isinstance(self.driver, webdriver.Chrome):
            return

        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        # todo keep this?
        options.add_argument('--disable-logging')
        options.add_argument('--log-level=3')
        # todo see if can disable images
        self.driver = webdriver.Chrome(options=options)
        self.driver.set_window_size(1280, 1024)
        self.driver.set_page_load_timeout(TIMEOUT)
        self.driver.implicitly_wait(TIMEOUT)  # todo keep this?
        logger.debug("Driver set up.")

    def start_scraping(self):
        logger.debug("Starting scraping.")
        self.init_driver()

    def close(self):  # todo when?
        self.driver.quit()
        logger.debug('Driver closed.')

    def get_scroll_height(self) -> int:
        return self.driver.execute_script('return document.body.scrollHeight')

    def scroll_and_scrape(self, fn: Callable) -> None:
        logger.debug('Starting to scroll.')
        # old_body_height = self.get_scroll_height()
        inner_height = self.driver.execute_script('return window.innerHeight')
        scroll_amount = int(inner_height * .2)
        seconds_sleep = 0
        while True:
            # exec f in every scroll step
            fn()
            # scroll 20% of viewport height since dom is dynamically populated,
            # removing els not in viewport and adding new ones
            ActionChains(self.driver).scroll_by_amount(0, scroll_amount).perform()
            # a short delay that also gives chance to load more els
            time.sleep(SCROLL_DELAY)
            seconds_sleep += SCROLL_DELAY

            new_body_height = self.get_scroll_height()
            scroll_y = self.driver.execute_script('return window.scrollY')
            end_of_page = math.ceil(inner_height + scroll_y) >= new_body_height  # round up due to precision loss
            if end_of_page and seconds_sleep >= TIMEOUT:
                logger.debug('End of page reached.')
                break

            # if new_body_height > old_body_height or not end_of_page:
            #     old_body_height = new_body_height
            #     seconds_sleep = 0
            #     continue

            if not end_of_page:
                seconds_sleep = 0
