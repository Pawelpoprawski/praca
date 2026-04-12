"""Add unified job extraction pipeline columns.

Revision ID: 011
Revises: 010
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa

revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("extraction_status", sa.String(20), server_default="pending", nullable=False))
    op.add_column("job_offers", sa.Column("extraction_version", sa.Integer(), server_default="0", nullable=False))
    op.add_column("job_offers", sa.Column("extraction_attempts", sa.Integer(), server_default="0", nullable=False))
    op.add_column("job_offers", sa.Column("extracted_data", sa.JSON(), nullable=True))
    op.add_column("job_offers", sa.Column("match_ready", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("skills", sa.JSON(), nullable=True))
    op.add_column("job_offers", sa.Column("nice_to_have_skills", sa.JSON(), nullable=True))
    op.add_column("job_offers", sa.Column("seniority_level", sa.String(20), nullable=True))
    op.add_column("job_offers", sa.Column("pensum_min", sa.Integer(), nullable=True))
    op.add_column("job_offers", sa.Column("pensum_max", sa.Integer(), nullable=True))
    op.add_column("job_offers", sa.Column("accommodation_provided", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("shift_work", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("industry_tags", sa.JSON(), nullable=True))

    op.create_index("idx_job_offers_extraction_status", "job_offers", ["extraction_status"])
    op.create_index("idx_job_offers_match_ready", "job_offers", ["match_ready"])

    # Backfill: existing jobs with ai_extracted=True → completed + match_ready
    op.execute(
        "UPDATE job_offers SET extraction_status = 'completed', match_ready = true "
        "WHERE ai_extracted = true"
    )


def downgrade() -> None:
    op.drop_index("idx_job_offers_match_ready", table_name="job_offers")
    op.drop_index("idx_job_offers_extraction_status", table_name="job_offers")
    op.drop_column("job_offers", "industry_tags")
    op.drop_column("job_offers", "shift_work")
    op.drop_column("job_offers", "accommodation_provided")
    op.drop_column("job_offers", "pensum_max")
    op.drop_column("job_offers", "pensum_min")
    op.drop_column("job_offers", "seniority_level")
    op.drop_column("job_offers", "nice_to_have_skills")
    op.drop_column("job_offers", "skills")
    op.drop_column("job_offers", "match_ready")
    op.drop_column("job_offers", "extracted_data")
    op.drop_column("job_offers", "extraction_attempts")
    op.drop_column("job_offers", "extraction_version")
    op.drop_column("job_offers", "extraction_status")
