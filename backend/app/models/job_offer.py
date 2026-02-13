import uuid
from datetime import datetime
from sqlalchemy import String, Integer, Boolean, Text, DateTime, JSON, ForeignKey, Index, func
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
    city: Mapped[str | None] = mapped_column(String(100))
    contract_type: Mapped[str] = mapped_column(String(30), nullable=False)
    salary_min: Mapped[int | None] = mapped_column(Integer)
    salary_max: Mapped[int | None] = mapped_column(Integer)
    salary_type: Mapped[str] = mapped_column(String(20), default="monthly")
    salary_currency: Mapped[str] = mapped_column(String(3), default="CHF")
    experience_min: Mapped[int] = mapped_column(Integer, default=0)
    work_permit_required: Mapped[str | None] = mapped_column(String(20))
    work_permit_sponsored: Mapped[bool] = mapped_column(Boolean, default=False)
    is_remote: Mapped[str] = mapped_column(String(20), default="no")
    languages_required: Mapped[dict | None] = mapped_column(JSON, default=list)
    contact_email: Mapped[str | None] = mapped_column(String(255))
    apply_via: Mapped[str] = mapped_column(String(20), default="portal")
    external_url: Mapped[str | None] = mapped_column(String(500))
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
