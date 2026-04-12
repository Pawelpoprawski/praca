"""Add cantons list and cv_german_required.

Revision ID: 015
Revises: 014
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = "015"
down_revision = "014"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("cantons", sa.JSON(), nullable=True))
    op.add_column("job_offers", sa.Column("cv_german_required", sa.Boolean(), server_default="false", nullable=False))


def downgrade() -> None:
    op.drop_column("job_offers", "cv_german_required")
    op.drop_column("job_offers", "cantons")
