"""Add application_clicks table for tracking apply button clicks.

Revision ID: 008
Revises: 007
Create Date: 2026-02-17
"""
from alembic import op
import sqlalchemy as sa

revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "application_clicks",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("job_offer_id", sa.String(36), sa.ForeignKey("job_offers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("click_type", sa.String(20), nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("idx_app_clicks_job", "application_clicks", ["job_offer_id"])
    op.create_index("idx_app_clicks_type", "application_clicks", ["click_type"])


def downgrade() -> None:
    op.drop_index("idx_app_clicks_type", "application_clicks")
    op.drop_index("idx_app_clicks_job", "application_clicks")
    op.drop_table("application_clicks")
