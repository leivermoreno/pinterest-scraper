import logging
import sqlite3
from sqlite3 import Row
from typing import List

from settings import DATABASE_NAME

logger = logging.getLogger(f"scraper.{__name__}")
_conn: sqlite3.Connection | None = None


def _create_tables() -> None:
    # creating tables
    _conn.executescript(
        f"""
        BEGIN;
        CREATE TABLE IF NOT EXISTS job(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        query TEXT NOT NULL UNIQUE,
        stage TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS board(
        job_id INTEGER NOT NULL,
        url TEXT NOT NULL UNIQUE,
        done INT NOT NULL,
        FOREIGN KEY(job_id) REFERENCES job(id)
        );
        CREATE TABLE IF NOT EXISTS pin(
        job_id INTEGER NOT NULL,
        url TEXT NOT NULL UNIQUE,
        img_url TEXT NOT NULL,
        done INT NOT NULL,
        FOREIGN KEY(job_id) REFERENCES job(id)
        );
        COMMIT;
    """
    )


def initialize() -> None:
    global _conn
    _conn = sqlite3.connect(DATABASE_NAME)
    _conn.execute("PRAGMA foreign_keys = ON")
    _conn.row_factory = Row
    _create_tables()
    logger.debug("Db conn set up.")


def close_conn() -> None:  # todo when? on command or at final of operations
    _conn.close()


def create_job(query: str, stage: str = "board") -> int:
    curr = _conn.execute(
        """
    INSERT INTO job(query, stage)
    VALUES(?, ?)
    """,
        (query.lower(), stage),
    )
    _conn.commit()

    return curr.lastrowid


def get_all_jobs() -> List[Row]:
    curr = _conn.execute(
        """
    SELECT * FROM job
    """
    )

    return curr.fetchall()


def get_job_by_query(query: str) -> Row | None:
    curr = _conn.execute(
        """
    SELECT * FROM job
    WHERE query = ?
    """,
        (query.lower(),),
    )

    return curr.fetchone()


def update_job_stage(job_id: int, stage: str) -> None:
    _conn.execute(
        """
    UPDATE job
    SET stage = ?
    WHERE id = ?
    """,
        (stage, job_id),
    )
    _conn.commit()


def create_many_board(rows: List[tuple]) -> None:
    _conn.executemany(
        f"""
        INSERT OR IGNORE INTO board(job_id, url, done)
        VALUES(?, ?, 0)
        """,
        rows,
    )
    _conn.commit()


def create_many_pin(rows: List[tuple]) -> None:
    _conn.executemany(
        f"""
        INSERT OR IGNORE INTO pin(job_id, url, img_url, done)
        VALUES(?, ?, ?, 0)
        """,
        rows,
    )
    _conn.commit()


_name_list = ["board", "pin"]


def get_all_board_or_pin_by_job_id(name: str, job_id: int) -> List[Row]:
    assert name in _name_list

    curr = _conn.execute(
        f"""
    SELECT * FROM {name}
    WHERE job_id = ? AND done = 0
    """,
        (job_id,),
    )

    return curr.fetchall()


def update_board_or_pin_done_by_url(name: str, url: str, done: int) -> None:
    assert name in _name_list

    _conn.execute(
        f"""
    UPDATE {name}
    SET done = ?
    WHERE url = ?
    """,
        (done, url),
    )
    _conn.commit()
