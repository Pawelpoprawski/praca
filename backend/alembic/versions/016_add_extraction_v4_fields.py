"""Add extraction v4 fields.

Revision ID: 016
Revises: 015
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = "016"
down_revision = "015"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("overtime_info", sa.String(200), nullable=True))
    op.add_column("job_offers", sa.Column("holiday_days", sa.Integer(), nullable=True))
    op.add_column("job_offers", sa.Column("coordinator_support", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("advance_payment", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("company_vehicle", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("age_preference", sa.String(50), nullable=True))
    op.add_column("job_offers", sa.Column("salary_netto_estimated", sa.Integer(), nullable=True))
    op.add_column("job_offers", sa.Column("tips_included", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("work_location_type", sa.String(50), nullable=True))
    op.add_column("job_offers", sa.Column("trial_period", sa.String(100), nullable=True))


def downgrade() -> None:
    op.drop_column("job_offers", "trial_period")
    op.drop_column("job_offers", "work_location_type")
    op.drop_column("job_offers", "tips_included")
    op.drop_column("job_offers", "salary_netto_estimated")
    op.drop_column("job_offers", "age_preference")
    op.drop_column("job_offers", "company_vehicle")
    op.drop_column("job_offers", "advance_payment")
    op.drop_column("job_offers", "coordinator_support")
    op.drop_column("job_offers", "holiday_days")
    op.drop_column("job_offers", "overtime_info")
