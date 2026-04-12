"""Add extended extraction fields v2.

Revision ID: 014
Revises: 013
Create Date: 2026-03-01
"""
from alembic import op
import sqlalchemy as sa

revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("salary_gross_net", sa.String(10), nullable=True))
    op.add_column("job_offers", sa.Column("meals_provided", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("accommodation_type", sa.String(100), nullable=True))
    op.add_column("job_offers", sa.Column("accommodation_organized", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("relocation_support", sa.Boolean(), server_default="false", nullable=False))
    op.add_column("job_offers", sa.Column("certifications_required", sa.JSON(), nullable=True))
    op.add_column("job_offers", sa.Column("work_schedule", sa.String(200), nullable=True))
    op.add_column("job_offers", sa.Column("payment_frequency", sa.String(50), nullable=True))
    op.add_column("job_offers", sa.Column("physical_requirements", sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column("job_offers", "physical_requirements")
    op.drop_column("job_offers", "payment_frequency")
    op.drop_column("job_offers", "work_schedule")
    op.drop_column("job_offers", "certifications_required")
    op.drop_column("job_offers", "relocation_support")
    op.drop_column("job_offers", "accommodation_organized")
    op.drop_column("job_offers", "accommodation_type")
    op.drop_column("job_offers", "meals_provided")
    op.drop_column("job_offers", "salary_gross_net")
