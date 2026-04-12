from sqlalchemy.ext.asyncio import AsyncSession
from app.models.notification import Notification


async def create_notification(
    db: AsyncSession,
    user_id: str,
    type: str,
    title: str,
    message: str,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
) -> Notification:
    """Utwórz powiadomienie dla użytkownika."""
    notification = Notification(
        user_id=user_id,
        type=type,
        title=title,
        message=message,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
    )
    db.add(notification)
    await db.flush()
    return notification
