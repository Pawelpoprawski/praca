from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, status
from app.database import get_db
from app.dependencies import get_current_worker
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.user import User
from app.models.job_alert import JobAlert
from app.schemas.job_alert import (
    JobAlertCreate,
    JobAlertUpdate,
    JobAlertResponse,
    JobAlertList,
    JobAlertFilters,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/worker/job-alerts", tags=["Alerty o pracy"])

MAX_ALERTS = 5


@router.post("", response_model=JobAlertResponse, status_code=status.HTTP_201_CREATED)
async def create_job_alert(
    data: JobAlertCreate,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Utwórz nowy alert o pracy (max 5)."""
    # Check limit
    count_query = select(func.count()).select_from(
        select(JobAlert).where(JobAlert.user_id == current_user.id).subquery()
    )
    count = await db.scalar(count_query)
    if count >= MAX_ALERTS:
        raise BadRequestError(
            f"Osiągnięto limit {MAX_ALERTS} alertów. Usuń istniejący alert, aby dodać nowy."
        )

    alert = JobAlert(
        user_id=current_user.id,
        name=data.name,
        filters=data.filters.model_dump(),
        frequency=data.frequency,
    )
    db.add(alert)
    await db.flush()

    return JobAlertResponse(
        id=alert.id,
        name=alert.name,
        filters=JobAlertFilters(**alert.filters),
        is_active=alert.is_active,
        frequency=alert.frequency,
        last_sent_at=alert.last_sent_at,
        created_at=alert.created_at,
    )


@router.get("", response_model=JobAlertList)
async def list_job_alerts(
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Lista alertów użytkownika."""
    result = await db.execute(
        select(JobAlert)
        .where(JobAlert.user_id == current_user.id)
        .order_by(JobAlert.created_at.desc())
    )
    alerts = result.scalars().all()

    return JobAlertList(
        alerts=[
            JobAlertResponse(
                id=a.id,
                name=a.name,
                filters=JobAlertFilters(**(a.filters or {})),
                is_active=a.is_active,
                frequency=a.frequency,
                last_sent_at=a.last_sent_at,
                created_at=a.created_at,
            )
            for a in alerts
        ],
        count=len(alerts),
        max_alerts=MAX_ALERTS,
    )


@router.put("/{alert_id}", response_model=JobAlertResponse)
async def update_job_alert(
    alert_id: str,
    data: JobAlertUpdate,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Edytuj alert."""
    result = await db.execute(
        select(JobAlert).where(
            JobAlert.id == alert_id, JobAlert.user_id == current_user.id
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Alert nie istnieje")

    if data.name is not None:
        alert.name = data.name
    if data.filters is not None:
        alert.filters = data.filters.model_dump()
    if data.frequency is not None:
        alert.frequency = data.frequency

    return JobAlertResponse(
        id=alert.id,
        name=alert.name,
        filters=JobAlertFilters(**(alert.filters or {})),
        is_active=alert.is_active,
        frequency=alert.frequency,
        last_sent_at=alert.last_sent_at,
        created_at=alert.created_at,
    )


@router.delete("/{alert_id}", response_model=MessageResponse)
async def delete_job_alert(
    alert_id: str,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Usuń alert."""
    result = await db.execute(
        select(JobAlert).where(
            JobAlert.id == alert_id, JobAlert.user_id == current_user.id
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Alert nie istnieje")

    await db.delete(alert)
    return MessageResponse(message="Alert został usunięty")


@router.patch("/{alert_id}/toggle", response_model=JobAlertResponse)
async def toggle_job_alert(
    alert_id: str,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Włącz/wyłącz alert."""
    result = await db.execute(
        select(JobAlert).where(
            JobAlert.id == alert_id, JobAlert.user_id == current_user.id
        )
    )
    alert = result.scalar_one_or_none()
    if not alert:
        raise NotFoundError("Alert nie istnieje")

    alert.is_active = not alert.is_active

    return JobAlertResponse(
        id=alert.id,
        name=alert.name,
        filters=JobAlertFilters(**(alert.filters or {})),
        is_active=alert.is_active,
        frequency=alert.frequency,
        last_sent_at=alert.last_sent_at,
        created_at=alert.created_at,
    )
