"""Aggregated search-term counter.

Instead of logging every search as a row (timestamp-heavy SearchLog), we keep a
single row per *normalized* query (lowercased + stripped) and bump a counter. This
keeps the table tiny no matter how many searches happen.
"""
from datetime import datetime

from sqlalchemy import String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class SearchTermCount(Base):
    __tablename__ = "search_term_counts"

    term: Mapped[str] = mapped_column(String(255), primary_key=True)
    count: Mapped[int] = mapped_column(Integer, nullable=False, default=1, server_default="1")
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
