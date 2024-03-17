# Pinterest Scraper

Automation to scrape and download pins from pinterest. It consists of two stages.

**First stage:** it performs a search for boards matching the query and scrapes all pin urls within them. The scraped urls are saved to a sqlite database and marked to be downloaded later.

**Second stage:** it reads all pin urls marked as pending and yield the requests. When the response arrives, download the img, save pin html and img path in a new row to feed export.

## Environment Variables

`PYTHON_ENV` set by default in the docker image to "production" so browser runs in headless mode.

## Installation

Use docker to build the image from Dockerfile:

```sh
docker build -t pinterest-scraper .
```

Archives to mount in `/usr/src/app`:

- `proxies.txt` proxy list, one per line
- `output` all output will go here

```sh
docker run --rm \
-v $(pwd)/proxies.txt:/usr/src/app/proxies.txt \
-v $(pwd)/output:/usr/src/app/output \
pinterest-scraper
```

## How to run

Append the executable and arguments to docker run command.

**Running first stage**

```sh
python playwright_scraper/scraper.py run --query="video game"
```

Params:

- query
- skip-process-clean make sure to use in development. Disable cleaning of process spawned by playwright after browser is done. This is needed to prevent memory leaks since playwright is intended for tests rather than long running jobs like scraping.

**Second stage**

```sh
scrapy crawl download-pins -o output/data.jsonl -o output/data.csv
```

As simple as that. Just provide where the data is going to be saved. In this case two feed exports are set.
