import os
import uuid
import logging

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.dependencies import get_optional_user
from app.core.rate_limit import limiter
from app.core.recaptcha import verify_recaptcha
from app.core.exceptions import NotFoundError, BadRequestError
from app.models.user import User
from app.models.cv_review import CVReview
from app.models.cv_database import CVDatabase
from app.services.cv_extractor import extract_text
from app.services.cv_ai import analyze_cv_with_ai, fallback_analysis
from app.services.email import _send_email
from app.schemas.cv_review import (
    CVReviewResponse,
    CVReviewEmailRequest,
    CVDatabaseSubmitRequest,
    CVAnalysisResult,
)
from app.schemas.common import MessageResponse
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)
settings = get_settings()

router = APIRouter(prefix="/cv-review", tags=["Analiza CV"])

ALLOWED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}


def _get_upload_dir() -> str:
    """Ensure cv-review upload directory exists and return path."""
    upload_dir = os.path.join(settings.UPLOAD_DIR, "cv-review")
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir


@router.post("/analyze", response_model=CVReviewResponse)
@limiter.limit("3/hour")
async def analyze_cv(
    request: Request,
    file: UploadFile = File(...),
    email: str | None = Form(None),
    previous_review_id: str | None = Form(None),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_recaptcha),
):
    """Upload and analyze a CV file using AI."""
    # Validate file type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise BadRequestError(
            "Nieobsługiwany format pliku. Dozwolone: PDF, DOCX"
        )

    # Validate file size (max 5 MB)
    content = await file.read()
    max_size = settings.MAX_CV_SIZE_MB * 1024 * 1024
    if len(content) > max_size:
        raise BadRequestError(
            f"Plik jest za duży. Maksymalny rozmiar: {settings.MAX_CV_SIZE_MB} MB"
        )

    # Save file
    upload_dir = _get_upload_dir()
    ext = ".pdf" if file.content_type == "application/pdf" else ".docx"
    filename = f"{uuid.uuid4()}{ext}"
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(content)

    # Extract text
    cv_text = extract_text(file_path, file.content_type)
    if not cv_text or len(cv_text.strip()) < 50:
        # Clean up file on failure
        try:
            os.remove(file_path)
        except OSError:
            pass
        raise BadRequestError(
            "Nie udało się wyodrębnić tekstu z CV. Upewnij się, że plik nie jest pusty ani zeskanowanym obrazem."
        )

    # AI analysis
    analysis = await analyze_cv_with_ai(cv_text)
    if analysis is None:
        # Fallback to basic analysis
        analysis = fallback_analysis(cv_text)

    # Check for previous review (for comparison)
    previous_score = None
    if previous_review_id:
        prev_result = await db.execute(
            select(CVReview).where(CVReview.id == previous_review_id)
        )
        prev_review = prev_result.scalar_one_or_none()
        if prev_review and prev_review.overall_score:
            previous_score = prev_review.overall_score

    # Save to database
    review = CVReview(
        user_id=current_user.id if current_user else None,
        email=email or (current_user.email if current_user else None),
        cv_filename=filename,
        cv_original_filename=file.filename or "cv",
        cv_text=cv_text,
        overall_score=analysis["overall_score"],
        analysis_json=analysis,
        status="analyzed",
        previous_review_id=previous_review_id,
    )
    db.add(review)
    await db.flush()
    await db.refresh(review)

    return CVReviewResponse(
        id=review.id,
        email=review.email,
        cv_filename=review.cv_filename,
        cv_original_filename=review.cv_original_filename,
        overall_score=review.overall_score,
        analysis=CVAnalysisResult(**analysis),
        status=review.status,
        previous_score=previous_score,
        created_at=review.created_at,
    )


