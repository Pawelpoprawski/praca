"""add cv_reviews and cv_database tables

Revision ID: 005_cv_review_db
Revises: 004_job_views
Create Date: 2026-02-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "005_cv_review_db"
down_revision: Union[str, None] = "004_job_views"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # cv_reviews table
    op.create_table(
        "cv_reviews",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("cv_filename", sa.String(255), nullable=False),
        sa.Column("cv_original_filename", sa.String(255), nullable=False, server_default=""),
        sa.Column("cv_text", sa.Text(), nullable=True),
        sa.Column("overall_score", sa.Integer(), nullable=True),
        sa.Column("analysis_json", sa.JSON(), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="analyzed", index=True),
        sa.Column(
            "previous_review_id",
            sa.String(36),
            sa.ForeignKey("cv_reviews.id", ondelete="SET NULL"),
            nullable=True,
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
    )

    # cv_database table
    op.create_table(
        "cv_database",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
        sa.Column(
            "cv_review_id",
            sa.String(36),
            sa.ForeignKey("cv_reviews.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("full_name", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("cv_text", sa.Text(), nullable=True),
        sa.Column("cv_file_path", sa.String(500), nullable=True),
        sa.Column("extracted_data", sa.JSON(), nullable=True),
        sa.Column("job_preferences", sa.Text(), nullable=True),
        sa.Column("available_from", sa.Date(), nullable=True),
        sa.Column("preferred_cantons", sa.JSON(), nullable=True),
        sa.Column("expected_salary_min", sa.Integer(), nullable=True),
        sa.Column("expected_salary_max", sa.Integer(), nullable=True),
        sa.Column("work_mode", sa.String(20), nullable=True),
        sa.Column("languages", sa.JSON(), nullable=True),
        sa.Column("driving_license", sa.String(10), nullable=True),
        sa.Column("additional_notes", sa.Text(), nullable=True),
        sa.Column("consent_given", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("is_active", sa.Boolean(), server_default="true", index=True),
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
    )


def downgrade() -> None:
    op.drop_table("cv_database")
    op.drop_table("cv_reviews")
