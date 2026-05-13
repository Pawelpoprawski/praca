"""Add JSON 'queries' column to public_job_alerts (multi-keyword support).

Revision ID: 023
Revises: 022
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa

revision = "023"
down_revision = "022"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "public_job_alerts",
        sa.Column("queries", sa.JSON(), nullable=True),
    )
    # Backfill: copy legacy single `query` into the list so the scheduler stays consistent
    op.execute(
        """
        UPDATE public_job_alerts
        SET queries = json_build_array(LOWER(query))
        WHERE queries IS NULL
        """
    )


def downgrade() -> None:
    op.drop_column("public_job_alerts", "queries")