@router.get("/{review_id}", response_model=CVReviewResponse)
async def get_review(
    review_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a CV review by ID."""
    result = await db.execute(
        select(CVReview).where(CVReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Analiza CV nie istnieje")

    # Check for previous score
    previous_score = None
    if review.previous_review_id:
        prev_result = await db.execute(
            select(CVReview).where(CVReview.id == review.previous_review_id)
        )
        prev_review = prev_result.scalar_one_or_none()
        if prev_review and prev_review.overall_score:
            previous_score = prev_review.overall_score

    analysis = None
    if review.analysis_json:
        analysis = CVAnalysisResult(**review.analysis_json)

    return CVReviewResponse(
        id=review.id,
        email=review.email,
        cv_filename=review.cv_filename,
        cv_original_filename=review.cv_original_filename,
        overall_score=review.overall_score,
        analysis=analysis,
        status=review.status,
        previous_score=previous_score,
        created_at=review.created_at,
    )


@router.post("/{review_id}/send-email", response_model=MessageResponse)
async def send_review_email(
    review_id: str,
    body: CVReviewEmailRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send CV review results to email."""
    result = await db.execute(
        select(CVReview).where(CVReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Analiza CV nie istnieje")

    if not review.analysis_json:
        raise BadRequestError("Brak wyników analizy do wysłania")

    analysis = review.analysis_json
    score = analysis.get("overall_score", 0)

    # Build HTML email
    strengths_html = "".join(
        f'<li style="color:#16a34a;margin-bottom:4px;">&#10003; {s}</li>'
        for s in analysis.get("strengths", [])
    )
    improvements_html = "".join(
        f'<li style="color:#d97706;margin-bottom:4px;">&#9888; {s}</li>'
        for s in analysis.get("improvements", [])
    )
    missing_html = "".join(
        f'<li style="color:#dc2626;margin-bottom:4px;">&#10007; {s}</li>'
        for s in analysis.get("missing", [])
    )
    tips_html = "".join(
        f'<li style="color:#2563eb;margin-bottom:4px;">&#128161; {s}</li>'
        for s in analysis.get("tips", [])
    )

    score_color = "#dc2626" if score <= 3 else "#d97706" if score <= 6 else "#16a34a"

    html = f"""
    <div style="font-family:Arial,sans-serif;max-width:600px;margin:0 auto;padding:20px;">
        <div style="text-align:center;margin-bottom:30px;">
            <h1 style="color:#dc2626;margin-bottom:5px;">Praca w Szwajcarii</h1>
            <h2 style="color:#1f2937;">Wyniki analizy Twojego CV</h2>
        </div>

        <div style="text-align:center;margin:30px 0;">
            <div style="display:inline-block;width:100px;height:100px;border-radius:50%;border:6px solid {score_color};line-height:100px;font-size:36px;font-weight:bold;color:{score_color};">
                {score}/10
            </div>
        </div>

        <p style="color:#4b5563;text-align:center;margin-bottom:30px;">
            {analysis.get("summary", "")}
        </p>

        <div style="margin-bottom:20px;">
            <h3 style="color:#16a34a;">Mocne strony</h3>
            <ul style="list-style:none;padding:0;">{strengths_html}</ul>
        </div>

        <div style="margin-bottom:20px;">
            <h3 style="color:#d97706;">Do poprawienia</h3>
            <ul style="list-style:none;padding:0;">{improvements_html}</ul>
        </div>

        <div style="margin-bottom:20px;">
            <h3 style="color:#dc2626;">Brakujące elementy</h3>
            <ul style="list-style:none;padding:0;">{missing_html}</ul>
        </div>

        <div style="margin-bottom:20px;">
            <h3 style="color:#2563eb;">Porady na rynek szwajcarski</h3>
            <ul style="list-style:none;padding:0;">{tips_html}</ul>
        </div>

        <div style="text-align:center;margin-top:30px;padding-top:20px;border-top:1px solid #e5e7eb;">
            <p style="color:#6b7280;font-size:12px;">
                Ta wiadomość została wysłana przez praca-w-szwajcarii.ch
            </p>
        </div>
    </div>
    """

    success = _send_email(body.email, "Wyniki analizy CV - Praca w Szwajcarii", html)
    if not success:
        raise BadRequestError("Nie udało się wysłać emaila. Spróbuj ponownie.")

    # Update email on review if not set
    if not review.email:
        review.email = body.email

    return MessageResponse(message="Wyniki zostały wysłane na podany adres email")


@router.post("/{review_id}/submit-to-database", response_model=MessageResponse)
async def submit_to_database(
    review_id: str,
    body: CVDatabaseSubmitRequest,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit CV to recruiter database with job preferences."""
    if not body.consent_given:
        raise BadRequestError("Wymagana jest zgoda na przetwarzanie danych")

    result = await db.execute(
        select(CVReview).where(CVReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Analiza CV nie istnieje")

    # Check if already submitted
    existing = await db.execute(
        select(CVDatabase).where(CVDatabase.cv_review_id == review_id)
    )
    if existing.scalar_one_or_none():
        raise BadRequestError("To CV zostało już przesłane do bazy rekruterów")

    # Build file path
    file_path = None
    if review.cv_filename:
        file_path = os.path.join("cv-review", review.cv_filename)

    # Normalize driving_license to list
    driving_license = body.driving_license
    if isinstance(driving_license, str):
        driving_license = [driving_license] if driving_license else []

    # Create database entry with extraction_status="pending"
    # AI extraction will happen in background via scheduler
    cv_db = CVDatabase(
        user_id=current_user.id if current_user else review.user_id,
        cv_review_id=review.id,
        full_name=body.full_name,
        email=body.email,
        phone=body.phone,
        cv_text=review.cv_text,
        cv_file_path=file_path,
        job_preferences=body.job_preferences,
        available_from=body.available_from,
        preferred_cantons=body.preferred_cantons,
        expected_salary_min=body.expected_salary_min,
        expected_salary_max=body.expected_salary_max,
        work_mode=body.work_mode,
        languages=body.languages,
        driving_license=driving_license,
        has_car=body.has_car,
        additional_notes=body.additional_notes,
        consent_given=body.consent_given,
        extraction_status="pending",
    )
    db.add(cv_db)

    # Update review status & extend retention (user gave explicit consent)
    review.status = "submitted_to_db"
    review.retention_status = "consented"

    await db.flush()
    await log_activity(
        "cv_submitted", f"CV submitted to database: {body.full_name}",
        entity_type="cv_database", entity_id=cv_db.id,
    )

    return MessageResponse(
        message="Twoje CV zostało pomyślnie przesłane do bazy rekruterów"
    )
