"""External (no-login) application — kandydat aplikuje bez konta.

Zapisuje dane wprowadzone w formie + CV (jako plik na dysku) + snapshot oferty
(tytuł i URL) żeby zachować historię nawet jeśli oferta zostanie usunięta.
"""
import uuid
from datetime import datetime

from sqlalchemy import String, DateTime, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class ExternalApplication(Base):
    __tablename__ = "external_applications"

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )

    # FK do oferty — SET NULL żeby zachować rekord aplikacji nawet po usunięciu oferty
    job_offer_id: Mapped[str | None] = mapped_column(
        String(36), ForeignKey("job_offers.id", ondelete="SET NULL"),
        nullable=True, index=True,
    )

    # Snapshot oferty (zachowane nawet po usunięciu/zmianie tytułu oferty)
    job_title: Mapped[str] = mapped_column(String(255), nullable=False)
    job_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    # Dane kandydata
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)

    # CV — oryginalna nazwa + ścieżka na dysku
    cv_original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    cv_storage_path: Mapped[str] = mapped_column(String(500), nullable=False)
    cv_size_bytes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Adresat maila (test recipient lub realny contact_email pracodawcy)
    sent_to: Mapped[str] = mapped_column(String(255), nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True,
    )
