import math
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.dependencies import get_current_worker, get_current_admin
from app.core.exceptions import NotFoundError, ConflictError, BadRequestError
from app.models.employer_profile import EmployerProfile
from app.models.review import EmployerReview
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewResponse,
    ReviewAdminResponse,
    ReviewListResponse,
    ReviewStatusUpdate,
)
from app.schemas.common import MessageResponse

router = APIRouter(tags=["Recenzje"])


# === PUBLIC / WORKER ENDPOINTS ===


@router.get("/companies/{slug}/reviews", response_model=ReviewListResponse)
async def get_company_reviews(
    slug: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista zatwierdzonych recenzji firmy (publiczny endpoint)."""
    profile_result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.company_slug == slug)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Firma nie została znaleziona")

    # Average rating and total count (approved only)
    stats_q = select(
        func.avg(EmployerReview.rating),
        func.count(),
    ).where(
        EmployerReview.employer_id == profile.id,
        EmployerReview.status == "approved",
    )
    stats_result = await db.execute(stats_q)
    stats_row = stats_result.one()
    avg_rating = round(float(stats_row[0]), 2) if stats_row[0] else None
    total_reviews = stats_row[1] or 0

    # Paginated reviews
    query = (
        select(EmployerReview)
        .options(selectinload(EmployerReview.worker))
        .where(
            EmployerReview.employer_id == profile.id,
            EmployerReview.status == "approved",
        )
        .order_by(EmployerReview.created_at.desc())
    )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    reviews = result.scalars().all()

    data = []
    for review in reviews:
        worker = review.worker
        worker_name = ""
        if worker and worker.first_name:
            worker_name = worker.first_name
            if worker.last_name:
                worker_name += f" {worker.last_name[0]}."
        elif worker:
            worker_name = "Anonim"

        data.append(ReviewResponse(
            id=review.id,
            employer_id=review.employer_id,
            rating=review.rating,
            comment=review.comment,
            status=review.status,
            worker_name=worker_name,
            created_at=review.created_at,
        ))

    return ReviewListResponse(
        data=data,
        total=total or 0,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
        avg_rating=avg_rating,
        total_reviews=total_reviews,
    )


@router.post("/companies/{slug}/reviews", response_model=ReviewResponse)
async def create_review(
    slug: str,
    payload: ReviewCreate,
    current_user: User = Depends(get_current_worker),
    db: AsyncSession = Depends(get_db),
):
    """Dodaj recenzję firmy (tylko zalogowani pracownicy)."""
    profile_result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.company_slug == slug)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Firma nie została znaleziona")

    # Check for existing review
    existing = await db.execute(
        select(EmployerReview).where(
            EmployerReview.employer_id == profile.id,
            EmployerReview.worker_user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictError("Już wystawiłeś recenzję tej firmie")

    review = EmployerReview(
        employer_id=profile.id,
        worker_user_id=current_user.id,
        rating=payload.rating,
        comment=payload.comment,
        status="pending",
    )
    db.add(review)
    await db.flush()

    worker_name = ""
    if current_user.first_name:
        worker_name = current_user.first_name
        if current_user.last_name:
            worker_name += f" {current_user.last_name[0]}."
    else:
        worker_name = "Anonim"

    return ReviewResponse(
        id=review.id,
        employer_id=review.employer_id,
        rating=review.rating,
        comment=review.comment,
        status=review.status,
        worker_name=worker_name,
        created_at=review.created_at,
    )


# === ADMIN ENDPOINTS ===


@router.get("/admin/reviews")
async def admin_list_reviews(
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista wszystkich recenzji (admin, z filtrem statusu)."""
    query = (
        select(EmployerReview)
        .options(
            selectinload(EmployerReview.worker),
            selectinload(EmployerReview.employer),
        )
        .order_by(EmployerReview.created_at.desc())
    )
    if status_filter:
        query = query.where(EmployerReview.status == status_filter)

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    reviews = result.scalars().all()

    data = []
    for review in reviews:
        worker = review.worker
        worker_name = worker.full_name if worker else "Usunięty użytkownik"
        company_name = review.employer.company_name if review.employer else "Usunięta firma"

        data.append(ReviewAdminResponse(
            id=review.id,
            employer_id=review.employer_id,
            worker_user_id=review.worker_user_id,
            rating=review.rating,
            comment=review.comment,
            status=review.status,
            worker_name=worker_name,
            company_name=company_name,
            created_at=review.created_at,
            updated_at=review.updated_at,
        ))

    return {
        "data": data,
        "total": total or 0,
        "page": page,
        "per_page": per_page,
        "pages": math.ceil(total / per_page) if total else 0,
    }


@router.patch("/admin/reviews/{review_id}", response_model=MessageResponse)
async def moderate_review(
    review_id: str,
    payload: ReviewStatusUpdate,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Moderacja recenzji (approve/reject, admin only)."""
    result = await db.execute(
        select(EmployerReview).where(EmployerReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Recenzja nie istnieje")

    review.status = payload.status
    status_text = "zatwierdzona" if payload.status == "approved" else "odrzucona"
    return MessageResponse(message=f"Recenzja została {status_text}")


@router.delete("/admin/reviews/{review_id}", response_model=MessageResponse)
async def delete_review(
    review_id: str,
    current_user: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Usunięcie recenzji (admin only)."""
    result = await db.execute(
        select(EmployerReview).where(EmployerReview.id == review_id)
    )
    review = result.scalar_one_or_none()
    if not review:
        raise NotFoundError("Recenzja nie istnieje")

    await db.delete(review)
    return MessageResponse(message="Recenzja została usunięta")
