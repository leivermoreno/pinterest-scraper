from sqlalchemy import create_engine
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists

from scrapy_scraper.settings import POSTGRES_HOST, POSTGRES_USER, POSTGRES_USER_PASSWORD

engine = create_engine(
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_USER_PASSWORD}@{POSTGRES_HOST}/pinterest_scraper"
)

if not database_exists(engine.url):
    create_database(engine.url)

Base = automap_base()
Base.prepare(autoload_with=engine)

Session = sessionmaker(engine)

Url = Base.classes.url
