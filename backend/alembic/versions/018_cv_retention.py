"""Add retention_status column to cv_reviews for 24h TTL of CV file+text without consent.

Revision ID: 018
Revises: 017
Create Date: 2026-05-13
"""
from alembic import op
import sqlalchemy as sa

revision = "018"
down_revision = "017"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "cv_reviews",
        sa.Column(
            "retention_status",
            sa.String(20),
            server_default="temporary",
            nullable=False,
        ),
    )
    op.create_index(
        "idx_cv_reviews_retention",
        "cv_reviews",
        ["retention_status", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("idx_cv_reviews_retention", table_name="cv_reviews")
    op.drop_column("cv_reviews", "retention_status")
