"""Simple activity logging for admin visibility."""
import logging
from app.database import async_session
from app.models.activity_log import ActivityLog

logger = logging.getLogger(__name__)


async def log_activity(
    event_type: str,
    summary: str,
    entity_type: str | None = None,
    entity_id: str | None = None,
    details: dict | None = None,
    session_factory=None,
):
    """Fire-and-forget activity log entry."""
    try:
        _sf = session_factory or async_session
        async with _sf() as db:
            db.add(ActivityLog(
                event_type=event_type,
                entity_type=entity_type,
                entity_id=entity_id,
                summary=summary,
                details=details,
            ))
            await db.commit()
    except Exception as e:
        logger.warning(f"Failed to log activity: {e}")
