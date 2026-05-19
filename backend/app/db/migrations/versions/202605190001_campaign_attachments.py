"""add campaign attachments

Revision ID: 202605190001
Revises: 202605180001
Create Date: 2026-05-19 00:00:01.000000
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202605190001"
down_revision: str | None = "202605180001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _index_names(table_name: str) -> set[str]:
    return {str(index["name"]) for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    if "campaign_attachments" not in _table_names():
        op.create_table(
            "campaign_attachments",
            sa.Column("id", sa.String(length=36), nullable=False),
            sa.Column("campaign_id", sa.String(length=36), nullable=False),
            sa.Column("file_id", sa.String(length=36), nullable=False),
            sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
            sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
            sa.ForeignKeyConstraint(["campaign_id"], ["campaigns.id"]),
            sa.ForeignKeyConstraint(["file_id"], ["stored_files.id"]),
            sa.PrimaryKeyConstraint("id"),
        )

    indexes = _index_names("campaign_attachments")
    if "ix_campaign_attachment_campaign_id" not in indexes:
        op.create_index(
            "ix_campaign_attachment_campaign_id",
            "campaign_attachments",
            ["campaign_id"],
            unique=False,
        )
    if "ix_campaign_attachment_file_id" not in indexes:
        op.create_index(
            "ix_campaign_attachment_file_id",
            "campaign_attachments",
            ["file_id"],
            unique=False,
        )


def downgrade() -> None:
    if "campaign_attachments" not in _table_names():
        return
    indexes = _index_names("campaign_attachments")
    if "ix_campaign_attachment_file_id" in indexes:
        op.drop_index("ix_campaign_attachment_file_id", table_name="campaign_attachments")
    if "ix_campaign_attachment_campaign_id" in indexes:
        op.drop_index("ix_campaign_attachment_campaign_id", table_name="campaign_attachments")
    op.drop_table("campaign_attachments")
