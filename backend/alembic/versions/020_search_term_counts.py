"""Add search_term_counts (aggregated, no per-row timestamp).

Revision ID: 020
Revises: 019
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa

revision = "020"
down_revision = "019"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "search_term_counts",
        sa.Column("term", sa.String(255), primary_key=True),
        sa.Column("count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("search_term_counts")
