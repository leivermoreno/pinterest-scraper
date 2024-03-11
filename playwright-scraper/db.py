from settings import SQLITE_DB_PATH
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Url(Base):
    __tablename__ = "url"

    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str]


def setup_db() -> Engine:
    engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}")
    Base.metadata.create_all(engine)

    return engine
