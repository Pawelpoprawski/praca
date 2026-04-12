import uuid
import math
import os
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Request, UploadFile, File, HTTPException, Query, status
from app.database import get_db
from app.dependencies import get_current_worker
from app.config import get_settings
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError
from app.core.rate_limit import limiter
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.models.employer_profile import EmployerProfile
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.cv_file import CVFile
from app.models.cv_database import CVDatabase
from app.models.saved_job import SavedJob
from app.models.job_view import JobView
from app.models.category import Category
from app.schemas.worker import WorkerProfileUpdate, WorkerProfileResponse, CVConsentRequest
from app.schemas.application import ApplyRequest, ApplicationResponse
from app.schemas.saved_job import SavedJobResponse, SavedJobCheckResponse, QuickApplyRequest
from app.schemas.job import JobListResponse, CompanyBrief, CategoryBrief
from app.schemas.common import PaginatedResponse, MessageResponse
from app.services.email import send_application_notification
from app.services.notifications import create_notification
from app.services.activity_logger import log_activity

router = APIRouter(prefix="/worker", tags=["Panel pracownika"])
settings = get_settings()


@router.get("/profile", response_model=WorkerProfileResponse)
async def get_profile(
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Pobierz profil pracownika."""
    result = await db.execute(
        select(WorkerProfile)
        .options(selectinload(WorkerProfile.active_cv))
        .where(WorkerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Profil nie istnieje")

    return WorkerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        canton=profile.canton,
        work_permit=profile.work_permit,
        experience_years=profile.experience_years,
        bio=profile.bio,
        languages=profile.languages or [],
        skills=profile.skills or [],
        desired_salary_min=profile.desired_salary_min,
        desired_salary_max=profile.desired_salary_max,
        available_from=profile.available_from,
        industry=profile.industry,
        has_cv=profile.active_cv is not None,
        cv_filename=profile.active_cv.original_filename if profile.active_cv else None,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone=current_user.phone,
        created_at=profile.created_at,
    )


@router.put("/profile", response_model=WorkerProfileResponse)
async def update_profile(
    data: WorkerProfileUpdate,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Aktualizuj profil pracownika."""
    result = await db.execute(
        select(WorkerProfile)
        .options(selectinload(WorkerProfile.active_cv))
        .where(WorkerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Profil nie istnieje")

    # Aktualizuj dane użytkownika
    if data.first_name is not None:
        current_user.first_name = data.first_name
    if data.last_name is not None:
        current_user.last_name = data.last_name
    if data.phone is not None:
        current_user.phone = data.phone

    # Aktualizuj profil
    profile_fields = [
        "canton", "work_permit", "experience_years", "bio",
        "languages", "skills", "desired_salary_min", "desired_salary_max",
        "available_from", "industry",
    ]
    for field in profile_fields:
        value = getattr(data, field, None)
        if value is not None:
            # Serializuj obiekty Pydantic na dicts dla kolumn JSON
            if field == "languages" and value is not None:
                value = [v.model_dump() if hasattr(v, "model_dump") else v for v in value]
            setattr(profile, field, value)

    return WorkerProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        canton=profile.canton,
        work_permit=profile.work_permit,
        experience_years=profile.experience_years,
        bio=profile.bio,
        languages=profile.languages or [],
        skills=profile.skills or [],
        desired_salary_min=profile.desired_salary_min,
        desired_salary_max=profile.desired_salary_max,
        available_from=profile.available_from,
        industry=profile.industry,
        has_cv=profile.active_cv is not None,
        cv_filename=profile.active_cv.original_filename if profile.active_cv else None,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        email=current_user.email,
        phone=current_user.phone,
        created_at=profile.created_at,
    )


ALLOWED_CV_MIMES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
}


@router.post("/cv", response_model=MessageResponse)
async def upload_cv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Upload CV (PDF or DOCX, max 5MB)."""
    # Walidacja typu pliku
    mime_type = file.content_type or ""
    if mime_type not in ALLOWED_CV_MIMES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dozwolony format: PDF lub DOCX",
        )

    # Walidacja rozmiaru
    content = await file.read()
    max_size = settings.MAX_CV_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Plik jest za duży. Maksymalny rozmiar: {settings.MAX_CV_SIZE_MB}MB",
        )

    # Zapisz plik z poprawnym rozszerzeniem
    ext = ALLOWED_CV_MIMES[mime_type]
    stored_filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, "cv", stored_filename)
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    with open(file_path, "wb") as f:
        f.write(content)

    # Dezaktywuj poprzednie CV
    old_cvs = await db.execute(
        select(CVFile).where(CVFile.user_id == current_user.id, CVFile.is_active.is_(True))
    )
    for old_cv in old_cvs.scalars().all():
        old_cv.is_active = False

    # Utwórz rekord w DB
    cv_file = CVFile(
        user_id=current_user.id,
        original_filename=file.filename or f"cv{ext}",
        stored_filename=stored_filename,
        file_path=file_path,
        file_size=len(content),
        mime_type=mime_type,
        is_active=True,
    )
    db.add(cv_file)
    await db.flush()

    # Ekstrakcja danych z CV
    from app.services.cv_extractor import extract_text, extract_info_from_text
    try:
        text = extract_text(file_path, mime_type)
        cv_file.extracted_text = text[:50000] if text else None  # limit size
        if text:
            info = extract_info_from_text(text)
            cv_file.extracted_name = info.get("name")
            cv_file.extracted_email = info.get("email")
            cv_file.extracted_phone = info.get("phone")
            cv_file.extracted_languages = info.get("languages") or []
            cv_file.extraction_status = "completed"
        else:
            cv_file.extraction_status = "failed"
    except Exception:
        cv_file.extraction_status = "failed"

    # Deactivate previous CVDatabase entries from worker uploads
    old_cv_dbs = await db.execute(
        select(CVDatabase).where(
            CVDatabase.user_id == current_user.id,
            CVDatabase.cv_file_id.isnot(None),
            CVDatabase.is_active.is_(True),
        )
    )
    for old_entry in old_cv_dbs.scalars().all():
        old_entry.is_active = False

    # Create CVDatabase entry for background AI extraction
    cv_db = CVDatabase(
        user_id=current_user.id,
        cv_file_id=cv_file.id,
        cv_review_id=None,
        full_name=f"{current_user.first_name} {current_user.last_name}".strip() or None,
        email=current_user.email,
        cv_text=cv_file.extracted_text,
        cv_file_path=file_path,
        extraction_status="pending" if cv_file.extracted_text else "failed",
        consent_given=False,  # Worker must consent separately via share flow
    )
    db.add(cv_db)

    await db.flush()
    await log_activity(
        "cv_submitted", f"Worker uploaded CV: {current_user.first_name} {current_user.last_name}",
        entity_type="cv_database", entity_id=cv_db.id,
    )

    # Zaktualizuj profil
    result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
    )
    profile = result.scalar_one_or_none()
    if profile:
        profile.active_cv_id = cv_file.id

    return MessageResponse(message="CV zostało przesłane")


@router.get("/cv-info")
async def get_cv_info(
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Pobierz dane ekstrakcji z aktywnego CV."""
    result = await db.execute(
        select(CVFile).where(
            CVFile.user_id == current_user.id, CVFile.is_active.is_(True)
        )
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise NotFoundError("Brak aktywnego CV")

    return {
        "id": cv.id,
        "original_filename": cv.original_filename,
        "mime_type": cv.mime_type,
        "extraction_status": cv.extraction_status,
        "extracted_name": cv.extracted_name,
        "extracted_email": cv.extracted_email,
        "extracted_phone": cv.extracted_phone,
        "extracted_languages": cv.extracted_languages,
    }


@router.delete("/cv", response_model=MessageResponse)
async def delete_cv(
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Usuń aktywne CV."""
    result = await db.execute(
        select(CVFile).where(CVFile.user_id == current_user.id, CVFile.is_active.is_(True))
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise NotFoundError("Brak aktywnego CV")

    cv.is_active = False

    # Wyczyść referencję w profilu
    profile_result = await db.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if profile:
        profile.active_cv_id = None

    return MessageResponse(message="CV zostało usunięte")


@router.post("/cv-analyze")
async def analyze_cv(
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Analizuj aktywne CV i zwróć mocne/słabe strony oraz wskazówki."""
    result = await db.execute(
        select(CVFile).where(
            CVFile.user_id == current_user.id, CVFile.is_active.is_(True)
        )
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise NotFoundError("Brak aktywnego CV")

    if not cv.extracted_text:
        raise BadRequestError("Nie udało się odczytać tekstu z CV — prześlij plik ponownie")

    from app.services.cv_extractor import analyze_cv_text
    extracted_info = {
        "name": cv.extracted_name,
        "email": cv.extracted_email,
        "phone": cv.extracted_phone,
        "languages": cv.extracted_languages or [],
    }
    analysis = analyze_cv_text(cv.extracted_text, extracted_info)
    return analysis


@router.post("/cv-consent", response_model=MessageResponse)
async def cv_consent(
    data: CVConsentRequest,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Wyraź zgodę na udostępnienie CV rekruterom."""
    result = await db.execute(
        select(CVFile).where(
            CVFile.user_id == current_user.id, CVFile.is_active.is_(True)
        )
    )
    cv = result.scalar_one_or_none()
    if not cv:
        raise NotFoundError("Brak aktywnego CV")

    if not data.consent:
        raise BadRequestError("Wymagana zgoda na udostępnienie CV")

    from datetime import datetime, timezone
    cv.is_shared = True
    cv.job_preferences = data.job_preferences
    cv.shared_at = datetime.now(timezone.utc)

    return MessageResponse(message="CV zostało udostępnione rekruterom")


@router.post("/jobs/{job_id}/apply", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("20/hour")
async def apply_for_job(
    request: Request,
    job_id: str,
    data: ApplyRequest,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Aplikuj na ofertę pracy."""
    # Sprawdź czy oferta istnieje, jest aktywna i nie wygasła
    job_result = await db.execute(
        select(JobOffer).where(
            JobOffer.id == job_id,
            JobOffer.status == "active",
            or_(JobOffer.expires_at.is_(None), JobOffer.expires_at > func.now()),
        )
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Oferta nie istnieje lub jest nieaktywna")

    # Sprawdź czy nie aplikował już
    existing = await db.execute(
        select(Application).where(
            Application.job_offer_id == job_id,
            Application.worker_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Już aplikowałeś na tę ofertę")

    # Pobierz aktywne CV
    cv_result = await db.execute(
        select(CVFile).where(
            CVFile.user_id == current_user.id, CVFile.is_active.is_(True)
        )
    )
    active_cv = cv_result.scalar_one_or_none()

    application = Application(
        job_offer_id=job_id,
        worker_id=current_user.id,
        cv_file_id=active_cv.id if active_cv else None,
        cover_letter=data.cover_letter,
        status="sent",
    )
    db.add(application)

    # Notify employer about new application
    job_with_employer = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer).selectinload(EmployerProfile.user))
        .where(JobOffer.id == job_id)
    )
    job_detail = job_with_employer.scalar_one_or_none()
    if job_detail and job_detail.employer and job_detail.employer.user:
        employer_user = job_detail.employer.user
        send_application_notification(
            employer_email=employer_user.email,
            employer_name=employer_user.first_name,
            job_title=job_detail.title,
            applicant_name=f"{current_user.first_name} {current_user.last_name}",
        )
        # In-app notification for employer
        await create_notification(
            db=db,
            user_id=employer_user.id,
            type="application_received",
            title="Nowa aplikacja",
            message=f"Nowa aplikacja na ofertę \"{job_detail.title}\" od {current_user.full_name}",
            related_entity_type="application",
            related_entity_id=application.id,
        )

    return MessageResponse(message="Aplikacja została wysłana")


@router.get("/applications", response_model=PaginatedResponse[ApplicationResponse])
async def list_applications(
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista moich aplikacji."""
    query = (
        select(Application)
        .options(selectinload(Application.job_offer).selectinload(JobOffer.employer))
        .where(Application.worker_id == current_user.id)
        .order_by(Application.created_at.desc())
    )

    count_query = select(func.count()).select_from(
        select(Application).where(Application.worker_id == current_user.id).subquery()
    )
    total = await db.scalar(count_query)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    applications = result.scalars().all()

    response_data = []
    for app in applications:
        response_data.append(ApplicationResponse(
            id=app.id,
            job_offer_id=app.job_offer_id,
            status=app.status,
            cover_letter=app.cover_letter,
            created_at=app.created_at,
            updated_at=app.updated_at,
            job_title=app.job_offer.title if app.job_offer else None,
            company_name=app.job_offer.employer.company_name if app.job_offer and app.job_offer.employer else None,
        ))

    return PaginatedResponse(
        data=response_data,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


# ─── Saved Jobs (Ulubione) ───────────────────────────────────────────────────


def _build_job_list_response(job: JobOffer) -> JobListResponse:
    """Helper: build JobListResponse from a JobOffer ORM instance."""
    employer_brief = None
    if job.employer:
        employer_brief = CompanyBrief(
            id=job.employer.id,
            company_name=job.employer.company_name,
            company_slug=job.employer.company_slug,
            logo_url=job.employer.logo_url if hasattr(job.employer, "logo_url") else None,
            is_verified=job.employer.is_verified if hasattr(job.employer, "is_verified") else False,
        )
    category_brief = None
    if job.category:
        category_brief = CategoryBrief(
            id=job.category.id,
            name=job.category.name,
            slug=job.category.slug,
            icon=job.category.icon if hasattr(job.category, "icon") else None,
        )
    return JobListResponse(
        id=job.id,
        title=job.title,
        canton=job.canton,
        city=job.city,
        contract_type=job.contract_type,
        salary_min=job.salary_min,
        salary_max=job.salary_max,
        salary_type=job.salary_type,
        salary_currency=job.salary_currency,
        is_remote=job.is_remote,
        is_featured=job.is_featured,
        published_at=job.published_at,
        employer=employer_brief,
        category=category_brief,
    )


@router.post("/saved-jobs/{job_id}", response_model=MessageResponse)
async def toggle_saved_job(
    job_id: str,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Zapisz lub usuń ofertę z ulubionych (toggle)."""
    # Sprawdź czy oferta istnieje
    job_result = await db.execute(
        select(JobOffer).where(JobOffer.id == job_id)
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Oferta nie istnieje")

    # Sprawdź czy już zapisana
    existing = await db.execute(
        select(SavedJob).where(
            SavedJob.user_id == current_user.id,
            SavedJob.job_offer_id == job_id,
        )
    )
    saved = existing.scalar_one_or_none()

    if saved:
        await db.delete(saved)
        return MessageResponse(message="Oferta usunięta z ulubionych")
    else:
        new_saved = SavedJob(
            user_id=current_user.id,
            job_offer_id=job_id,
        )
        db.add(new_saved)
        return MessageResponse(message="Oferta zapisana w ulubionych")


@router.get("/saved-jobs", response_model=PaginatedResponse[SavedJobResponse])
async def list_saved_jobs(
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista zapisanych ofert."""
    count_query = select(func.count()).select_from(
        select(SavedJob).where(SavedJob.user_id == current_user.id).subquery()
    )
    total = await db.scalar(count_query)

    query = (
        select(SavedJob)
        .options(
            selectinload(SavedJob.job_offer)
            .selectinload(JobOffer.employer),
            selectinload(SavedJob.job_offer)
            .selectinload(JobOffer.category),
        )
        .where(SavedJob.user_id == current_user.id)
        .order_by(SavedJob.created_at.desc())
        .offset((page - 1) * per_page)
        .limit(per_page)
    )
    result = await db.execute(query)
    saved_jobs = result.scalars().all()

    response_data = []
    for sj in saved_jobs:
        job_response = _build_job_list_response(sj.job_offer) if sj.job_offer else None
        response_data.append(SavedJobResponse(
            id=sj.id,
            job_offer_id=sj.job_offer_id,
            created_at=sj.created_at,
            job=job_response,
        ))

    return PaginatedResponse(
        data=response_data,
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/saved-jobs/check/{job_id}", response_model=SavedJobCheckResponse)
async def check_saved_job(
    job_id: str,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Sprawdź czy oferta jest zapisana."""
    result = await db.execute(
        select(SavedJob).where(
            SavedJob.user_id == current_user.id,
            SavedJob.job_offer_id == job_id,
        )
    )
    saved = result.scalar_one_or_none()
    return SavedJobCheckResponse(is_saved=saved is not None)


# ─── Quick Apply ──────────────────────────────────────────────────────────────


@router.post("/quick-apply/{job_id}", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def quick_apply(
    job_id: str,
    data: QuickApplyRequest,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Szybka aplikacja na ofertę z użyciem danych z profilu i aktywnego CV."""
    # Sprawdź czy oferta istnieje, jest aktywna i nie wygasła
    job_result = await db.execute(
        select(JobOffer).where(
            JobOffer.id == job_id,
            JobOffer.status == "active",
            or_(JobOffer.expires_at.is_(None), JobOffer.expires_at > func.now()),
        )
    )
    job = job_result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Oferta nie istnieje lub jest nieaktywna")

    # Sprawdź czy nie aplikował już
    existing = await db.execute(
        select(Application).where(
            Application.job_offer_id == job_id,
            Application.worker_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Już aplikowałeś na tę ofertę")

    # Sprawdź czy pracownik ma aktywne CV
    profile_result = await db.execute(
        select(WorkerProfile)
        .options(selectinload(WorkerProfile.active_cv))
        .where(WorkerProfile.user_id == current_user.id)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile or not profile.active_cv_id:
        raise BadRequestError("Aby szybko aplikować, musisz mieć aktywne CV w profilu")

    # Utwórz aplikację
    application = Application(
        job_offer_id=job_id,
        worker_id=current_user.id,
        cv_file_id=profile.active_cv_id,
        cover_letter=data.cover_letter,
        status="sent",
    )
    db.add(application)

    # Notify employer
    job_with_employer = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer).selectinload(EmployerProfile.user))
        .where(JobOffer.id == job_id)
    )
    job_detail = job_with_employer.scalar_one_or_none()
    if job_detail and job_detail.employer and job_detail.employer.user:
        employer_user = job_detail.employer.user
        send_application_notification(
            employer_email=employer_user.email,
            employer_name=employer_user.first_name,
            job_title=job_detail.title,
            applicant_name=f"{current_user.first_name} {current_user.last_name}",
        )
        await create_notification(
            db=db,
            user_id=employer_user.id,
            type="application_received",
            title="Nowa aplikacja",
            message=f"Nowa aplikacja na ofertę \"{job_detail.title}\" od {current_user.full_name}",
            related_entity_type="application",
            related_entity_id=application.id,
        )

    return MessageResponse(message="Szybka aplikacja została wysłana")


# ─── Viewed Jobs (Historia przeglądanych) ────────────────────────────────────


@router.get("/viewed-jobs", response_model=list[JobListResponse])
async def list_viewed_jobs(
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
    limit: int = Query(20, ge=1, le=50),
):
    """Lista ostatnio przeglądanych ofert (unikalne, posortowane od najnowszego)."""
    # Podzapytanie: ostatnie wyświetlenie każdej oferty
    subq = (
        select(
            JobView.job_offer_id,
            func.max(JobView.viewed_at).label("last_viewed"),
        )
        .where(JobView.user_id == current_user.id)
        .group_by(JobView.job_offer_id)
        .subquery()
    )

    query = (
        select(JobOffer)
        .join(subq, JobOffer.id == subq.c.job_offer_id)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .where(JobOffer.status == "active")
        .order_by(subq.c.last_viewed.desc())
        .limit(limit)
    )

    result = await db.execute(query)
    jobs = result.scalars().all()

    return [_build_job_list_response(j) for j in jobs]
