from typing import Iterable

from settings import SQLITE_DB_PATH
from sqlalchemy import Engine, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column


class Base(DeclarativeBase):
    pass


class Url(Base):
    __tablename__ = "url"

    id: Mapped[int] = mapped_column(primary_key=True)
    scraped: Mapped[bool]
    url: Mapped[str]

    @staticmethod
    def exclude_duplicates(session: Session, urls: Iterable) -> list[str]:
        deduplicated_urls = []
        for url in urls:
            stmt = select(Url).where(Url.url == url)
            result = session.scalars(stmt).first()
            if result is None:
                deduplicated_urls.append(url)

        return deduplicated_urls


def setup_db() -> Engine:
    engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")
    Base.metadata.create_all(engine)

    return engine
