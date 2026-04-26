"""rename outreach templates to templates

Revision ID: 202604260001
Revises: 202604240001
Create Date: 2026-04-26 00:00:01.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "202604260001"
down_revision: str | None = "202604240001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _table_names() -> set[str]:
    return set(sa.inspect(op.get_bind()).get_table_names())


def _column_names(table_name: str) -> set[str]:
    return {column["name"] for column in sa.inspect(op.get_bind()).get_columns(table_name)}


def _index_names(table_name: str) -> set[str]:
    return {index["name"] for index in sa.inspect(op.get_bind()).get_indexes(table_name)}


def upgrade() -> None:
    tables = _table_names()
    if "outreach_templates" in tables and "templates" not in tables:
        op.rename_table("outreach_templates", "templates")

    tables = _table_names()
    if "templates" not in tables:
        return

    if "type" not in _column_names("templates"):
        op.add_column(
            "templates",
            sa.Column(
                "type",
                sa.String(length=64),
                nullable=False,
                server_default="OUTREACH_EMAIL",
            ),
        )

    indexes = _index_names("templates")
    if "ix_outreach_templates_archived" in indexes:
        op.drop_index("ix_outreach_templates_archived", table_name="templates")
    if "ix_templates_archived" not in _index_names("templates"):
        op.create_index("ix_templates_archived", "templates", ["is_archived"])


def downgrade() -> None:
    tables = _table_names()
    if "templates" not in tables:
        return

    indexes = _index_names("templates")
    if "ix_templates_archived" in indexes:
        op.drop_index("ix_templates_archived", table_name="templates")
    if "ix_outreach_templates_archived" not in _index_names("templates"):
        op.create_index("ix_outreach_templates_archived", "templates", ["is_archived"])

    if "type" in _column_names("templates"):
        op.drop_column("templates", "type")

    if "outreach_templates" not in _table_names():
        op.rename_table("templates", "outreach_templates")
