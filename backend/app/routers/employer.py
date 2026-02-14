import uuid
import os
import math
from datetime import date, datetime, timedelta, timezone
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
from app.database import get_db
from app.dependencies import get_current_employer
from app.config import get_settings
from app.core.exceptions import NotFoundError, ForbiddenError, QuotaExceededError
from app.core.sanitize import sanitize_html
from app.models.user import User
from app.models.employer_profile import EmployerProfile
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.posting_quota import PostingQuota
from app.models.system_setting import SystemSetting
from app.schemas.job import JobCreateRequest, JobUpdateRequest, JobResponse
from app.schemas.employer import (
    EmployerProfileUpdate, EmployerProfileResponse,
    EmployerDashboard, QuotaResponse,
)
from app.schemas.application import ApplicationStatusUpdate, CandidateResponse
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.email import send_status_change_notification

router = APIRouter(prefix="/employer", tags=["Panel pracodawcy"])
settings = get_settings()


async def _get_employer_profile(user: User, db: AsyncSession) -> EmployerProfile:
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Profil firmy nie istnieje")
    return profile


async def _get_effective_limit(employer_id: str, db: AsyncSession) -> int:
    """Oblicz efektywny limit ogłoszeń dla pracodawcy."""
    result = await db.execute(
        select(PostingQuota).where(PostingQuota.employer_id == employer_id)
    )
    quota = result.scalar_one_or_none()

    if quota and quota.custom_limit is not None:
        return quota.custom_limit
    if quota and quota.monthly_limit is not None:
        return quota.monthly_limit

    # Globalny domyślny
    setting = await db.execute(
        select(SystemSetting).where(SystemSetting.key == "default_monthly_posting_limit")
    )
    sys_setting = setting.scalar_one_or_none()
    return int(sys_setting.value) if sys_setting else 5


# === PROFIL ===

@router.get("/profile", response_model=EmployerProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Pobierz profil firmy."""
    profile = await _get_employer_profile(current_user, db)
    return EmployerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        company_name=profile.company_name,
        company_slug=profile.company_slug,
        description=profile.description,
        logo_url=profile.logo_url,
        website=profile.website,
        industry=profile.industry,
        canton=profile.canton,
        city=profile.city,
        address=profile.address,
        uid_number=profile.uid_number,
        company_size=profile.company_size,
        is_verified=profile.is_verified,
        created_at=profile.created_at,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone=current_user.phone,
    )


@router.put("/profile", response_model=EmployerProfileResponse)
async def update_profile(
    data: EmployerProfileUpdate,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Aktualizuj profil firmy."""
    profile = await _get_employer_profile(current_user, db)

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "description" and value:
            value = sanitize_html(value)
        setattr(profile, field, value)

    return EmployerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        company_name=profile.company_name,
        company_slug=profile.company_slug,
        description=profile.description,
        logo_url=profile.logo_url,
        website=profile.website,
        industry=profile.industry,
        canton=profile.canton,
        city=profile.city,
        address=profile.address,
        uid_number=profile.uid_number,
        company_size=profile.company_size,
        is_verified=profile.is_verified,
        created_at=profile.created_at,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone=current_user.phone,
    )


