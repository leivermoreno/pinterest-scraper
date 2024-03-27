from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker

from scrapy_scraper.settings import POSTGRES_HOST, POSTGRES_USER, POSTGRES_USER_PASSWORD

Base = automap_base()


def setup_db():
    engine = create_engine(
        f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_USER_PASSWORD}@{POSTGRES_HOST}/pinterest_scraper"
    )
    Base.prepare(autoload_with=engine)

    return sessionmaker(engine)
