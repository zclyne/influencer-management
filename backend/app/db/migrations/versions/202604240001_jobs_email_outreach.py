"""add jobs and templates

Revision ID: 202604240001
Revises: 202604160001
Create Date: 2026-04-24 00:00:01.000000
"""
from collections.abc import Sequence

from alembic import op

from app.db.models import Base

revision: str = "202604240001"
down_revision: str | None = "202604160001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    bind = op.get_bind()
    for table_name in (
        "templates",
        "job_records",
    ):
        if table_name in Base.metadata.tables:
            Base.metadata.tables[table_name].drop(bind=bind, checkfirst=True)
