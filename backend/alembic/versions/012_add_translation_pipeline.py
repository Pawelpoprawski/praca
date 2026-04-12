"""Add translation pipeline columns to job_offers.

Revision ID: 012
Revises: 011
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa

revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("translation_status", sa.String(20), server_default="none", nullable=False))
    op.add_column("job_offers", sa.Column("translation_attempts", sa.Integer(), server_default="0", nullable=False))

    op.create_index("idx_job_offers_translation_status", "job_offers", ["translation_status"])

    # Backfill: scraped jobs that are already active -> translation completed
    op.execute(
        "UPDATE job_offers SET translation_status = 'completed' "
        "WHERE source_name IS NOT NULL AND status = 'active'"
    )
    # Backfill: scraped jobs still pending -> translation pending
    op.execute(
        "UPDATE job_offers SET translation_status = 'pending' "
        "WHERE source_name IS NOT NULL AND status = 'pending'"
    )


def downgrade() -> None:
    op.drop_index("idx_job_offers_translation_status", table_name="job_offers")
    op.drop_column("job_offers", "translation_attempts")
    op.drop_column("job_offers", "translation_status")
