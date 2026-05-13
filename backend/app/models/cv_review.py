import uuid
from datetime import datetime
from sqlalchemy import String, Boolean, Integer, Text, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CVReview(Base):
    __tablename__ = "cv_reviews"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cv_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    cv_original_filename: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    cv_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    overall_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    analysis_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="analyzed", index=True
    )  # analyzed, improved, submitted_to_db
    retention_status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="temporary", index=True
    )  # temporary (CV file+text deleted after 24h), consented (kept permanently), purged (file+text already deleted by scheduler)
    previous_review_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cv_reviews.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])
    previous_review: Mapped["CVReview | None"] = relationship(
        "CVReview", remote_side=[id], foreign_keys=[previous_review_id]
    )
    cv_database_entry: Mapped["CVDatabase | None"] = relationship(
        "CVDatabase", back_populates="cv_review", uselist=False
    )
