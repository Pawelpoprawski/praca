import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base


class PageVisit(Base):
    __tablename__ = "page_visits"
    __table_args__ = (
        Index("idx_page_visits_created", "created_at"),
        Index("idx_page_visits_ip_created", "ip", "created_at"),
    )

    id: Mapped[str] = mapped_column(
        String(36), primary_key=True, default=lambda: str(uuid.uuid4())
    )
    ip: Mapped[str] = mapped_column(String(64), nullable=False)
    path: Mapped[str] = mapped_column(String(500), nullable=False, default="/")
    user_agent: Mapped[str | None] = mapped_column(Text, nullable=True)
    referrer: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )
