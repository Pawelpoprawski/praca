import math
import re
from datetime import datetime, timezone, timedelta, date
from sqlalchemy import select, func, cast, Date
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.dependencies import get_current_admin
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.user import User
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.category import Category
from app.models.posting_quota import PostingQuota
from app.models.system_setting import SystemSetting
from app.models.cv_file import CVFile
from app.schemas.auth import UserResponse
from app.schemas.job import JobResponse
from app.schemas.common import PaginatedResponse, MessageResponse

router = APIRouter(prefix="/admin", tags=["Panel administratora"])


# === DASHBOARD ===

@router.get("/dashboard")
async def dashboard(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Statystyki ogólne."""
    total_users = await db.scalar(select(func.count()).select_from(User))
    total_workers = await db.scalar(
        select(func.count()).where(User.role == "worker")
    )
    total_employers = await db.scalar(
        select(func.count()).where(User.role == "employer")
    )
    total_jobs = await db.scalar(select(func.count()).select_from(JobOffer))
    active_jobs = await db.scalar(
        select(func.count()).where(JobOffer.status == "active")
    )
    pending_jobs = await db.scalar(
        select(func.count()).where(JobOffer.status == "pending")
    )
    total_applications = await db.scalar(
        select(func.count()).select_from(Application)
    )

    return {
        "total_users": total_users or 0,
        "total_workers": total_workers or 0,
        "total_employers": total_employers or 0,
        "total_jobs": total_jobs or 0,
        "active_jobs": active_jobs or 0,
        "pending_jobs": pending_jobs or 0,
        "total_applications": total_applications or 0,
    }


@router.get("/stats/trends")
async def stats_trends(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dzienne statystyki + porównania okresów (7d/14d/30d)."""
    today = date.today()
    start_date = today - timedelta(days=59)  # 30d current + 30d previous

    # Daily new users
    users_q = await db.execute(
        select(
            cast(User.created_at, Date).label("day"),
            func.count().label("cnt"),
        )
        .where(cast(User.created_at, Date) >= start_date)
        .group_by(cast(User.created_at, Date))
    )
    users_by_day = {row.day: row.cnt for row in users_q}

    # Daily new jobs
    jobs_q = await db.execute(
        select(
            cast(JobOffer.created_at, Date).label("day"),
            func.count().label("cnt"),
        )
        .where(cast(JobOffer.created_at, Date) >= start_date)
        .group_by(cast(JobOffer.created_at, Date))
    )
    jobs_by_day = {row.day: row.cnt for row in jobs_q}

    # Daily new applications
    apps_q = await db.execute(
        select(
            cast(Application.created_at, Date).label("day"),
            func.count().label("cnt"),
        )
        .where(cast(Application.created_at, Date) >= start_date)
        .group_by(cast(Application.created_at, Date))
    )
    apps_by_day = {row.day: row.cnt for row in apps_q}

    # Build daily array (last 30 days) with zero-fill
    daily = []
    for i in range(29, -1, -1):
        d = today - timedelta(days=i)
        daily.append({
            "date": d.isoformat(),
            "new_users": users_by_day.get(d, 0),
            "new_jobs": jobs_by_day.get(d, 0),
            "new_applications": apps_by_day.get(d, 0),
        })

    # Period comparisons
    def _compare(by_day: dict, days: int) -> dict:
        current_start = today - timedelta(days=days - 1)
        prev_start = current_start - timedelta(days=days)
        current_total = sum(
            by_day.get(today - timedelta(days=i), 0) for i in range(days)
        )
        prev_total = sum(
            by_day.get(current_start - timedelta(days=i + 1), 0) for i in range(days)
        )
        if prev_total > 0:
            pct = round((current_total - prev_total) / prev_total * 100, 1)
        elif current_total > 0:
            pct = 100.0
        else:
            pct = 0.0
        return {"current": current_total, "previous": prev_total, "pct_change": pct}

    comparisons = {}
    for label, by_day in [("users", users_by_day), ("jobs", jobs_by_day), ("applications", apps_by_day)]:
        comparisons[label] = {
            "7d": _compare(by_day, 7),
            "14d": _compare(by_day, 14),
            "30d": _compare(by_day, 30),
        }

    # Total views
    total_views = await db.scalar(
        select(func.coalesce(func.sum(JobOffer.views_count), 0))
    ) or 0

    return {
        "daily": daily,
        "comparisons": comparisons,
        "total_views": total_views,
    }


# === MODERACJA OGŁOSZEŃ ===

@router.get("/jobs", response_model=PaginatedResponse[JobResponse])
async def list_jobs(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista ogłoszeń (z filtrowaniem po statusie)."""
    query = (
        select(JobOffer)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .order_by(JobOffer.created_at.desc())
    )
    if status_filter:
        query = query.where(JobOffer.status == status_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    jobs = result.scalars().all()

    return PaginatedResponse(
        data=[JobResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.put("/jobs/{job_id}/approve", response_model=MessageResponse)
async def approve_job(
    job_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Zatwierdź ogłoszenie."""
    result = await db.execute(select(JobOffer).where(JobOffer.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Ogłoszenie nie istnieje")

    job.status = "active"
    job.published_at = datetime.now(timezone.utc)
    return MessageResponse(message="Ogłoszenie zostało zatwierdzone")


@router.put("/jobs/{job_id}/reject", response_model=MessageResponse)
async def reject_job(
    job_id: str,
    reason: str = Query(..., min_length=1, description="Powód odrzucenia"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Odrzuć ogłoszenie (z podaniem powodu)."""
    result = await db.execute(select(JobOffer).where(JobOffer.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Ogłoszenie nie istnieje")

    job.status = "rejected"
    job.rejection_reason = reason
    return MessageResponse(message="Ogłoszenie zostało odrzucone")


# === UŻYTKOWNICY ===

@router.get("/users", response_model=PaginatedResponse[UserResponse])
async def list_users(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    role: str | None = Query(None),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista użytkowników."""
    query = select(User).order_by(User.created_at.desc())

    if role:
        query = query.where(User.role == role)
    if q:
        query = query.where(
            User.email.ilike(f"%{q}%")
            | User.first_name.ilike(f"%{q}%")
            | User.last_name.ilike(f"%{q}%")
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    users = result.scalars().all()

    return PaginatedResponse(
        data=[UserResponse.model_validate(u) for u in users],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.put("/users/{user_id}/status", response_model=MessageResponse)
async def toggle_user_status(
    user_id: str,
    is_active: bool = Query(...),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Aktywuj / dezaktywuj użytkownika."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise NotFoundError("Użytkownik nie istnieje")
    if user.id == current_user.id:
        raise BadRequestError("Nie możesz dezaktywować własnego konta")

    user.is_active = is_active
    status_text = "aktywowany" if is_active else "dezaktywowany"
    return MessageResponse(message=f"Użytkownik został {status_text}")


# === KATEGORIE ===

@router.get("/categories")
async def list_categories(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Lista wszystkich kategorii."""
    result = await db.execute(
        select(Category).order_by(Category.sort_order, Category.name)
    )
    categories = result.scalars().all()
    return [
        {
            "id": str(c.id), "name": c.name, "slug": c.slug,
            "icon": c.icon, "sort_order": c.sort_order,
            "is_active": c.is_active, "parent_id": str(c.parent_id) if c.parent_id else None,
        }
        for c in categories
    ]


@router.post("/categories", response_model=MessageResponse)
async def create_category(
    name: str = Query(..., min_length=1, max_length=100),
    icon: str | None = Query(None),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Dodaj kategorię."""
    slug = re.sub(r"[^\w\s-]", "", name.lower().strip())
    slug = re.sub(r"[\s_]+", "-", slug)

    category = Category(name=name, slug=slug, icon=icon)
    db.add(category)
    return MessageResponse(message=f"Kategoria '{name}' została dodana")


@router.put("/categories/{category_id}", response_model=MessageResponse)
async def update_category(
    category_id: str,
    name: str | None = Query(None),
    icon: str | None = Query(None),
    is_active: bool | None = Query(None),
    sort_order: int | None = Query(None),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Edytuj kategorię."""
    result = await db.execute(select(Category).where(Category.id == category_id))
    category = result.scalar_one_or_none()
    if not category:
        raise NotFoundError("Kategoria nie istnieje")

    if name is not None:
        category.name = name
        category.slug = re.sub(r"[\s_]+", "-", re.sub(r"[^\w\s-]", "", name.lower().strip()))
    if icon is not None:
        category.icon = icon
    if is_active is not None:
        category.is_active = is_active
    if sort_order is not None:
        category.sort_order = sort_order

    return MessageResponse(message="Kategoria została zaktualizowana")


# === USTAWIENIA ===

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pobierz ustawienia systemowe."""
    result = await db.execute(select(SystemSetting).order_by(SystemSetting.key))
    settings_list = result.scalars().all()
    return [
        {
            "id": str(s.id), "key": s.key, "value": s.value,
            "value_type": s.value_type, "description": s.description,
        }
        for s in settings_list
    ]


@router.put("/settings", response_model=MessageResponse)
async def update_setting(
    key: str = Query(...),
    value: str = Query(...),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Zmień ustawienie systemowe."""
    result = await db.execute(select(SystemSetting).where(SystemSetting.key == key))
    setting = result.scalar_one_or_none()
    if not setting:
        raise NotFoundError(f"Ustawienie '{key}' nie istnieje")

    setting.value = value
    setting.updated_by = current_user.id
    return MessageResponse(message=f"Ustawienie '{key}' zmienione na '{value}'")


# === QUOTA OVERRIDE ===

@router.put("/employers/{employer_id}/quota", response_model=MessageResponse)
async def override_quota(
    employer_id: str,
    custom_limit: int = Query(..., ge=0),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Nadpisz limit ogłoszeń dla pracodawcy."""
    result = await db.execute(
        select(PostingQuota).where(PostingQuota.employer_id == employer_id)
    )
    quota = result.scalar_one_or_none()
    if not quota:
        raise NotFoundError("Quota nie istnieje dla tego pracodawcy")

    quota.custom_limit = custom_limit
    return MessageResponse(
        message=f"Limit ogłoszeń ustawiony na {custom_limit} dla pracodawcy"
    )


# === BAZA CV ===

@router.get("/cv-stats")
async def cv_stats(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Statystyki CV."""
    total = await db.scalar(select(func.count()).select_from(CVFile))
    active = await db.scalar(
        select(func.count()).where(CVFile.is_active.is_(True))
    )
    completed = await db.scalar(
        select(func.count()).where(CVFile.extraction_status == "completed")
    )
    failed = await db.scalar(
        select(func.count()).where(CVFile.extraction_status == "failed")
    )
    pending = await db.scalar(
        select(func.count()).where(CVFile.extraction_status == "pending")
    )
    return {
        "total": total or 0,
        "active": active or 0,
        "extracted": completed or 0,
        "failed": failed or 0,
        "pending": pending or 0,
    }


@router.get("/cvs")
async def list_cvs(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista wszystkich CV z danymi ekstrakcji."""
    query = (
        select(CVFile)
        .options(selectinload(CVFile.user))
        .order_by(CVFile.created_at.desc())
    )

    if q:
        query = query.join(User, CVFile.user_id == User.id).where(
            User.email.ilike(f"%{q}%")
            | User.first_name.ilike(f"%{q}%")
            | User.last_name.ilike(f"%{q}%")
            | CVFile.extracted_name.ilike(f"%{q}%")
            | CVFile.extracted_email.ilike(f"%{q}%")
        )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    cvs = result.scalars().all()

    data = []
    for cv in cvs:
        user = cv.user
        data.append({
            "id": cv.id,
            "user_id": cv.user_id,
            "user_name": f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
            "user_email": user.email if user else None,
            "original_filename": cv.original_filename,
            "mime_type": cv.mime_type,
            "file_size": cv.file_size,
            "is_active": cv.is_active,
            "extraction_status": cv.extraction_status,
            "extracted_name": cv.extracted_name,
            "extracted_email": cv.extracted_email,
            "extracted_phone": cv.extracted_phone,
            "extracted_languages": cv.extracted_languages,
            "created_at": cv.created_at.isoformat() if cv.created_at else None,
        })

    return {
        "data": data,
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 0,
    }
