"""add ai_keywords and ai_extracted columns to job_offers

Revision ID: 007_ai_keywords
Revises: 006_has_car
Create Date: 2026-02-17
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "007_ai_keywords"
down_revision: Union[str, None] = "006_has_car"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("job_offers", sa.Column("ai_keywords", sa.Text(), nullable=True))
    op.add_column("job_offers", sa.Column("ai_extracted", sa.Boolean(), nullable=False, server_default="0"))


def downgrade() -> None:
    op.drop_column("job_offers", "ai_extracted")
    op.drop_column("job_offers", "ai_keywords")
