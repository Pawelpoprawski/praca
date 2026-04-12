import math
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.dependencies import get_current_user
from app.core.exceptions import NotFoundError, ForbiddenError
from app.models.user import User
from app.models.notification import Notification
from app.schemas.notification import NotificationResponse, NotificationList
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/notifications", tags=["Powiadomienia"])


@router.get("", response_model=NotificationList)
async def list_notifications(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista powiadomień bieżącego użytkownika (newest first)."""
    base_filter = Notification.user_id == current_user.id

    count_q = select(func.count()).select_from(
        select(Notification).where(base_filter).subquery()
    )
    total = await db.scalar(count_q) or 0

    query = (
        select(Notification)
        .where(base_filter)
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    notifications = result.scalars().all()

    return NotificationList(
        data=[NotificationResponse.model_validate(n) for n in notifications],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/unread-count")
async def unread_count(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Liczba nieprzeczytanych powiadomień."""
    count = await db.scalar(
        select(func.count()).where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    return {"unread_count": count or 0}


@router.patch("/{notification_id}/read", response_model=MessageResponse)
async def mark_as_read(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Oznacz powiadomienie jako przeczytane."""
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Powiadomienie nie istnieje")
    if notification.user_id != current_user.id:
        raise ForbiddenError("Brak uprawnień")

    notification.is_read = True
    return MessageResponse(message="Powiadomienie oznaczone jako przeczytane")


@router.post("/mark-all-read", response_model=MessageResponse)
async def mark_all_read(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Oznacz wszystkie powiadomienia jako przeczytane."""
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    return MessageResponse(message="Wszystkie powiadomienia oznaczone jako przeczytane")


@router.delete("/{notification_id}", response_model=MessageResponse)
async def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Usuń powiadomienie."""
    result = await db.execute(
        select(Notification).where(Notification.id == notification_id)
    )
    notification = result.scalar_one_or_none()
    if not notification:
        raise NotFoundError("Powiadomienie nie istnieje")
    if notification.user_id != current_user.id:
        raise ForbiddenError("Brak uprawnień")

    await db.delete(notification)
    return MessageResponse(message="Powiadomienie zostało usunięte")
