from typing import Iterable

from settings import SQLITE_DB_PATH
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class Url(Base):
    __tablename__ = "url"

    id: Mapped[int] = mapped_column(primary_key=True)
    pin_url: Mapped[str]
    board_url: Mapped[str]
    query: Mapped[str]
    scraped: Mapped[bool]

    @staticmethod
    def exclude_duplicates(
        session: Session, urls: Iterable, is_board: bool = False
    ) -> list[str]:
        deduplicated_urls = []
        for url in urls:
            stmt = select(Url)
            if is_board:
                stmt = stmt.where(Url.board_url == url)
            else:
                stmt = stmt.where(Url.pin_url == url)
            result = session.scalars(stmt).first()
            if result is None:
                deduplicated_urls.append(url)

        return deduplicated_urls


def setup_db() -> sessionmaker:
    engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")
    Base.metadata.create_all(engine)

    return sessionmaker(engine)
