import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class ApplicationClick(Base):
    __tablename__ = "application_clicks"
    __table_args__ = (
        Index("idx_app_clicks_job", "job_offer_id"),
        Index("idx_app_clicks_type", "click_type"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_offer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_offers.id", ondelete="CASCADE"),
        nullable=False,
    )
    click_type: Mapped[str] = mapped_column(
        String(20), nullable=False
    )  # portal, external, email
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    job_offer: Mapped["JobOffer"] = relationship()
