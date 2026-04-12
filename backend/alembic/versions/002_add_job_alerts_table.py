"""add job_alerts table

Revision ID: 002_job_alerts
Revises: 001_notifications
Create Date: 2026-02-15
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "002_job_alerts"
down_revision: Union[str, None] = "001_notifications"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "job_alerts",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column(
            "user_id",
            sa.String(36),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("filters", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("frequency", sa.String(20), nullable=False, server_default="daily"),
        sa.Column("last_sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
        ),
    )
    op.create_index(
        "idx_job_alerts_user_active",
        "job_alerts",
        ["user_id", "is_active"],
    )


def downgrade() -> None:
    op.drop_index("idx_job_alerts_user_active", table_name="job_alerts")
    op.drop_table("job_alerts")
