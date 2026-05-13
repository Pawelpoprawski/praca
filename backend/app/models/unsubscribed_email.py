"""Archive of emails that have unsubscribed from public job alerts.

We keep the email after deletion so we can:
  - tell who has historically opted out (analytics)
  - potentially honour 'do not re-subscribe' policy in the future
  - keep an audit trail of opt-outs (GDPR — record of consent withdrawal)
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class UnsubscribedEmail(Base):
    __tablename__ = "unsubscribed_emails"
    __table_args__ = (
        Index("idx_unsubscribed_emails_email", "email"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # What query they were subscribed to (preserved for analytics, e.g. "monter")
    query: Mapped[str | None] = mapped_column(String(255), nullable=True)
    # When they originally subscribed (copied from the deleted alert)
    subscribed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    unsubscribed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
