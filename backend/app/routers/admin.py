import asyncio
import csv
import io
import math
import os
import re
from datetime import datetime, timezone, timedelta, date
import sqlalchemy as sa
from sqlalchemy import select, func, cast, Date, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse, FileResponse
from app.config import get_settings
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
from app.models.cv_review import CVReview
from app.models.cv_database import CVDatabase
from app.schemas.auth import UserResponse
from app.schemas.job import JobResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.models.employer_profile import EmployerProfile
from app.models.activity_log import ActivityLog
from app.services.notifications import create_notification

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


# === EKSPORT CSV ===

@router.get("/export/users")
async def export_users_csv(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Eksportuj użytkowników jako CSV."""
    result = await db.execute(
        select(User).order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "email", "first_name", "last_name", "role", "is_active", "created_at"])

    for u in users:
        writer.writerow([
            u.id,
            u.email,
            u.first_name or "",
            u.last_name or "",
            u.role,
            u.is_active,
            u.created_at.isoformat() if u.created_at else "",
        ])

    output.seek(0)
    filename = f"uzytkownicy_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/export/jobs")
async def export_jobs_csv(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Eksportuj ogłoszenia jako CSV."""
    result = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer))
        .order_by(JobOffer.created_at.desc())
    )
    jobs = result.scalars().all()

    # Pre-count applications per job
    app_counts_q = await db.execute(
        select(Application.job_offer_id, func.count().label("cnt"))
        .group_by(Application.job_offer_id)
    )
    app_counts = {row.job_offer_id: row.cnt for row in app_counts_q}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "id", "title", "company", "canton", "salary_from", "salary_to",
        "status", "applications_count", "created_at",
    ])

    for j in jobs:
        writer.writerow([
            j.id,
            j.title,
            j.employer.company_name if j.employer else "",
            j.canton,
            j.salary_min or "",
            j.salary_max or "",
            j.status,
            app_counts.get(j.id, 0),
            j.created_at.isoformat() if j.created_at else "",
        ])

    output.seek(0)
    filename = f"ogloszenia_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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
    result = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer).selectinload(EmployerProfile.user))
        .where(JobOffer.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Ogłoszenie nie istnieje")

    job.status = "active"
    job.published_at = datetime.now(timezone.utc)

    # Powiadomienie dla pracodawcy
    if job.employer and job.employer.user:
        await create_notification(
            db=db,
            user_id=job.employer.user.id,
            type="job_approved",
            title="Ogłoszenie zatwierdzone",
            message=f"Twoje ogłoszenie \"{job.title}\" zostało zatwierdzone i jest teraz widoczne.",
            related_entity_type="job_offer",
            related_entity_id=job.id,
        )

    return MessageResponse(message="Ogłoszenie zostało zatwierdzone")


@router.put("/jobs/{job_id}/reject", response_model=MessageResponse)
async def reject_job(
    job_id: str,
    reason: str = Query(..., min_length=1, description="Powód odrzucenia"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Odrzuć ogłoszenie (z podaniem powodu)."""
    result = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer).selectinload(EmployerProfile.user))
        .where(JobOffer.id == job_id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Ogłoszenie nie istnieje")

    job.status = "rejected"
    job.rejection_reason = reason

    # Powiadomienie dla pracodawcy
    if job.employer and job.employer.user:
        await create_notification(
            db=db,
            user_id=job.employer.user.id,
            type="job_rejected",
            title="Ogłoszenie odrzucone",
            message=f"Twoje ogłoszenie \"{job.title}\" zostało odrzucone. Powód: {reason}",
            related_entity_type="job_offer",
            related_entity_id=job.id,
        )

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


# === BAZA CV REKRUTERSKA ===

@router.get("/cv-database")
async def list_cv_database(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None),
    canton: str | None = Query(None),
    language: str | None = Query(None),
    min_score: int | None = Query(None, ge=1, le=10),
    extraction_status: str | None = Query(None),
    category_slug: str | None = Query(None),
    skill: str | None = Query(None),
    match_ready: bool | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista CV w bazie rekruterskiej z filtrami."""
    query = (
        select(CVDatabase)
        .outerjoin(CVReview, CVDatabase.cv_review_id == CVReview.id)
        .where(CVDatabase.is_active.is_(True))
        .order_by(CVDatabase.created_at.desc())
    )

    if q:
        search = f"%{q}%"
        query = query.where(
            or_(
                CVDatabase.full_name.ilike(search),
                CVDatabase.email.ilike(search),
                CVDatabase.job_preferences.ilike(search),
                CVDatabase.ai_keywords.ilike(search),
                CVDatabase.cv_text.ilike(search),
            )
        )

    if canton:
        # Filter by preferred canton (JSON array contains)
        query = query.where(
            CVDatabase.preferred_cantons.cast(sa.Text).ilike(f"%{canton}%")
        )

    if language:
        query = query.where(
            CVDatabase.languages.cast(sa.Text).ilike(f"%{language}%")
        )

    if min_score:
        query = query.where(CVReview.overall_score >= min_score)

    if extraction_status:
        query = query.where(CVDatabase.extraction_status == extraction_status)

    if category_slug:
        query = query.where(
            CVDatabase.category_slugs.cast(sa.Text).ilike(f"%{category_slug}%")
        )

    if skill:
        query = query.where(
            CVDatabase.skills.cast(sa.Text).ilike(f"%{skill}%")
        )

    if match_ready is not None:
        query = query.where(CVDatabase.match_ready.is_(match_ready))

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    entries = result.scalars().all()

    # Get associated review scores
    review_ids = [e.cv_review_id for e in entries]
    reviews_q = await db.execute(
        select(CVReview.id, CVReview.overall_score)
        .where(CVReview.id.in_(review_ids))
    ) if review_ids else None
    score_map = {}
    if reviews_q:
        score_map = {row.id: row.overall_score for row in reviews_q}

    data = []
    for entry in entries:
        data.append({
            "id": entry.id,
            "full_name": entry.full_name,
            "email": entry.email,
            "phone": entry.phone,
            "job_preferences": entry.job_preferences,
            "available_from": entry.available_from.isoformat() if entry.available_from else None,
            "preferred_cantons": entry.preferred_cantons,
            "expected_salary_min": entry.expected_salary_min,
            "expected_salary_max": entry.expected_salary_max,
            "work_mode": entry.work_mode,
            "languages": entry.languages,
            "driving_license": entry.driving_license,
            "has_car": entry.has_car,
            "overall_score": score_map.get(entry.cv_review_id),
            "is_active": entry.is_active,
            "extraction_status": entry.extraction_status,
            "match_ready": entry.match_ready,
            "category_slugs": entry.category_slugs,
            "skills": entry.skills,
            "location": entry.location,
            "experience_years": entry.experience_years,
            "created_at": entry.created_at.isoformat() if entry.created_at else None,
        })

    return {
        "data": data,
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 0,
    }


@router.get("/cv-database/{entry_id}")
async def get_cv_database_entry(
    entry_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Szczegóły wpisu w bazie CV."""
    result = await db.execute(
        select(CVDatabase).where(CVDatabase.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise NotFoundError("Wpis nie istnieje")

    # Get review score (may be None for Flow 2 entries)
    review = None
    if entry.cv_review_id:
        review_result = await db.execute(
            select(CVReview).where(CVReview.id == entry.cv_review_id)
        )
        review = review_result.scalar_one_or_none()

    return {
        "id": entry.id,
        "full_name": entry.full_name,
        "email": entry.email,
        "phone": entry.phone,
        "cv_text": entry.cv_text,
        "cv_file_path": entry.cv_file_path,
        "extracted_data": entry.extracted_data,
        "job_preferences": entry.job_preferences,
        "available_from": entry.available_from.isoformat() if entry.available_from else None,
        "preferred_cantons": entry.preferred_cantons,
        "expected_salary_min": entry.expected_salary_min,
        "expected_salary_max": entry.expected_salary_max,
        "work_mode": entry.work_mode,
        "languages": entry.languages,
        "driving_license": entry.driving_license,
        "has_car": entry.has_car,
        "additional_notes": entry.additional_notes,
        "consent_given": entry.consent_given,
        "overall_score": review.overall_score if review else None,
        "analysis": review.analysis_json if review else None,
        "is_active": entry.is_active,
        "extraction_status": entry.extraction_status,
        "extraction_version": entry.extraction_version,
        "match_ready": entry.match_ready,
        "experience_years": entry.experience_years,
        "experience_entries": entry.experience_entries,
        "category_slugs": entry.category_slugs,
        "skills": entry.skills,
        "ai_keywords": entry.ai_keywords,
        "education": entry.education,
        "location": entry.location,
        "cv_review_id": entry.cv_review_id,
        "cv_file_id": entry.cv_file_id,
        "user_id": entry.user_id,
        "created_at": entry.created_at.isoformat() if entry.created_at else None,
        "updated_at": entry.updated_at.isoformat() if entry.updated_at else None,
    }


@router.get("/cv-database/{entry_id}/download")
async def download_cv_file(
    entry_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Pobierz plik CV."""
    result = await db.execute(
        select(CVDatabase).where(CVDatabase.id == entry_id)
    )
    entry = result.scalar_one_or_none()
    if not entry:
        raise NotFoundError("Wpis nie istnieje")

    if not entry.cv_file_path:
        raise NotFoundError("Brak pliku CV")

    settings = get_settings()
    file_path = os.path.join(settings.UPLOAD_DIR, entry.cv_file_path)
    if not os.path.exists(file_path):
        raise NotFoundError("Plik CV nie został znaleziony na serwerze")

    filename = entry.full_name or "cv"
    ext = ".pdf" if file_path.endswith(".pdf") else ".docx"
    download_name = f"CV_{filename.replace(' ', '_')}{ext}"

    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type="application/octet-stream",
    )


@router.get("/cv-database-export")
async def export_cv_database_csv(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Eksportuj bazę CV jako CSV."""
    result = await db.execute(
        select(CVDatabase)
        .where(CVDatabase.is_active.is_(True))
        .order_by(CVDatabase.created_at.desc())
    )
    entries = result.scalars().all()

    # Get scores
    review_ids = [e.cv_review_id for e in entries]
    score_map = {}
    if review_ids:
        reviews_q = await db.execute(
            select(CVReview.id, CVReview.overall_score)
            .where(CVReview.id.in_(review_ids))
        )
        score_map = {row.id: row.overall_score for row in reviews_q}

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Imię i nazwisko", "Email", "Telefon", "Szukana praca",
        "Dostępny od", "Kantony", "Wynagrodzenie min", "Wynagrodzenie max",
        "Tryb pracy", "Języki", "Prawo jazdy", "Ocena CV", "Data"
    ])

    for entry in entries:
        cantons_str = ", ".join(entry.preferred_cantons) if entry.preferred_cantons else ""
        langs_str = ", ".join(
            f"{l.get('language', '')} ({l.get('level', '')})"
            for l in (entry.languages or [])
        ) if entry.languages else ""

        writer.writerow([
            entry.full_name or "",
            entry.email or "",
            entry.phone or "",
            (entry.job_preferences or "")[:100],
            entry.available_from.isoformat() if entry.available_from else "",
            cantons_str,
            entry.expected_salary_min or "",
            entry.expected_salary_max or "",
            entry.work_mode or "",
            langs_str,
            entry.driving_license or "",
            score_map.get(entry.cv_review_id, ""),
            entry.created_at.isoformat() if entry.created_at else "",
        ])

    output.seek(0)
    filename = f"baza_cv_{date.today().isoformat()}.csv"
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# === FIRMY (COMPANIES) ===

@router.get("/companies")
async def list_companies(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista firm pracodawców z limitami i statystykami."""
    query = (
        select(EmployerProfile)
        .options(
            selectinload(EmployerProfile.posting_quota),
            selectinload(EmployerProfile.user),
        )
        .order_by(EmployerProfile.created_at.desc())
    )

    if q:
        query = query.where(EmployerProfile.company_name.ilike(f"%{q}%"))

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    companies = result.scalars().all()

    # Count active job postings per employer
    employer_ids = [c.id for c in companies]
    active_counts: dict[str, int] = {}
    if employer_ids:
        active_q = await db.execute(
            select(JobOffer.employer_id, func.count().label("cnt"))
            .where(
                JobOffer.employer_id.in_(employer_ids),
                JobOffer.status == "active",
            )
            .group_by(JobOffer.employer_id)
        )
        active_counts = {row.employer_id: row.cnt for row in active_q}

    data = []
    for c in companies:
        quota = c.posting_quota
        data.append({
            "id": c.id,
            "company_name": c.company_name,
            "company_slug": c.company_slug,
            "logo_url": c.logo_url,
            "is_verified": c.is_verified,
            "created_at": c.created_at.isoformat() if c.created_at else None,
            "active_postings": active_counts.get(c.id, 0),
            "quota": {
                "monthly_limit": quota.monthly_limit if quota else None,
                "used_count": quota.used_count if quota else 0,
                "custom_limit": quota.custom_limit if quota else None,
                "plan_type": quota.plan_type if quota else "free",
                "period_start": quota.period_start.isoformat() if quota and quota.period_start else None,
                "period_end": quota.period_end.isoformat() if quota and quota.period_end else None,
            } if quota else None,
        })

    return {
        "data": data,
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 0,
    }


@router.get("/companies/{company_id}")
async def get_company_detail(
    company_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Szczegóły firmy z limitem i ostatnimi ogłoszeniami."""
    result = await db.execute(
        select(EmployerProfile)
        .options(
            selectinload(EmployerProfile.posting_quota),
            selectinload(EmployerProfile.user),
        )
        .where(EmployerProfile.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Firma nie istnieje")

    # Active postings count
    active_count = await db.scalar(
        select(func.count()).where(
            JobOffer.employer_id == company_id,
            JobOffer.status == "active",
        )
    ) or 0

    # Recent job postings (last 10)
    jobs_result = await db.execute(
        select(JobOffer)
        .where(JobOffer.employer_id == company_id)
        .order_by(JobOffer.created_at.desc())
        .limit(10)
    )
    recent_jobs = jobs_result.scalars().all()

    quota = company.posting_quota
    user = company.user

    return {
        "id": company.id,
        "user_id": company.user_id,
        "company_name": company.company_name,
        "company_slug": company.company_slug,
        "description": company.description,
        "logo_url": company.logo_url,
        "website": company.website,
        "industry": company.industry,
        "canton": company.canton,
        "city": company.city,
        "address": company.address,
        "uid_number": company.uid_number,
        "company_size": company.company_size,
        "is_verified": company.is_verified,
        "created_at": company.created_at.isoformat() if company.created_at else None,
        "user_email": user.email if user else None,
        "user_name": f"{user.first_name or ''} {user.last_name or ''}".strip() if user else None,
        "active_postings": active_count,
        "quota": {
            "id": quota.id,
            "monthly_limit": quota.monthly_limit,
            "used_count": quota.used_count,
            "custom_limit": quota.custom_limit,
            "plan_type": quota.plan_type,
            "period_start": quota.period_start.isoformat() if quota.period_start else None,
            "period_end": quota.period_end.isoformat() if quota.period_end else None,
        } if quota else None,
        "recent_jobs": [
            {
                "id": j.id,
                "title": j.title,
                "status": j.status,
                "views_count": j.views_count,
                "is_featured": j.is_featured,
                "created_at": j.created_at.isoformat() if j.created_at else None,
                "published_at": j.published_at.isoformat() if j.published_at else None,
            }
            for j in recent_jobs
        ],
    }


@router.put("/companies/{company_id}/quota", response_model=MessageResponse)
async def update_company_quota(
    company_id: str,
    monthly_limit: int = Query(..., ge=0),
    custom_limit: int | None = Query(None, ge=0),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Zaktualizuj limit ogłoszeń firmy."""
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Firma nie istnieje")

    # Find or create quota
    quota_result = await db.execute(
        select(PostingQuota).where(PostingQuota.employer_id == company_id)
    )
    quota = quota_result.scalar_one_or_none()

    if quota:
        quota.monthly_limit = monthly_limit
        quota.custom_limit = custom_limit
    else:
        today = date.today()
        quota = PostingQuota(
            employer_id=company_id,
            monthly_limit=monthly_limit,
            custom_limit=custom_limit,
            used_count=0,
            period_start=today.replace(day=1),
            period_end=(today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1),
        )
        db.add(quota)

    return MessageResponse(
        message=f"Limity ogłoszeń zostały zaktualizowane (miesięczny: {monthly_limit}"
        + (f", nadpisany: {custom_limit}" if custom_limit is not None else "")
        + ")"
    )


@router.put("/companies/{company_id}/verify", response_model=MessageResponse)
async def toggle_company_verification(
    company_id: str,
    is_verified: bool = Query(...),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Zmień status weryfikacji firmy."""
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.id == company_id)
    )
    company = result.scalar_one_or_none()
    if not company:
        raise NotFoundError("Firma nie istnieje")

    company.is_verified = is_verified
    status_text = "zweryfikowana" if is_verified else "odznaczona jako niezweryfikowana"
    return MessageResponse(message=f"Firma \"{company.company_name}\" została {status_text}")


# === SCRAPER ===

@router.post("/scraper/sync-jobspl")
async def trigger_jobspl_sync(
    current_user: User = Depends(get_current_admin),
    limit: int | None = Query(None, ge=1, description="Max new jobs to create"),
):
    """Ręcznie uruchom synchronizację ofert z JOBSPL.

    Pobiera oferty z XML feed jobs.pl, przetwarza je przez AI,
    tworzy nowe ogłoszenia i usuwa nieaktualne.
    """
    from app.services.job_scraper import sync_jobspl
    result = await sync_jobspl(limit=limit)
    return result


@router.post("/scraper/sync-fachpraca")
async def trigger_fachpraca_sync(
    current_user: User = Depends(get_current_admin),
    limit: int | None = Query(None, ge=1, description="Max new jobs to create"),
):
    """Ręcznie uruchom synchronizację ofert z FACHPRACA."""
    from app.services.job_scraper import sync_fachpraca
    result = await sync_fachpraca(limit=limit)
    return result


@router.post("/scraper/sync-roljob")
async def trigger_roljob_sync(
    current_user: User = Depends(get_current_admin),
    limit: int | None = Query(None, ge=1, description="Max new jobs to create"),
):
    """Ręcznie uruchom synchronizację ofert z ROLJOB."""
    from app.services.job_scraper import sync_roljob
    result = await sync_roljob(limit=limit)
    return result


@router.post("/scraper/sync-adecco")
async def trigger_adecco_sync(
    current_user: User = Depends(get_current_admin),
    limit: int | None = Query(None, ge=1, description="Max new jobs to create"),
):
    """Ręcznie uruchom synchronizację ofert z ADECCO."""
    from app.services.job_scraper import sync_adecco
    result = await sync_adecco(limit=limit)
    return result


@router.delete("/scraper/purge-source")
async def purge_source(
    source_name: str = Query(..., description="Source name to purge: JOBSPL, FACHPRACA, ROLJOB, ADECCO"),
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Usuń wszystkie oferty z danego źródła."""
    valid_sources = {"JOBSPL", "FACHPRACA", "ROLJOB", "ADECCO"}
    if source_name not in valid_sources:
        raise BadRequestError(f"Nieprawidłowe źródło. Dozwolone: {', '.join(valid_sources)}")

    from app.models.job_offer import JobOffer
    result = await db.execute(
        select(JobOffer).where(JobOffer.source_name == source_name)
    )
    jobs = result.scalars().all()
    count = len(jobs)
    for job in jobs:
        await db.delete(job)
    await db.commit()
    return {"deleted": count, "message": f"Usunięto {count} ofert {source_name}"}


@router.delete("/scraper/purge-jobspl")
async def purge_jobspl(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Usuń wszystkie oferty zaimportowane z JOBSPL (legacy endpoint)."""
    from app.models.job_offer import JobOffer
    result = await db.execute(
        select(JobOffer).where(JobOffer.source_name == "JOBSPL")
    )
    jobs = result.scalars().all()
    count = len(jobs)
    for job in jobs:
        await db.delete(job)
    await db.commit()
    return {"deleted": count, "message": f"Usunięto {count} ofert JOBSPL"}


@router.post("/ai-extract-keywords")
async def ai_extract_keywords(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    job_id: str | None = Query(None, description="Process single job by ID, or all unprocessed if omitted"),
):
    """Uruchom pełną ekstrakcję AI dla ofert pracy.

    Dla scraped jobs: tłumaczy najpierw jeśli trzeba, potem ekstrakcja.
    Używa pipeline'u translate_single_job() + extract_single_job().
    """
    from app.services.job_extraction_service import extract_single_job
    from app.services.job_translation_service import translate_single_job

    if job_id:
        result = await db.execute(
            select(JobOffer).where(JobOffer.id == job_id)
        )
        jobs = result.scalars().all()
    else:
        result = await db.execute(
            select(JobOffer)
            .where(JobOffer.extraction_status.in_(["pending", "failed"]))
            .limit(50)
        )
        jobs = result.scalars().all()

    if not jobs:
        return {"processed": 0, "errors": 0, "message": "Brak ofert do przetworzenia"}

    processed = 0
    errors = 0
    for job in jobs:
        # Scraped jobs: translate first if needed
        if job.source_name and job.translation_status != "completed":
            if not await translate_single_job(job.id):
                errors += 1
                continue

        if await extract_single_job(job.id):
            processed += 1
        else:
            errors += 1

    return {
        "processed": processed,
        "errors": errors,
        "message": f"Przetworzono {processed} ofert, {errors} błędów",
    }


@router.get("/scraper/status")
async def scraper_status(
    current_user: User = Depends(get_current_admin),
):
    """Status scrapera: czas ostatniej synchronizacji, liczniki, następne uruchomienie."""
    from app.services.job_scraper import get_scraper_status, get_source_counts
    status_info = get_scraper_status()
    counts = await get_source_counts()
    return {**status_info, "counts": counts}


# === LOGI AKTYWNOŚCI ===

@router.get("/activity-logs")
async def list_activity_logs(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    event_type: str | None = Query(None),
    entity_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(30, ge=1, le=100),
):
    """Lista logów aktywności z filtrami."""
    query = select(ActivityLog).order_by(ActivityLog.created_at.desc())

    if event_type:
        query = query.where(ActivityLog.event_type == event_type)
    if entity_type:
        query = query.where(ActivityLog.entity_type == entity_type)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    logs = result.scalars().all()

    return {
        "data": [
            {
                "id": log.id,
                "event_type": log.event_type,
                "entity_type": log.entity_type,
                "entity_id": log.entity_id,
                "summary": log.summary,
                "details": log.details,
                "created_at": log.created_at.isoformat() if log.created_at else None,
            }
            for log in logs
        ],
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 0,
    }


# === EKSTRAKCJA AI ===

@router.get("/extraction/status")
async def extraction_status(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Status ekstrakcji AI - ile CV/ofert przetworzonych, w kolejce, z błędami."""
    # CV stats
    cv_pending = await db.scalar(
        select(func.count()).where(CVDatabase.extraction_status == "pending")
    ) or 0
    cv_processing = await db.scalar(
        select(func.count()).where(CVDatabase.extraction_status == "processing")
    ) or 0
    cv_completed = await db.scalar(
        select(func.count()).where(CVDatabase.extraction_status == "completed")
    ) or 0
    cv_failed = await db.scalar(
        select(func.count()).where(CVDatabase.extraction_status == "failed")
    ) or 0

    # Job extraction stats
    job_total = await db.scalar(
        select(func.count()).select_from(JobOffer)
    ) or 0
    job_pending = await db.scalar(
        select(func.count()).where(JobOffer.extraction_status == "pending")
    ) or 0
    job_processing = await db.scalar(
        select(func.count()).where(JobOffer.extraction_status == "processing")
    ) or 0
    job_completed = await db.scalar(
        select(func.count()).where(JobOffer.extraction_status == "completed")
    ) or 0
    job_failed = await db.scalar(
        select(func.count()).where(JobOffer.extraction_status == "failed")
    ) or 0

    # Job translation stats
    trans_pending = await db.scalar(
        select(func.count()).where(JobOffer.translation_status == "pending")
    ) or 0
    trans_processing = await db.scalar(
        select(func.count()).where(JobOffer.translation_status == "processing")
    ) or 0
    trans_completed = await db.scalar(
        select(func.count()).where(JobOffer.translation_status == "completed")
    ) or 0
    trans_failed = await db.scalar(
        select(func.count()).where(JobOffer.translation_status == "failed")
    ) or 0

    return {
        "cv": {
            "pending": cv_pending,
            "processing": cv_processing,
            "completed": cv_completed,
            "failed": cv_failed,
            "total": cv_pending + cv_processing + cv_completed + cv_failed,
        },
        "jobs": {
            "pending": job_pending,
            "processing": job_processing,
            "completed": job_completed,
            "failed": job_failed,
            "total": job_total,
        },
        "translation": {
            "pending": trans_pending,
            "processing": trans_processing,
            "completed": trans_completed,
            "failed": trans_failed,
            "total": trans_pending + trans_processing + trans_completed + trans_failed,
        },
    }


@router.post("/extraction/run-cv")
async def trigger_cv_extraction(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Ręcznie uruchom ekstrakcję AI dla oczekujących CV (w tle)."""
    pending_count = await db.scalar(
        select(func.count()).where(CVDatabase.extraction_status == "pending")
    ) or 0

    if pending_count == 0:
        return {"triggered": False, "pending_count": 0, "message": "Brak CV do przetworzenia"}

    from app.services.cv_extraction_service import process_pending_cv_extractions
    asyncio.create_task(process_pending_cv_extractions())

    return {"triggered": True, "pending_count": pending_count}


@router.post("/extraction/run-jobs")
async def trigger_job_extraction(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Ręcznie uruchom ekstrakcję AI dla ofert (w tle)."""
    pending_count = await db.scalar(
        select(func.count()).where(
            JobOffer.extraction_status.in_(["pending", "failed"]),
        )
    ) or 0

    if pending_count == 0:
        return {"triggered": False, "pending_count": 0, "message": "Brak ofert do przetworzenia"}

    from app.services.job_extraction_service import process_pending_job_extractions
    asyncio.create_task(process_pending_job_extractions())

    return {"triggered": True, "pending_count": pending_count}


@router.post("/extraction/run-translation")
async def trigger_job_translation(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Ręcznie uruchom tłumaczenie AI dla oczekujących ofert scraped (w tle)."""
    pending_count = await db.scalar(
        select(func.count()).where(
            JobOffer.translation_status == "pending",
            JobOffer.source_name.isnot(None),
        )
    ) or 0

    if pending_count == 0:
        return {"triggered": False, "pending_count": 0, "message": "Brak ofert do tłumaczenia"}

    from app.services.job_translation_service import process_pending_job_translations
    asyncio.create_task(process_pending_job_translations())

    return {"triggered": True, "pending_count": pending_count}


# === PRZEGLĄDARKA OFERT AI ===

@router.get("/jobs-browser")
async def jobs_browser(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None),
    canton: str | None = Query(None),
    category_id: str | None = Query(None),
    source_name: str | None = Query(None),
    extraction_status: str | None = Query(None),
    translation_status: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    salary_min: int | None = Query(None),
    salary_max: int | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Przeglądarka ofert z filtrami AI."""
    query = (
        select(JobOffer)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .order_by(JobOffer.created_at.desc())
    )

    if q:
        search = f"%{q}%"
        query = query.where(
            or_(
                JobOffer.title.ilike(search),
                JobOffer.ai_keywords.ilike(search),
                JobOffer.description.ilike(search),
            )
        )

    if canton:
        query = query.where(JobOffer.canton == canton)

    if category_id:
        query = query.where(JobOffer.category_id == category_id)

    if source_name:
        query = query.where(JobOffer.source_name == source_name)

    if extraction_status:
        query = query.where(JobOffer.extraction_status == extraction_status)

    if translation_status:
        query = query.where(JobOffer.translation_status == translation_status)

    if status_filter:
        query = query.where(JobOffer.status == status_filter)

    if salary_min is not None:
        query = query.where(
            or_(JobOffer.salary_max >= salary_min, JobOffer.salary_max.is_(None))
        )

    if salary_max is not None:
        query = query.where(
            or_(JobOffer.salary_min <= salary_max, JobOffer.salary_min.is_(None))
        )

    if date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
            query = query.where(JobOffer.created_at >= dt_from)
        except ValueError:
            pass

    if date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
            query = query.where(JobOffer.created_at <= dt_to)
        except ValueError:
            pass

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    jobs = result.scalars().all()

    return {
        "data": [
            {
                "id": j.id,
                "title": j.title,
                "company_name": j.employer.company_name if j.employer else None,
                "canton": j.canton,
                "city": j.city,
                "category_name": j.category.name if j.category else None,
                "category_id": j.category_id,
                "ai_keywords": j.ai_keywords,
                "extraction_status": j.extraction_status,
                "translation_status": j.translation_status,
                "source_name": j.source_name,
                "salary_min": j.salary_min,
                "salary_max": j.salary_max,
                "salary_type": j.salary_type,
                "status": j.status,
                "views_count": j.views_count,
                "created_at": j.created_at.isoformat() if j.created_at else None,
            }
            for j in jobs
        ],
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 0,
    }
