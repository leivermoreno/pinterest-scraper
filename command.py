import logging

import fire

import logging_config
from pinterest_scraper import db
from pinterest_scraper.board_stage import BoardStage
from pinterest_scraper.download_stage import DownloadStage
from pinterest_scraper.pin_stage import PinStage

logging_config.configure()
logger = logging.getLogger(f"scraper.{__name__}")

# init db conn
db.initialize()


class Command:
    def show_jobs(self):
        jobs = db.get_all_jobs()
        if not jobs:
            print("No jobs created yet.")

        for job in jobs:
            print(
                f'{job["id"]}. Job for query: {job["query"]}, in stage: {job["stage"]}.'
            )

    def start_scraping(self, query: str, headed: bool = False):
        job = db.get_job_by_query(query)

        if not job:
            logger.info(f"Job created for query: {query}.")
            job_id = db.create_job(query)
            job = {"id": job_id, "query": query, "stage": "board"}

        stage = job["stage"]
        if stage == "board":
            stage_cls = BoardStage
        elif stage == "pin":
            stage_cls = PinStage
        else:
            stage_cls = DownloadStage

        try:
            stage_instance = stage_cls(job, headless=not headed)
            stage_instance.start_scraping()
        except:
            logger.critical(
                f'Unable to handle exception on {stage_cls.__name__}, for query "{job["query"]}".',
                exc_info=True,
            )
        finally:
            stage_instance.close()
            db.close_conn()


fire.Fire(Command)
