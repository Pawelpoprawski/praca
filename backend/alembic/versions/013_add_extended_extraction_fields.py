"""Add extended extraction fields.

Revision ID: 013
Revises: 012
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("start_date_text", sa.String(100), nullable=True))
    op.add_column("job_offers", sa.Column("contract_duration", sa.String(100), nullable=True))
    op.add_column("job_offers", sa.Column("per_diem", sa.Integer(), nullable=True))
    op.add_column("job_offers", sa.Column("hours_per_week", sa.Integer(), nullable=True))
    op.add_column("job_offers", sa.Column("accommodation_cost_min", sa.Integer(), nullable=True))
    op.add_column("job_offers", sa.Column("accommodation_cost_max", sa.Integer(), nullable=True))
    op.add_column("job_offers", sa.Column("benefits", sa.JSON(), nullable=True))
    op.add_column("job_offers", sa.Column("education_required", sa.String(200), nullable=True))
    op.add_column("job_offers", sa.Column("responsibilities", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_offers", "responsibilities")
    op.drop_column("job_offers", "education_required")
    op.drop_column("job_offers", "benefits")
    op.drop_column("job_offers", "accommodation_cost_max")
    op.drop_column("job_offers", "accommodation_cost_min")
    op.drop_column("job_offers", "hours_per_week")
    op.drop_column("job_offers", "per_diem")
    op.drop_column("job_offers", "contract_duration")
    op.drop_column("job_offers", "start_date_text")
