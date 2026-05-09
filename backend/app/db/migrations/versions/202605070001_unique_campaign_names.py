"""add unique campaign names

Revision ID: 202605070001
Revises: 202605030001
Create Date: 2026-05-07 00:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605070001"
down_revision: str | None = "202605030001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _indexes(table_name: str) -> list[dict[str, object]]:
    return list(sa.inspect(op.get_bind()).get_indexes(table_name))


def _has_unique_name_index() -> bool:
    return any(
        index.get("unique") and index.get("column_names") == ["name"]
        for index in _indexes("campaigns")
    )


def _index_names(table_name: str) -> set[str]:
    return {str(index["name"]) for index in _indexes(table_name)}


def upgrade() -> None:
    if "campaigns" not in _table_names():
        return
    if not _has_unique_name_index():
        op.create_index("uq_campaigns_name", "campaigns", ["name"], unique=True)


def downgrade() -> None:
    if "campaigns" not in _table_names():
        return
    if "uq_campaigns_name" in _index_names("campaigns"):
        op.drop_index("uq_campaigns_name", table_name="campaigns")
