import uuid
from datetime import date, datetime
from sqlalchemy import String, Integer, Text, Date, DateTime, JSON, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class WorkerProfile(Base):
    __tablename__ = "worker_profiles"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        unique=True, nullable=False,
    )
    canton: Mapped[str | None] = mapped_column(String(50), index=True)
    work_permit: Mapped[str | None] = mapped_column(String(20), index=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    bio: Mapped[str | None] = mapped_column(Text)
    languages: Mapped[dict | None] = mapped_column(JSON, default=list)
    skills: Mapped[dict | None] = mapped_column(JSON, default=list)
    desired_salary_min: Mapped[int | None] = mapped_column(Integer)
    desired_salary_max: Mapped[int | None] = mapped_column(Integer)
    available_from: Mapped[date | None] = mapped_column(Date)
    industry: Mapped[str | None] = mapped_column(String(100))
    active_cv_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("cv_files.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    user: Mapped["User"] = relationship(back_populates="worker_profile")
    active_cv: Mapped["CVFile | None"] = relationship(foreign_keys=[active_cv_id])
