import uuid
import math
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.core.exceptions import NotFoundError
from app.models.employer_profile import EmployerProfile
from app.models.job_offer import JobOffer
from app.schemas.employer import EmployerProfileResponse
from app.schemas.job import JobListResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/companies", tags=["Firmy"])


@router.get("/{slug}")
async def get_company(slug: str, db: AsyncSession = Depends(get_db)):
    """Publiczny profil firmy."""
    result = await db.execute(
        select(EmployerProfile)
        .options(selectinload(EmployerProfile.user))
        .where(EmployerProfile.company_slug == slug)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Firma nie została znaleziona")

    return {
        "id": str(profile.id),
        "company_name": profile.company_name,
        "company_slug": profile.company_slug,
        "description": profile.description,
        "logo_url": profile.logo_url,
        "website": profile.website,
        "industry": profile.industry,
        "canton": profile.canton,
        "city": profile.city,
        "company_size": profile.company_size,
        "is_verified": profile.is_verified,
    }


@router.get("/{slug}/jobs", response_model=PaginatedResponse[JobListResponse])
async def get_company_jobs(
    slug: str,
    db: AsyncSession = Depends(get_db),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Aktywne oferty firmy."""
    profile_result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.company_slug == slug)
    )
    profile = profile_result.scalar_one_or_none()
    if not profile:
        raise NotFoundError("Firma nie została znaleziona")

    query = (
        select(JobOffer)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .where(
            JobOffer.employer_id == profile.id,
            JobOffer.status == "active",
            or_(JobOffer.expires_at.is_(None), JobOffer.expires_at > func.now()),
        )
        .order_by(JobOffer.published_at.desc())
    )

    count_q = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_q)

    result = await db.execute(query.offset((page - 1) * per_page).limit(per_page))
    jobs = result.scalars().all()

    return PaginatedResponse(
        data=[JobListResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )
