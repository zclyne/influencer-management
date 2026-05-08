"""add campaign tags

Revision ID: 202605030001
Revises: 202605010002
Create Date: 2026-05-03 00:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605030001"
down_revision: str | None = "202605010002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def upgrade() -> None:
    if "campaigns" not in _table_names():
        return
    if "tags_json" not in _column_names("campaigns"):
        op.add_column("campaigns", sa.Column("tags_json", sa.JSON(), nullable=True))


def downgrade() -> None:
    if "campaigns" not in _table_names():
        return
    if "tags_json" in _column_names("campaigns"):
        op.drop_column("campaigns", "tags_json")
