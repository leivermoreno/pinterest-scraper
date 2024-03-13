import itertools
import logging
import random
from pathlib import Path

import psutil
from playwright.sync_api import Page, sync_playwright
from settings import HEADLESS, PROXY_LIST_PATH


class Browser:
    def __init__(self, url: str, proxy: dict, clean_process: bool):
        self._url = url
        self._proxy = proxy
        self._skip_process_clean = not clean_process
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
        if self._skip_process_clean == False:
            self._clean_process()


class BrowserManager:

    def __init__(self, clean_process: bool) -> None:
        self._proxy_list = itertools.cycle(self._load_proxy_list(PROXY_LIST_PATH))
        self._clean_process = clean_process

    def _load_proxy_list(self, proxy_list_path: Path) -> list[dict]:
        proxy_list = []
        with proxy_list_path.open("r", encoding="utf-8") as fp:
            for line in fp:
                [credentials, server] = line.split("@")
                [username, password] = credentials.split(":")
                proxy_list.append(
                    {"server": server, "username": username, "password": password}
                )
        random.shuffle(proxy_list)

        return proxy_list

    def get_browser(self, url: str) -> Browser:
        return Browser(
            url, proxy=next(self._proxy_list), clean_process=self._clean_process
        )
