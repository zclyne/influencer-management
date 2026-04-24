"""create mvp tables

Revision ID: 202604160001
Revises:
Create Date: 2026-04-16 00:00:01.000000
"""
from collections.abc import Sequence

from alembic import op

from app.db.models import Base

revision: str = "202604160001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    Base.metadata.create_all(bind=op.get_bind())


def downgrade() -> None:
    Base.metadata.drop_all(bind=op.get_bind())

