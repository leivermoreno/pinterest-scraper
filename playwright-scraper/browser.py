import logging

import psutil
from playwright.sync_api import Page, sync_playwright
from settings import HEADLESS


class Browser:
    def __init__(self, url: str, proxy: dict):
        self._url = url
        self._proxy = proxy
        self._pw = None
        self._browser = None
        self._context = None
        self._page = None
        self._headless = HEADLESS
        self.logger = logging.getLogger(__name__)

    def get_page(self) -> Page:
        self._pw = sync_playwright().start()
        self._browser = self._pw.firefox.launch(
            proxy=self._proxy, headless=self._headless
        )
        self._context = self._browser.new_context()
        self._page = self._context.new_page()
        self._page.goto(self._url)

        return self._page

    def close(self) -> None:
        self._page.close()
        self._context.close()
        self._browser.close()
        self._pw.stop()

    def _clean_process(self) -> None:
        for proc in psutil.process_iter(["pid", "name"]):
            if "node" in proc.info["name"] or "firefox" in proc.info["name"]:
                proc.kill()
                self.logger.info(
                    f"Killed {proc.info['name']} with pid {proc.info['pid']}"
                )

    def __enter__(self) -> Page:
        return self.get_page()

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()
        self._clean_process()
