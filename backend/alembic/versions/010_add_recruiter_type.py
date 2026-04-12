"""Add recruiter_type column to job_offers.

Revision ID: 010
Revises: 009
Create Date: 2026-02-19
"""
from alembic import op
import sqlalchemy as sa

revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("recruiter_type", sa.String(20), nullable=True))

    # Backfill existing offers based on source_name
    op.execute(
        "UPDATE job_offers SET recruiter_type = 'polish' "
        "WHERE source_name IN ('JOBSPL', 'FACHPRACA')"
    )
    op.execute(
        "UPDATE job_offers SET recruiter_type = 'swiss' "
        "WHERE source_name IN ('ROLJOB', 'ADECCO')"
    )


def downgrade() -> None:
    op.drop_column("job_offers", "recruiter_type")
