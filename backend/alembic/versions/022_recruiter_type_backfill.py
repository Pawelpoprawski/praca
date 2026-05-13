"""Re-align recruiter_type defaults: ROLJOB -> polish, manual jobs -> polish.

ADECCO remains 'swiss' (Swiss employer), JOBSPL/FACHPRACA stay 'polish'.

Revision ID: 022
Revises: 021
Create Date: 2026-05-13
"""
from alembic import op

revision = "022"
down_revision = "021"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ROLJOB was historically tagged 'swiss' — it's actually a Polish recruiter
    op.execute(
        "UPDATE job_offers SET recruiter_type = 'polish' "
        "WHERE source_name = 'ROLJOB'"
    )
    # Manual employer-posted offers: no source_name and missing recruiter_type
    op.execute(
        "UPDATE job_offers SET recruiter_type = 'polish' "
        "WHERE source_name IS NULL AND recruiter_type IS NULL"
    )


def downgrade() -> None:
    op.execute(
        "UPDATE job_offers SET recruiter_type = 'swiss' "
        "WHERE source_name = 'ROLJOB'"
    )
