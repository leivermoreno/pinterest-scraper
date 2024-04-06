import json
import re
from typing import Iterable

from scrapy import Request, Spider, signals
from scrapy.crawler import Crawler
from scrapy.http import TextResponse
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from scrapy_scraper.db import Session
from scrapy_scraper.db import Url as UrlModel


class DownloadPinsSpider(Spider):
    name = "download-pins"
    allowed_domains = ["pinterest.com"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.pending_count = 0
        self.completed_count = 0
        self.session = None

    @classmethod
    def from_crawler(cls, crawler: Crawler, *args, **kwargs):
        spider = super().from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_opened, signal=signals.spider_opened)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_opened(self, spider):
        self.session = Session()

    def spider_closed(self, spider, reason):
        self.session.close()

    def start_requests(self) -> Iterable[Request]:
        stmt = select(UrlModel).filter_by(scraped=False)
        for url in self.session.scalars(stmt):
            self.pending_count += 1
            yield Request(
                url.pin_url,
                cb_kwargs={
                    "query": url.query,
                    "board_url": url.board_url,
                    "row_id": url.id,
                },
            )

    def parse(self, response: TextResponse, query: str, board_url: str, row_id: int):
        pin_url = response.url
        try:
            json_data = re.search(
                r'<script data-relay-response="true" type="application\/json">(.+?)<\/script>',
                response.text,
                flags=re.S,
            ).group(1)

            data = json.loads(json_data)
            data = data["response"]["data"]["v3GetPinQuery"]["data"]

            self.completed_count += 1
            self.logger.info(f"Pin scraped. Url: {pin_url}")
            self.logger.info(
                f"Pins scraped count={self.completed_count} out of {self.pending_count}"
            )

            if data and data.get("imageLargeUrl"):
                yield {
                    "board_url": board_url,
                    "query": query,
                    "pin_url": pin_url,
                    "title": data["title"],
                    "description": data["closeupUnifiedDescription"],
                    "image_urls": [data["imageLargeUrl"]],
                }
            else:
                self.logger.info(f"Pin {pin_url} has no data")

        except (KeyError, AttributeError, json.JSONDecodeError) as e:
            self.logger.error(f"Error parsing pin {pin_url}: {repr(e)}")

        self.session.execute(update(UrlModel).filter_by(id=row_id).values(scraped=True))
        self.session.commit()
