import logging
import math
import time
from typing import Callable

import psutil
from playwright.sync_api import Page
from settings import CHECK_BOTTOM_TIMES, SCROLL_DELAY, SHORT_WAIT


class BaseView:
    def __init__(self, page: Page) -> None:
        self._page = page
        self._scroll_delay = SCROLL_DELAY
        self._check_bottom_times = CHECK_BOTTOM_TIMES
        self._short_wait = SHORT_WAIT
        self._logger = logging.getLogger(__name__)

    def _scroll_to_bottom_while_do(
        self,
        do: Callable,
        stop_on_more_heading: bool = True,
    ):
        document_element_handle = self._page.evaluate_handle("document.documentElement")
        client_height = document_element_handle.get_property(
            "clientHeight"
        ).json_value()
        scroll_amount = client_height * 0.2
        bottom_checks = 0
        amount_scrolled = client_height
        get_scrolled_from_api = False
        more_heading_locator = self._page.locator("h2.GTB")
        time_counter = time.perf_counter()

        while True:
            self._logger.debug("Checking memory usage")
            mem_usage_percent = psutil.virtual_memory().percent
            if (time.perf_counter() - time_counter) >= 30:
                time_counter = time.perf_counter()
                self._logger.info(f"Memory usage {mem_usage_percent}%")
            if mem_usage_percent > 90:
                self._logger.info(
                    f"Memory usage exceeded threshold. Ram usage {mem_usage_percent}%, stopping scroll"
                )
                break

            do()
            self._page.mouse.wheel(0, scroll_amount)

            if stop_on_more_heading and more_heading_locator.is_visible():
                bounding_box = more_heading_locator.bounding_box()
                more_heading_crossed_viewport = bounding_box["y"] - client_height <= 0
                if more_heading_crossed_viewport:
                    break

            if get_scrolled_from_api:
                get_scrolled_from_api = False
                amount_scrolled = document_element_handle.get_property(
                    "scrollTop"
                ).json_value()
                amount_scrolled += client_height
            else:
                amount_scrolled += scroll_amount

            time.sleep(self._scroll_delay)

            scroll_height = document_element_handle.get_property(
                "scrollHeight"
            ).json_value()
            bottom_reached = math.ceil(amount_scrolled) >= scroll_height

            if bottom_reached:
                get_scrolled_from_api = True
                bottom_checks += 1
                if bottom_checks >= self._check_bottom_times:
                    break
            else:
                bottom_checks = 0