@router.post("/profile/logo", response_model=MessageResponse)
async def upload_logo(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Upload logo firmy (JPG/PNG, max 2MB)."""
    allowed_types = ["image/jpeg", "image/png", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dozwolone formaty: JPG, PNG, WebP",
        )

    content = await file.read()
    max_size = settings.MAX_LOGO_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plik jest za duży. Maksymalny rozmiar: {settings.MAX_LOGO_SIZE_MB}MB",
        )

    ext = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "png"
    stored_filename = f"{uuid.uuid4()}.{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, "logos", stored_filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(content)

    profile = await _get_employer_profile(current_user, db)
    profile.logo_url = f"/uploads/logos/{stored_filename}"

    return MessageResponse(message="Logo zostało przesłane")


# === DASHBOARD ===

@router.get("/dashboard", response_model=EmployerDashboard)
async def get_dashboard(
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Statystyki pracodawcy."""
    profile = await _get_employer_profile(current_user, db)

    active_jobs = await db.scalar(
        select(func.count()).where(
            JobOffer.employer_id == profile.id, JobOffer.status == "active"
        )
    )

    total_apps = await db.scalar(
        select(func.count())
        .select_from(Application)
        .join(JobOffer)
        .where(JobOffer.employer_id == profile.id)
    )

    new_apps = await db.scalar(
        select(func.count())
        .select_from(Application)
        .join(JobOffer)
        .where(JobOffer.employer_id == profile.id, Application.status == "sent")
    )

    quota_result = await db.execute(
        select(PostingQuota).where(PostingQuota.employer_id == profile.id)
    )
    quota = quota_result.scalar_one_or_none()
    limit = await _get_effective_limit(profile.id, db)

    return EmployerDashboard(
        active_jobs=active_jobs or 0,
        total_applications=total_apps or 0,
        new_applications=new_apps or 0,
        quota_used=quota.used_count if quota else 0,
        quota_limit=limit,
        quota_reset_date=quota.period_end if quota else None,
    )


# === OGŁOSZENIA ===

@router.get("/jobs", response_model=PaginatedResponse[JobResponse])
async def list_my_jobs(
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista moich ogłoszeń."""
    profile = await _get_employer_profile(current_user, db)

    query = (
        select(JobOffer)
        .options(selectinload(JobOffer.category))
        .where(JobOffer.employer_id == profile.id)
    )
    if status_filter:
        query = query.where(JobOffer.status == status_filter)

    query = query.order_by(JobOffer.created_at.desc())

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


@router.post("/jobs", response_model=JobResponse, status_code=status.HTTP_201_CREATED)
async def create_job(
    data: JobCreateRequest,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Dodaj ogłoszenie (sprawdza limit)."""
    profile = await _get_employer_profile(current_user, db)

    # Sprawdź limit
    quota_result = await db.execute(
        select(PostingQuota).where(PostingQuota.employer_id == profile.id)
    )
    quota = quota_result.scalar_one_or_none()
    limit = await _get_effective_limit(profile.id, db)

    if quota and quota.used_count >= limit:
        raise QuotaExceededError(
            f"Wyczerpano limit ogłoszeń ({limit}/miesiąc). "
            f"Reset: {quota.period_end.isoformat()}"
        )

    job = JobOffer(
        employer_id=profile.id,
        category_id=data.category_id,
        title=data.title,
        description=sanitize_html(data.description),
        canton=data.canton,
        city=data.city,
        contract_type=data.contract_type,
        salary_min=data.salary_min,
        salary_max=data.salary_max,
        salary_type=data.salary_type,
        experience_min=data.experience_min,
        work_permit_required=data.work_permit_required,
        work_permit_sponsored=data.work_permit_sponsored,
        is_remote=data.is_remote,
        languages_required=[lr.model_dump() for lr in data.languages_required],
        contact_email=data.contact_email,
        apply_via=data.apply_via,
        external_url=data.external_url,
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db.add(job)

    # Inkrementuj quota
    if quota:
        quota.used_count += 1

    await db.flush()
    await db.refresh(job, ["employer", "category"])

    return job


@router.put("/jobs/{job_id}", response_model=JobResponse)
async def update_job(
    job_id: str,
    data: JobUpdateRequest,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Edytuj ogłoszenie."""
    profile = await _get_employer_profile(current_user, db)

    result = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .where(JobOffer.id == job_id, JobOffer.employer_id == profile.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Ogłoszenie nie zostało znalezione")

    for field, value in data.model_dump(exclude_unset=True).items():
        if field == "description" and value:
            value = sanitize_html(value)
        if field == "languages_required" and value is not None:
            value = [lr.model_dump() if hasattr(lr, "model_dump") else lr for lr in value]
        setattr(job, field, value)

    # Jeśli edytowane po odrzuceniu, wróć do pending
    if job.status == "rejected":
        job.status = "pending"
        job.rejection_reason = None

    return job


@router.delete("/jobs/{job_id}", response_model=MessageResponse)
async def delete_job(
    job_id: str,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Usuń ogłoszenie."""
    profile = await _get_employer_profile(current_user, db)

    result = await db.execute(
        select(JobOffer).where(JobOffer.id == job_id, JobOffer.employer_id == profile.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Ogłoszenie nie zostało znalezione")

    await db.delete(job)
    return MessageResponse(message="Ogłoszenie zostało usunięte")


@router.patch("/jobs/{job_id}/close", response_model=MessageResponse)
async def close_job(
    job_id: str,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Zamknij ogłoszenie."""
    profile = await _get_employer_profile(current_user, db)

    result = await db.execute(
        select(JobOffer).where(JobOffer.id == job_id, JobOffer.employer_id == profile.id)
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Ogłoszenie nie zostało znalezione")

    job.status = "closed"
    return MessageResponse(message="Ogłoszenie zostało zamknięte")


# === KANDYDACI ===

@router.get("/jobs/{job_id}/applications", response_model=list[CandidateResponse])
async def list_candidates(
    job_id: str,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Lista kandydatów na ofertę."""
    profile = await _get_employer_profile(current_user, db)

    # Sprawdź czy oferta należy do tego pracodawcy
    job_result = await db.execute(
        select(JobOffer).where(JobOffer.id == job_id, JobOffer.employer_id == profile.id)
    )
    if not job_result.scalar_one_or_none():
        raise NotFoundError("Ogłoszenie nie zostało znalezione")

    result = await db.execute(
        select(Application)
        .options(selectinload(Application.worker), selectinload(Application.cv_file))
        .where(Application.job_offer_id == job_id)
        .order_by(Application.created_at.desc())
    )
    applications = result.scalars().all()

    return [
        CandidateResponse(
            id=app.id,
            worker_id=app.worker_id,
            status=app.status,
            cover_letter=app.cover_letter,
            created_at=app.created_at,
            worker_name=app.worker.full_name if app.worker else None,
            worker_email=app.worker.email if app.worker else None,
            has_cv=app.cv_file is not None,
            employer_notes=app.employer_notes,
        )
        for app in applications
    ]


@router.put("/applications/{application_id}/status", response_model=MessageResponse)
async def update_application_status(
    application_id: str,
    data: ApplicationStatusUpdate,
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Zmień status aplikacji (viewed, shortlisted, rejected, accepted)."""
    profile = await _get_employer_profile(current_user, db)

    result = await db.execute(
        select(Application)
        .join(JobOffer)
        .where(Application.id == application_id, JobOffer.employer_id == profile.id)
    )
    application = result.scalar_one_or_none()
    if not application:
        raise NotFoundError("Aplikacja nie została znaleziona")

    application.status = data.status
    if data.employer_notes is not None:
        application.employer_notes = data.employer_notes

    # Notify worker about status change
    app_with_details = await db.execute(
        select(Application)
        .options(
            selectinload(Application.worker),
            selectinload(Application.job_offer).selectinload(JobOffer.employer),
        )
        .where(Application.id == application_id)
    )
    app_detail = app_with_details.scalar_one_or_none()
    if app_detail and app_detail.worker and app_detail.job_offer:
        send_status_change_notification(
            worker_email=app_detail.worker.email,
            worker_name=app_detail.worker.first_name,
            job_title=app_detail.job_offer.title,
            company_name=app_detail.job_offer.employer.company_name if app_detail.job_offer.employer else "",
            new_status=data.status,
        )

    return MessageResponse(message=f"Status aplikacji zmieniony na: {data.status}")


# === QUOTA ===

@router.get("/quota", response_model=QuotaResponse)
async def get_quota(
    current_user: User = Depends(get_current_employer),
    db: AsyncSession = Depends(get_db),
):
    """Informacja o limicie ogłoszeń."""
    profile = await _get_employer_profile(current_user, db)

    result = await db.execute(
        select(PostingQuota).where(PostingQuota.employer_id == profile.id)
    )
    quota = result.scalar_one_or_none()
    limit = await _get_effective_limit(profile.id, db)

    if not quota:
        today = date.today()
        return QuotaResponse(
            plan_type="free",
            monthly_limit=limit,
            used_count=0,
            remaining=limit,
            period_start=today,
            period_end=today + timedelta(days=30),
            days_until_reset=30,
            has_custom_limit=False,
        )

    remaining = max(0, limit - quota.used_count)
    days_until = (quota.period_end - date.today()).days

    return QuotaResponse(
        plan_type=quota.plan_type,
        monthly_limit=limit,
        used_count=quota.used_count,
        remaining=remaining,
        period_start=quota.period_start,
        period_end=quota.period_end,
        days_until_reset=max(0, days_until),
        has_custom_limit=quota.custom_limit is not None,
    )
