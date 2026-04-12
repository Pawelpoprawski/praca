import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class JobView(Base):
    __tablename__ = "job_views"
    __table_args__ = (
        Index("idx_job_views_user_job", "user_id", "job_offer_id"),
        Index("idx_job_views_user_viewed", "user_id", "viewed_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    job_offer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_offers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    viewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship()
    job_offer: Mapped["JobOffer"] = relationship()
