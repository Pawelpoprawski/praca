"""Add public_job_alerts table for no-login weekly email digest.

Revision ID: 021
Revises: 020
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa

revision = "021"
down_revision = "020"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "public_job_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("query_key", sa.String(255), nullable=False),
        sa.Column("query", sa.String(255), nullable=False),
        sa.Column("unsubscribe_token", sa.String(64), unique=True, nullable=False),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_public_alerts_email_query", "public_job_alerts", ["email", "query_key"])
    op.create_index("idx_public_alerts_last_sent", "public_job_alerts", ["last_sent_at"])

    op.create_table(
        "unsubscribed_emails",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("query", sa.String(255), nullable=True),
        sa.Column("subscribed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("unsubscribed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_unsubscribed_emails_email", "unsubscribed_emails", ["email"])


def downgrade() -> None:
    op.drop_index("idx_unsubscribed_emails_email", table_name="unsubscribed_emails")
    op.drop_table("unsubscribed_emails")
    op.drop_index("idx_public_alerts_last_sent", table_name="public_job_alerts")
    op.drop_index("idx_public_alerts_email_query", table_name="public_job_alerts")
    op.drop_table("public_job_alerts")
