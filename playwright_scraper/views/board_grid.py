from bs4 import BeautifulSoup
from views._base_view import BaseView


class BoardGridView(BaseView):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._board_urls = set()

    def _extract_urls(self):
        html = self._page.content()
        soup = BeautifulSoup(html, "lxml")

        for board in soup.select("[role=listitem] a"):
            self._board_urls.add(board["href"])

    def start_view(self):
        self._page.wait_for_timeout(self._short_wait)
        self._scroll_to_bottom_while_do(self._extract_urls)

    def get_board_urls(self):
        return self._board_urls
