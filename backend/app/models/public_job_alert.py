"""Public (no-login) email alert: weekly digest of new job offers matching a search query."""
import secrets
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Index, JSON, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _gen_token() -> str:
    return secrets.token_urlsafe(32)


class PublicJobAlert(Base):
    __tablename__ = "public_job_alerts"
    __table_args__ = (
        Index("idx_public_alerts_email_query", "email", "query_key"),
        Index("idx_public_alerts_last_sent", "last_sent_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # Normalized lowercase comma-joined keywords — used as dedup key with email
    query_key: Mapped[str] = mapped_column(String(255), nullable=False)
    # Original casing comma-joined keywords for display in emails ("Monter, Hydraulik")
    query: Mapped[str] = mapped_column(String(255), nullable=False)
    # List of individual keywords (lowercase). One alert can match any of them (OR).
    queries: Mapped[list | None] = mapped_column(JSON, nullable=True)
    unsubscribe_token: Mapped[str] = mapped_column(
        String(64), unique=True, nullable=False, default=_gen_token
    )
    last_sent_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
