import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, Boolean, DateTime, ForeignKey, Text, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class CVFile(Base):
    __tablename__ = "cv_files"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False, index=True,
    )
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    mime_type: Mapped[str] = mapped_column(String(50), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    # Extracted CV data
    extracted_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    extracted_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extracted_email: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    extracted_phone: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    extracted_languages: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)
    extraction_status: Mapped[str] = mapped_column(
        String(20), default="pending", server_default="pending"
    )

    # Sharing with recruiters
    is_shared: Mapped[bool] = mapped_column(Boolean, default=False)
    job_preferences: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    shared_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="cv_files")
