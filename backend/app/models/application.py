import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_offer_id", "worker_id", name="uq_application_job_worker"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    job_offer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("job_offers.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    worker_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    cv_file_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cv_files.id", ondelete="SET NULL"),
    )
    cover_letter: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(
        String(20), default="sent", index=True
    )  # sent, viewed, shortlisted, rejected, accepted
    employer_notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    job_offer: Mapped["JobOffer"] = relationship(back_populates="applications")
    worker: Mapped["User"] = relationship(back_populates="applications")
    cv_file: Mapped["CVFile | None"] = relationship()
