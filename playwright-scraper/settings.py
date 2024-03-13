import os
from pathlib import Path

is_production = os.getenv("PYTHON_ENV", "development") == "production"

OUTPUT_DIR = Path("output")
SQLITE_DB_PATH = OUTPUT_DIR / "db.sqlite3"
PROXY_LIST_PATH = Path("proxies.txt")
HEADLESS = is_production
SCROLL_DELAY = 0.3
CHECK_BOTTOM_TIMES = 33
SHORT_WAIT = 3000
RETRY_TIMES = 3
