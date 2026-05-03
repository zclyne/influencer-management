"""remove local email tables

Revision ID: 202605010002
Revises: 202605010001
Create Date: 2026-05-01 00:00:02.000000
"""

from collections.abc import Sequence

from alembic import op

revision: str = "202605010002"
down_revision: str | None = "202605010001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    for table_name in (
        "email_thread_links",
        "email_thread_metadata",
        "email_accounts",
    ):
        op.drop_table(table_name, if_exists=True)


def downgrade() -> None:
    # Email state now lives in Gmail labels and a local OAuth secret file.
    # Recreating the removed tables would reintroduce the old source of truth.
    pass
