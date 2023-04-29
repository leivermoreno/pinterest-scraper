import logging
import os
import time
from datetime import timedelta
from os import path
from sqlite3 import Row
from typing import List
from urllib.parse import urlparse, urlunparse

from requests import Session, RequestException, Response

from pinterest_scraper.stage import Stage
from settings import MAX_RETRY, OUTPUT_FOlDER, TIMEOUT, DOWNLOAD_DELAY

logger = logging.getLogger(f"scraper.{__name__}")


class DownloadStage(Stage):
    def __get_img_urls(self, url: str) -> List[str]:
        parsed_url = urlparse(url)
        path_parts = parsed_url.path.split("/")
        path_parts[1] = "originals"

        extensions = ["jpg", "png"]
        new_urls = []
        for ext in extensions:
            filename = path.splitext(path_parts[-1])[0]
            basename = f"{filename}.{ext}"
            path_parts[-1] = basename
            new_path = "/".join(path_parts)
            new_url = urlunparse(
                (
                    parsed_url.scheme,
                    parsed_url.netloc,
                    new_path,
                    parsed_url.params,
                    parsed_url.query,
                    parsed_url.fragment,
                )
            )
            new_urls.append(new_url)

        return new_urls

    def __save_img(self, res: Response, img_url: str) -> None:
        basename = path.basename(img_url)
        img_path = path.join(OUTPUT_FOlDER, "jobs", self._job["query"], basename)
        os.makedirs(path.dirname(img_path), exist_ok=True)

        with open(img_path, "wb") as fh:
            fh.write(res.content)

    def __download_pin_img(self, session: Session, pin: Row) -> None:
        img_urls = self.__get_img_urls(pin["img_url"])
        for img_url in img_urls:
            res = session.get(img_url, timeout=TIMEOUT)

            # sleeping for DOWNLOAD_DELAY seconds between requests
            delta_diff = res.elapsed - timedelta(seconds=DOWNLOAD_DELAY)
            if delta_diff.total_seconds() < 0:
                time.sleep(abs(delta_diff.total_seconds()))

            # if xml, have to try with the other url
            if res.headers["content-type"] == "application/xml":
                continue

            res.raise_for_status()

            self.__save_img(res, img_url)

            break

    def start_scraping(self) -> None:
        # super().start_scraping() # todo revert this

        with Session() as session:
            retries = 0
            while True:
                try:
                    # retrieve pins here to not re-download pins
                    # successfully scraped before error
                    pins = self._db.get_all_board_or_pin_by_job_id(
                        "pin", self._job["id"]
                    )
                    for pin in pins:
                        self.__download_pin_img(session, pin)

                        self._db.update_board_or_pin_done_by_url("pin", pin["url"], 1)
                        retries = 0
                        logger.info(f"Successfully scraped pin {pin['url']}.")

                    break
                except RequestException as e:
                    if retries == MAX_RETRY:
                        raise

                    logger.exception(
                        f"Exception downloading pin: {pin['url']}, retrying..."
                    )
                    retries += 1

        self._db.update_job_stage(self._job["id"], "completed")
        logger.info(f"Finished scraping of job for query {self._job['query']}.")
