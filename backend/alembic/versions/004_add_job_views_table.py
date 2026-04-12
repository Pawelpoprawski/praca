"""add job_views table

Revision ID: 004_job_views
Revises: 003_saved_jobs
Create Date: 2026-02-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "004_job_views"
down_revision: Union[str, None] = "003_saved_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_views",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "job_offer_id",
            sa.String(36),
            sa.ForeignKey("job_offers.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "viewed_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_job_views_user_job",
        "job_views",
        ["user_id", "job_offer_id"],
    )
    op.create_index(
        "idx_job_views_user_viewed",
        "job_views",
        ["user_id", "viewed_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_job_views_user_viewed", table_name="job_views")
    op.drop_index("idx_job_views_user_job", table_name="job_views")
    op.drop_table("job_views")
