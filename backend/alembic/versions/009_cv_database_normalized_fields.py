"""Add normalized extraction fields to cv_database for matching.

Revision ID: 009
Revises: 008
Create Date: 2026-02-18
"""
from alembic import op
import sqlalchemy as sa

revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Link to cv_files (for Flow 2: worker upload)
    op.add_column("cv_database", sa.Column("cv_file_id", sa.String(36), sa.ForeignKey("cv_files.id", ondelete="SET NULL"), nullable=True))

    # Make cv_review_id nullable (Flow 2 has no CVReview)
    with op.batch_alter_table("cv_database") as batch_op:
        batch_op.alter_column("cv_review_id", existing_type=sa.String(36), nullable=True)

    # Normalized AI extraction fields
    op.add_column("cv_database", sa.Column("experience_years", sa.Integer(), nullable=True))
    op.add_column("cv_database", sa.Column("experience_entries", sa.JSON(), nullable=True))
    op.add_column("cv_database", sa.Column("category_slugs", sa.JSON(), nullable=True))
    op.add_column("cv_database", sa.Column("skills", sa.JSON(), nullable=True))
    op.add_column("cv_database", sa.Column("ai_keywords", sa.Text(), nullable=True))
    op.add_column("cv_database", sa.Column("education", sa.JSON(), nullable=True))
    op.add_column("cv_database", sa.Column("location", sa.String(100), nullable=True))

    # Extraction pipeline status
    op.add_column("cv_database", sa.Column("extraction_status", sa.String(20), server_default="pending", nullable=False))
    op.add_column("cv_database", sa.Column("extraction_version", sa.Integer(), server_default="0", nullable=False))
    op.add_column("cv_database", sa.Column("match_ready", sa.Boolean(), server_default=sa.text("0"), nullable=False))

    # Indexes for extraction pipeline
    op.create_index("idx_cv_db_extraction_status", "cv_database", ["extraction_status"])
    op.create_index("idx_cv_db_match_ready", "cv_database", ["match_ready"])
    op.create_index("idx_cv_db_cv_file_id", "cv_database", ["cv_file_id"])

    # Change driving_license from String(10) to JSON (stores list like ["B","C"])
    with op.batch_alter_table("cv_database") as batch_op:
        batch_op.alter_column(
            "driving_license",
            existing_type=sa.String(10),
            type_=sa.JSON(),
            existing_nullable=True,
            postgresql_using="CASE WHEN driving_license IS NOT NULL THEN json_build_array(driving_license) ELSE NULL END",
        )

    # Backfill: existing rows with extracted_data -> mark as completed
    op.execute(
        "UPDATE cv_database SET extraction_status = 'completed', match_ready = 1 "
        "WHERE extracted_data IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_index("idx_cv_db_cv_file_id", "cv_database")
    op.drop_index("idx_cv_db_match_ready", "cv_database")
    op.drop_index("idx_cv_db_extraction_status", "cv_database")

    op.drop_column("cv_database", "match_ready")
    op.drop_column("cv_database", "extraction_version")
    op.drop_column("cv_database", "extraction_status")
    op.drop_column("cv_database", "location")
    op.drop_column("cv_database", "education")
    op.drop_column("cv_database", "ai_keywords")
    op.drop_column("cv_database", "skills")
    op.drop_column("cv_database", "category_slugs")
    op.drop_column("cv_database", "experience_entries")
    op.drop_column("cv_database", "experience_years")

    with op.batch_alter_table("cv_database") as batch_op:
        batch_op.alter_column(
            "driving_license",
            existing_type=sa.JSON(),
            type_=sa.String(10),
            existing_nullable=True,
        )
        batch_op.alter_column("cv_review_id", existing_type=sa.String(36), nullable=False)

    op.drop_column("cv_database", "cv_file_id")
