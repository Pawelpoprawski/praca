import uuid
from datetime import datetime, date
from sqlalchemy import String, Boolean, Integer, Text, Date, DateTime, ForeignKey, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CVDatabase(Base):
    __tablename__ = "cv_database"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    cv_review_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cv_reviews.id", ondelete="CASCADE"), nullable=True, index=True
    )
    cv_file_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cv_files.id", ondelete="SET NULL"), nullable=True, index=True
    )

    # Personal info (from form or AI extraction)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # CV content
    cv_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    cv_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    extracted_data: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    # Job preferences (from form)
    job_preferences: Mapped[str | None] = mapped_column(Text, nullable=True)
    available_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    preferred_cantons: Mapped[list | None] = mapped_column(JSON, nullable=True)
    expected_salary_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    expected_salary_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    work_mode: Mapped[str | None] = mapped_column(
        String(20), nullable=True
    )  # onsite, remote, hybrid
    languages: Mapped[list | None] = mapped_column(JSON, nullable=True)
    driving_license: Mapped[list | None] = mapped_column(JSON, nullable=True)
    has_car: Mapped[bool] = mapped_column(Boolean, default=False)
    additional_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    consent_given: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Normalized AI extraction fields (for matching)
    experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    experience_entries: Mapped[list | None] = mapped_column(JSON, nullable=True)
    category_slugs: Mapped[list | None] = mapped_column(JSON, nullable=True)
    skills: Mapped[list | None] = mapped_column(JSON, nullable=True)
    ai_keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    education: Mapped[list | None] = mapped_column(JSON, nullable=True)
    location: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Extraction pipeline
    extraction_status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending", index=True
    )
    extraction_version: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0"
    )
    match_ready: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=str(False), index=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id])
    cv_review: Mapped["CVReview | None"] = relationship(
        "CVReview", back_populates="cv_database_entry", foreign_keys=[cv_review_id]
    )
    cv_file: Mapped["CVFile | None"] = relationship(
        "CVFile", foreign_keys=[cv_file_id]
    )
