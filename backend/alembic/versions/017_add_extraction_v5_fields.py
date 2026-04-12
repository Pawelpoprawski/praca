"""Add extraction v5 fields (JOBSPL review).

Revision ID: 017
Revises: 016
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = "017"
down_revision = "016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("mileage_allowance", sa.String(100), nullable=True))
    op.add_column("job_offers", sa.Column("commute_time_paid", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("own_tools_required", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("work_hours_text", sa.String(200), nullable=True))
    op.add_column("job_offers", sa.Column("family_allowance", sa.String(200), nullable=True))
    op.add_column("job_offers", sa.Column("christmas_bonus", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("holiday_bonus", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("shift_bonus", sa.String(100), nullable=True))
    op.add_column("job_offers", sa.Column("work_clothing_provided", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("meal_allowance", sa.String(100), nullable=True))
    op.add_column("job_offers", sa.Column("accommodation_deducted", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("accommodation_per_night", sa.String(100), nullable=True))
    op.add_column("job_offers", sa.Column("stable_project", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("group_car", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("insurance_info", sa.String(200), nullable=True))


def downgrade() -> None:
    op.drop_column("job_offers", "insurance_info")
    op.drop_column("job_offers", "group_car")
    op.drop_column("job_offers", "stable_project")
    op.drop_column("job_offers", "accommodation_per_night")
    op.drop_column("job_offers", "accommodation_deducted")
    op.drop_column("job_offers", "meal_allowance")
    op.drop_column("job_offers", "work_clothing_provided")
    op.drop_column("job_offers", "shift_bonus")
    op.drop_column("job_offers", "holiday_bonus")
    op.drop_column("job_offers", "christmas_bonus")
    op.drop_column("job_offers", "family_allowance")
    op.drop_column("job_offers", "work_hours_text")
    op.drop_column("job_offers", "own_tools_required")
    op.drop_column("job_offers", "commute_time_paid")
    op.drop_column("job_offers", "mileage_allowance")
