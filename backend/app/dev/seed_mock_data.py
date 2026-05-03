from __future__ import annotations

import argparse
import os
import sqlite3
from pathlib import Path
from urllib.parse import unquote, urlparse

from alembic import command
from alembic.config import Config

from app.core.config import get_settings

BACKEND_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_SQL_PATH = BACKEND_ROOT / "dev" / "mock_data.sql"
DEFAULT_ALEMBIC_CONFIG = BACKEND_ROOT / "alembic.ini"
SEEDED_TABLES = [
    "brands",
    "campaigns",
    "campaign_brands",
    "influencers",
    "influencer_platforms",
    "influencer_audience_snapshots",
    "influencer_contacts",
    "deals",
    "deliverables",
    "compensation_items",
    "import_sessions",
    "stored_files",
    "job_records",
    "templates",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Seed persistent local mock data into the configured SQLite database."
    )
    parser.add_argument(
        "--sql-path",
        type=Path,
        default=DEFAULT_SQL_PATH,
        help=f"SQL seed file to execute. Defaults to {DEFAULT_SQL_PATH}.",
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip alembic upgrade before applying seed data.",
    )
    parser.add_argument(
        "--database-url",
        help="Override DATABASE_URL for this seed run, for example sqlite:////tmp/irm.db.",
    )
    return parser.parse_args()


def configure_database_url(database_url: str | None) -> str:
    if database_url:
        os.environ["DATABASE_URL"] = database_url
        get_settings.cache_clear()
    return get_settings().database_url


def run_migrations() -> None:
    config = Config(str(DEFAULT_ALEMBIC_CONFIG))
    command.upgrade(config, "head")


def sqlite_path_from_url(database_url: str) -> Path:
    parsed = urlparse(database_url)
    if parsed.scheme != "sqlite":
        raise ValueError("Mock SQL seeding currently supports sqlite DATABASE_URL values only.")
    if parsed.path in {"", "/:memory:"}:
        raise ValueError("Mock SQL seeding requires a file-backed sqlite database, not :memory:.")
    if database_url.startswith("sqlite:////"):
        return Path(unquote(parsed.path)).expanduser()
    if database_url.startswith("sqlite:///"):
        return Path(unquote(database_url.removeprefix("sqlite:///"))).expanduser()
    if parsed.netloc:
        path = f"//{parsed.netloc}{parsed.path}"
    else:
        path = parsed.path
    return Path(unquote(path)).expanduser()


def apply_sql(database_url: str, sql_path: Path) -> dict[str, int]:
    resolved_sql_path = sql_path.resolve()
    if not resolved_sql_path.exists():
        raise FileNotFoundError(f"Seed SQL file not found: {resolved_sql_path}")

    db_path = sqlite_path_from_url(database_url)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    sql = resolved_sql_path.read_text(encoding="utf-8")
    with sqlite3.connect(db_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(sql)
        return {
            table: connection.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            for table in SEEDED_TABLES
        }


def main() -> None:
    args = parse_args()
    database_url = configure_database_url(args.database_url)

    if not args.skip_migrations:
        run_migrations()

    counts = apply_sql(database_url, args.sql_path)
    print(f"Seeded mock data into {database_url}")
    for table in SEEDED_TABLES:
        print(f"{table}: {counts[table]}")
    print("Campaign list: http://localhost:5173/campaigns")
    print("Primary seeded campaign: 22222222-2222-2222-2222-222222222221")


if __name__ == "__main__":
    main()
