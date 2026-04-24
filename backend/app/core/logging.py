import logging
from urllib.parse import urlparse

from app.core.config import Settings


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )


def log_startup(settings: Settings) -> None:
    database_type = urlparse(settings.database_url).scheme or "sqlite"
    logging.getLogger("app.startup").info(
        "Desktop IRM backend starting env=%s database=%s storage=%s",
        settings.app_env,
        database_type,
        settings.local_storage_dir,
    )

