"""add has_car column to cv_database

Revision ID: 006_has_car
Revises: 005_cv_review_db
Create Date: 2026-02-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "006_has_car"
down_revision: Union[str, None] = "005_cv_review_db"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("cv_database", sa.Column("has_car", sa.Boolean(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("cv_database", "has_car")
