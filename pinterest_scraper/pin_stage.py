import logging
from typing import Callable
from urllib.parse import urljoin

from selenium.common import NoSuchElementException, TimeoutException
from selenium.webdriver.common.by import By

from pinterest_scraper.download_stage import DownloadStage
from pinterest_scraper.stage import Stage
from pinterest_scraper.utils import time_perf
from settings import MAX_RETRY

logger = logging.getLogger(f'scraper.{__name__}')


class PinStage(Stage):
    @time_perf('scroll to end of board and get all pins')
    def scroll_and_scrape(self, fn: Callable) -> None:
        super().scroll_and_scrape(fn)

    def scrape_urls(self, urls: set):

        pin_selector = '.qDf > .Hsu .Hsu > .a3i div.wsz.zmN > div[data-test-id="deeplink-wrapper"] a'
        pins = self.driver.find_elements(By.CSS_SELECTOR, pin_selector)
        for pin in pins:
            pin_url = pin.get_attribute('href')
            pin_img = pin.find_element(By.TAG_NAME, 'img')
            pin_img_url = pin_img.get_attribute('src')
            print('gotten', pin_img_url)
            pin_data = (pin_url, pin_img_url)
            urls.add(pin_data)

    def scrape(self):
        pin_urls = set()

        get_sections = lambda: self.driver.find_elements(By.CSS_SELECTOR, 'div[data-test-id=board-section]')

        try:
            # there may be sections or not
            # there is no need to scroll since all sections are in dom at first
            sections = get_sections()
        except NoSuchElementException:
            pass
        else:
            n_sections = len(sections)
            for section_n in range(n_sections):
                # re-selecting since on every section click els are removed
                sections = get_sections()
                sections[section_n].click()
                self.scroll_and_scrape(lambda: self.scrape_urls(pin_urls))
                self.driver.back()

                # if section_n == n_sections - 1:
                #     ActionChains(self.driver).scroll_to_element()

        # time to get the pins that are in main page
        self.scroll_and_scrape(lambda: self.scrape_urls(pin_urls))

        pin_urls = list(pin_urls)

        rows = [
            (self.job['id'], urljoin(self.driver.current_url, urls[0]), urls[1])
            for urls in pin_urls
        ]
        logger.info(f'Found {len(rows)} pins for board {self.driver.current_url}, query: {self.job["query"]}.')
        self.db.create_many_pin(rows)

    def start_scraping(self):
        super().start_scraping()

        # boards = self.db.get_all_board_or_pin_by_job_id('board', self.job['id'])
        #
        # for board in boards:
        #     url = board['url']
        #     for i in range(0, MAX_RETRY + 1):
        #         try:
        #             self.driver.get(url)
        #             self.scrape()
        #             self.db.update_board_or_pin_done_by_url('board', url, 1)
        #             break
        #         except (NoSuchElementException, TimeoutException) as e:
        #             logger.exception(f'{e.__class__.__name__} scraping boards from {url}, retrying...')
        #             if i == MAX_RETRY:
        #                 raise

        retries = 0
        while True:
            try:
                boards = self.db.get_all_board_or_pin_by_job_id('board', self.job['id'])
                for board in boards:
                    url = board['url']
                    self.driver.get(url)
                    self.scrape()
                    self.db.update_board_or_pin_done_by_url('board', url, 1)
                    retries = 0
                    logger.info(f'Successfully scraped board {url}.')

                break

            except (NoSuchElementException, TimeoutException) as e:
                if retries == MAX_RETRY:
                    raise

                logger.exception(f'{e.__class__.__name__} scraping boards from {url}, retrying...')
                retries += 1

        self.db.update_job_stage(self.job['id'], 'download')
        logger.info('Finished scraping of pins, starting download stage.')
        DownloadStage(self.job, self.driver, self.headless).start_scraping()
