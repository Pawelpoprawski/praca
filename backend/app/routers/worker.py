import uuid
import math
import os
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query, status
from app.database import get_db
from app.dependencies import get_current_worker
from app.config import get_settings
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.cv_file import CVFile
from app.schemas.worker import WorkerProfileUpdate, WorkerProfileResponse, CVConsentRequest
from app.schemas.application import ApplyRequest, ApplicationResponse
from app.schemas.common import PaginatedResponse, MessageResponse

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
async def apply_for_job(
    job_id: str,
    data: ApplyRequest,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Aplikuj na ofertę pracy."""
    # Sprawdź czy oferta istnieje i jest aktywna
    job_result = await db.execute(
        select(JobOffer).where(JobOffer.id == job_id, JobOffer.status == "active")
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
