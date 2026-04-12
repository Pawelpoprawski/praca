"""add employer_reviews table

Revision ID: 002_employer_reviews
Revises: 001_notifications
Create Date: 2026-02-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_employer_reviews"
down_revision: Union[str, None] = "001_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "employer_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "employer_id",
            sa.String(36),
            sa.ForeignKey("employer_profiles.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "worker_user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="pending",
            index=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "employer_id", "worker_user_id", name="uq_review_employer_worker"
        ),
    )


def downgrade() -> None:
    op.drop_table("employer_reviews")
