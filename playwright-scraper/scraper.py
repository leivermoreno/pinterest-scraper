import itertools
import logging
import random
import urllib.parse
from pathlib import Path
from typing import Iterator

import settings
from db import setup_db
from sqlalchemy import Engine
from sqlalchemy.orm import Session


class Scraper:
    def __init__(self, query: str) -> None:
        query = urllib.parse.quote_plus(query)
        self.base_url = "https://www.pinterest.com"
        self.initial_url = f"{self.base_url}/search/boards/?q={query}&rs=typed"
        self.output_dir = settings.OUTPUT_DIR
        self.proxy_list_path = settings.PROXY_LIST_PATH
        self.engine: Engine
        self.session: Session
        self.proxy_list: Iterator
        self.logger = logging.getLogger(__name__)

    def load_proxy_list(self, proxy_list_path: Path) -> list[dict]:
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

    def setup(self) -> None:
        self.output_dir.mkdir(exist_ok=True)
        self.engine = setup_db()
        self.session = Session(self.engine)
        self.proxy_list = itertools.cycle(self.load_proxy_list(self.proxy_list_path))
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s",
            datefmt="%m-%d %H:%M:%S",
        )
        self.logger.info("Scraper setup complete")

    def run(self) -> None:
        try:
            self.setup()
        finally:
            if self.session is not None:
                self.session.close()
