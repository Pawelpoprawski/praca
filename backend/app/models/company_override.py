import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class CompanyOverride(Base):
    """Maps a company name -> recipient email so applications go through our internal form."""

    __tablename__ = "company_overrides"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    # Normalized form (lowercase, stripped) — used for lookup
    company_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    # Original casing for display in admin panel
    company_name: Mapped[str] = mapped_column(String(255), nullable=False)
    apply_email: Mapped[str] = mapped_column(String(255), nullable=False)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
