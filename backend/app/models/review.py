import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class EmployerReview(Base):
    __tablename__ = "employer_reviews"

    __table_args__ = (
        UniqueConstraint("employer_id", "worker_user_id", name="uq_review_employer_worker"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    employer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employer_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    worker_user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="pending", index=True,
    )  # pending, approved, rejected
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    employer: Mapped["EmployerProfile"] = relationship(back_populates="reviews")
    worker: Mapped["User"] = relationship(back_populates="reviews")
