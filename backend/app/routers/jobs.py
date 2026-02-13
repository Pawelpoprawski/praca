import math
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query
from app.database import get_db
from app.core.exceptions import NotFoundError
from app.models.job_offer import JobOffer
from app.models.employer_profile import EmployerProfile
from app.models.category import Category
from app.schemas.job import JobResponse, JobListResponse
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/jobs", tags=["Oferty pracy"])

# Lista 26 kantonów Szwajcarii
SWISS_CANTONS = [
    "zurich", "bern", "luzern", "uri", "schwyz", "obwalden", "nidwalden",
    "glarus", "zug", "fribourg", "solothurn", "basel-stadt", "basel-landschaft",
    "schaffhausen", "appenzell-ausserrhoden", "appenzell-innerrhoden",
    "st-gallen", "graubunden", "aargau", "thurgau", "ticino", "vaud",
    "valais", "neuchatel", "geneve", "jura",
]


@router.get("", response_model=PaginatedResponse[JobListResponse])
async def list_jobs(
    db: AsyncSession = Depends(get_db),
    q: str | None = Query(None, description="Szukaj w tytule i opisie"),
    canton: str | None = Query(None, description="Kanton (rozdzielone przecinkami)"),
    category_id: str | None = Query(None),
    contract_type: str | None = Query(None, description="Typ umowy (rozdzielone przecinkami)"),
    salary_min: int | None = Query(None, ge=0),
    salary_max: int | None = Query(None, ge=0),
    language: str | None = Query(None, description="Wymagany język"),
    is_remote: str | None = Query(None),
    work_permit_sponsored: bool | None = Query(None),
    sort_by: str = Query("published_at", pattern="^(published_at|salary|views)$"),
    sort_order: str = Query("desc", pattern="^(asc|desc)$"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    """Lista aktywnych ofert pracy z filtrami."""
    query = (
        select(JobOffer)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .where(
            JobOffer.status == "active",
            or_(JobOffer.expires_at.is_(None), JobOffer.expires_at > func.now()),
        )
    )

    # Full-text search
    if q:
        search_filter = or_(
            JobOffer.title.ilike(f"%{q}%"),
            JobOffer.description.ilike(f"%{q}%"),
        )
        query = query.where(search_filter)

    # Kanton (multi-select)
    if canton:
        cantons = [c.strip() for c in canton.split(",")]
        query = query.where(JobOffer.canton.in_(cantons))

    # Kategoria
    if category_id:
        query = query.where(JobOffer.category_id == category_id)

    # Typ umowy (multi-select)
    if contract_type:
        types = [t.strip() for t in contract_type.split(",")]
        query = query.where(JobOffer.contract_type.in_(types))

    # Wynagrodzenie
    if salary_min is not None:
        query = query.where(
            or_(JobOffer.salary_max >= salary_min, JobOffer.salary_max.is_(None))
        )
    if salary_max is not None:
        query = query.where(
            or_(JobOffer.salary_min <= salary_max, JobOffer.salary_min.is_(None))
        )

    # Język - use LIKE on the JSON text for cross-database compatibility
    if language:
        query = query.where(
            cast(JobOffer.languages_required, String).ilike(f"%{language}%")
        )

    # Praca zdalna
    if is_remote:
        query = query.where(JobOffer.is_remote == is_remote)

    # Sponsoring pozwolenia
    if work_permit_sponsored is not None:
        query = query.where(JobOffer.work_permit_sponsored == work_permit_sponsored)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # Sortowanie - wyróżnione zawsze na górze
    order_clauses = [JobOffer.is_featured.desc(), JobOffer.feature_priority.desc()]
    if sort_by == "published_at":
        col = JobOffer.published_at.desc() if sort_order == "desc" else JobOffer.published_at.asc()
        order_clauses.append(col)
    elif sort_by == "salary":
        order_clauses.append(JobOffer.salary_max.desc().nulls_last())
    elif sort_by == "views":
        order_clauses.append(JobOffer.views_count.desc())

    query = query.order_by(*order_clauses)

    # Paginacja
    query = query.offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(query)
    jobs = result.scalars().all()

    return PaginatedResponse(
        data=[JobListResponse.model_validate(j) for j in jobs],
        total=total,
        page=page,
        per_page=per_page,
        pages=math.ceil(total / per_page) if total else 0,
    )


@router.get("/categories")
async def list_categories(db: AsyncSession = Depends(get_db)):
    """Lista aktywnych kategorii."""
    result = await db.execute(
        select(Category)
        .where(Category.is_active.is_(True))
        .order_by(Category.sort_order, Category.name)
    )
    categories = result.scalars().all()
    return [
        {
            "id": str(c.id),
            "name": c.name,
            "slug": c.slug,
            "icon": c.icon,
            "parent_id": str(c.parent_id) if c.parent_id else None,
        }
        for c in categories
    ]


@router.get("/cantons")
async def list_cantons():
    """Lista kantonów Szwajcarii."""
    canton_names = {
        "zurich": "Zurych", "bern": "Berno", "luzern": "Lucerna",
        "uri": "Uri", "schwyz": "Schwyz", "obwalden": "Obwalden",
        "nidwalden": "Nidwalden", "glarus": "Glarus", "zug": "Zug",
        "fribourg": "Fryburg", "solothurn": "Solura",
        "basel-stadt": "Bazylea-Miasto", "basel-landschaft": "Bazylea-Okręg",
        "schaffhausen": "Szafuza",
        "appenzell-ausserrhoden": "Appenzell Ausserrhoden",
        "appenzell-innerrhoden": "Appenzell Innerrhoden",
        "st-gallen": "St. Gallen", "graubunden": "Gryzonia",
        "aargau": "Argowia", "thurgau": "Turgowia", "ticino": "Ticino",
        "vaud": "Vaud", "valais": "Valais", "neuchatel": "Neuchâtel",
        "geneve": "Genewa", "jura": "Jura",
    }
    return [{"value": k, "label": v} for k, v in canton_names.items()]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Szczegóły oferty pracy."""
    result = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .where(JobOffer.id == job_id, JobOffer.status == "active")
    )
    job = result.scalar_one_or_none()

    if not job:
        raise NotFoundError("Oferta nie została znaleziona")

    # Inkrementuj wyświetlenia (fire-and-forget)
    job.views_count += 1

    return job
