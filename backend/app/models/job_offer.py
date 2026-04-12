import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Float, Boolean, Text, DateTime, JSON, ForeignKey, Index, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class JobOffer(Base):
    __tablename__ = "job_offers"
    __table_args__ = (
        Index("idx_job_offers_status_expires", "status", "expires_at"),
        Index("idx_job_offers_featured", "is_featured", "feature_priority"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    employer_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("employer_profiles.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    category_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("categories.id", ondelete="SET NULL"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    canton: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    cantons: Mapped[list | None] = mapped_column(JSON)
    city: Mapped[str | None] = mapped_column(String(100))
    contract_type: Mapped[str] = mapped_column(String(30), nullable=False)
    salary_min: Mapped[float | None] = mapped_column(Float)
    salary_max: Mapped[float | None] = mapped_column(Float)
    salary_type: Mapped[str] = mapped_column(String(20), default="monthly")
    salary_currency: Mapped[str] = mapped_column(String(3), default="CHF")
    experience_min: Mapped[int] = mapped_column(Integer, default=0)
    work_permit_required: Mapped[str | None] = mapped_column(String(20))
    work_permit_sponsored: Mapped[bool] = mapped_column(Boolean, default=False)
    is_remote: Mapped[str] = mapped_column(String(20), default="no")
    languages_required: Mapped[dict | None] = mapped_column(JSON, default=list)
    car_required: Mapped[bool] = mapped_column(Boolean, default=False)
    driving_license_required: Mapped[bool] = mapped_column(Boolean, default=False)
    own_tools_required: Mapped[bool] = mapped_column(Boolean, default=False)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    apply_via: Mapped[str] = mapped_column(String(20), default="portal")
    external_url: Mapped[str | None] = mapped_column(String(500))
    ai_keywords: Mapped[str | None] = mapped_column(Text)
    ai_extracted: Mapped[bool] = mapped_column(Boolean, default=False)
    extraction_status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    extraction_version: Mapped[int] = mapped_column(Integer, default=0)
    extraction_attempts: Mapped[int] = mapped_column(Integer, default=0)
    extracted_data: Mapped[dict | None] = mapped_column(JSON)
    match_ready: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    skills: Mapped[list | None] = mapped_column(JSON)
    nice_to_have_skills: Mapped[list | None] = mapped_column(JSON)
    seniority_level: Mapped[str | None] = mapped_column(String(20))
    accommodation_provided: Mapped[bool] = mapped_column(Boolean, default=False)
    accommodation_organized: Mapped[bool] = mapped_column(Boolean, default=False)
    accommodation_deducted: Mapped[bool] = mapped_column(Boolean, default=False)
    relocation_support: Mapped[bool] = mapped_column(Boolean, default=False)
    coordinator_support: Mapped[bool] = mapped_column(Boolean, default=False)
    cv_german_required: Mapped[bool] = mapped_column(Boolean, default=False)
    shift_work: Mapped[bool] = mapped_column(Boolean, default=False)
    industry_tags: Mapped[list | None] = mapped_column(JSON)
    start_date_text: Mapped[str | None] = mapped_column(String(100))
    contract_duration: Mapped[str | None] = mapped_column(String(100))
    trial_period: Mapped[str | None] = mapped_column(String(100))
    per_diem: Mapped[int | None] = mapped_column(Integer)
    hours_per_week: Mapped[int | None] = mapped_column(Integer)
    benefits: Mapped[list | None] = mapped_column(JSON)
    education_required: Mapped[str | None] = mapped_column(String(200))
    responsibilities: Mapped[list | None] = mapped_column(JSON)
    certifications_required: Mapped[list | None] = mapped_column(JSON)
    recruiter_type: Mapped[str | None] = mapped_column(String(20))
    translation_status: Mapped[str] = mapped_column(String(20), default="none", index=True)
    translation_attempts: Mapped[int] = mapped_column(Integer, default=0)
    source_id: Mapped[str | None] = mapped_column(String(100), index=True)
    source_name: Mapped[str | None] = mapped_column(String(50), index=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text)
    views_count: Mapped[int] = mapped_column(Integer, default=0)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)
    feature_priority: Mapped[int] = mapped_column(Integer, default=0)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    employer: Mapped["EmployerProfile"] = relationship(back_populates="job_offers")
    category: Mapped["Category | None"] = relationship(back_populates="job_offers")
    applications: Mapped[list["Application"]] = relationship(
        back_populates="job_offer", cascade="all, delete-orphan"
    )
