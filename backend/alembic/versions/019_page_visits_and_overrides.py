"""Add page_visits and company_overrides tables for /admin-panel.

Revision ID: 019
Revises: 018
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa

revision = "019"
down_revision = "018"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "page_visits",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("ip", sa.String(64), nullable=False),
        sa.Column("path", sa.String(500), nullable=False, server_default="/"),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referrer", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_page_visits_created", "page_visits", ["created_at"])
    op.create_index("idx_page_visits_ip_created", "page_visits", ["ip", "created_at"])

    op.create_table(
        "company_overrides",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("company_key", sa.String(255), nullable=False, unique=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("apply_email", sa.String(255), nullable=False),
        sa.Column("note", sa.String(500), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_company_overrides_company_key", "company_overrides", ["company_key"])


def downgrade() -> None:
    op.drop_index("ix_company_overrides_company_key", table_name="company_overrides")
    op.drop_table("company_overrides")
    op.drop_index("idx_page_visits_ip_created", table_name="page_visits")
    op.drop_index("idx_page_visits_created", table_name="page_visits")
    op.drop_table("page_visits")
