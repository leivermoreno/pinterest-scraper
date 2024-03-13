import re

from bs4 import BeautifulSoup
from views._base_view import BaseView


class PinGridView(BaseView):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._pin_urls = set()

    def _extract_pin_urls(self):
        html = self._page.content()
        soup = BeautifulSoup(html, "lxml")
        for pin in soup.find_all("a", href=re.compile(r"\/pin\/\d+\/")):
            self._pin_urls.add(pin["href"])

    def _scrape_sections(self):
        section_selector = ".Uxw"
        sections_number = self._page.locator(section_selector).count()

        for i in range(sections_number):
            self._page.locator(section_selector).nth(i).click()
            self._page.wait_for_timeout(self._short_wait)
            self._scroll_to_bottom_while_do(self._extract_pin_urls)
            self._page.go_back()
            self._page.wait_for_timeout(self._short_wait)

    def start_view(self):
        self._page.wait_for_timeout(self._short_wait)
        self._scrape_sections()
        self._scroll_to_bottom_while_do(self._extract_pin_urls)

    def get_pin_urls(self):
        return self._pin_urls
