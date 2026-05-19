"""add deal attachments

Revision ID: 202605180001
Revises: 202605070001
Create Date: 2026-05-18 00:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605180001"
down_revision: str | None = "202605070001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {str(index["name"]) for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    if "deal_attachments" not in _table_names():
        op.create_table(
            "deal_attachments",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("deal_id", sa.String(length=36), nullable=False),
            sa.Column("file_id", sa.String(length=36), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["deal_id"], ["deals.id"]),
            sa.ForeignKeyConstraint(["file_id"], ["stored_files.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = _index_names("deal_attachments")
    if "ix_deal_attachment_deal_id" not in indexes:
        op.create_index(
            "ix_deal_attachment_deal_id",
            "deal_attachments",
            ["deal_id"],
            unique=False,
        )
    if "ix_deal_attachment_file_id" not in indexes:
        op.create_index(
            "ix_deal_attachment_file_id",
            "deal_attachments",
            ["file_id"],
            unique=False,
        )


def downgrade() -> None:
    if "deal_attachments" not in _table_names():
        return
    indexes = _index_names("deal_attachments")
    if "ix_deal_attachment_file_id" in indexes:
        op.drop_index("ix_deal_attachment_file_id", table_name="deal_attachments")
    if "ix_deal_attachment_deal_id" in indexes:
        op.drop_index("ix_deal_attachment_deal_id", table_name="deal_attachments")
    op.drop_table("deal_attachments")
