import math
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, or_, cast, String
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, Query, status
from app.database import get_db
from app.dependencies import get_optional_user
from app.core.exceptions import NotFoundError
from app.models.job_offer import JobOffer
from app.models.job_view import JobView
from app.models.search_log import SearchLog
from app.models.application_click import ApplicationClick
from app.models.employer_profile import EmployerProfile
from app.models.category import Category
from app.models.user import User
from app.schemas.job import JobResponse, JobListResponse
from app.schemas.common import PaginatedResponse, MessageResponse

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
    recruiter_type: str | None = Query(None, description="Typ rekrutera: polish / swiss"),
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

    # Full-text search — escape LIKE wildcards to prevent wildcard injection
    if q:
        escaped_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        search_filter = or_(
            JobOffer.title.ilike(f"%{escaped_q}%"),
            JobOffer.description.ilike(f"%{escaped_q}%"),
        )
        query = query.where(search_filter)
        # Log search query (fire-and-forget, don't fail on error)
        try:
            db.add(SearchLog(query=q.strip()[:255].lower()))
        except Exception:
            pass

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

    # Wynagrodzenie — exclude jobs with no salary data when filtering by salary
    if salary_min is not None:
        query = query.where(
            JobOffer.salary_max.isnot(None),
            JobOffer.salary_max >= salary_min,
        )
    if salary_max is not None:
        query = query.where(
            JobOffer.salary_min.isnot(None),
            JobOffer.salary_min <= salary_max,
        )

    # Język - use LIKE on the JSON text for cross-database compatibility
    if language:
        escaped_lang = language.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        query = query.where(
            cast(JobOffer.languages_required, String).ilike(f"%{escaped_lang}%")
        )

    # Praca zdalna
    if is_remote:
        query = query.where(JobOffer.is_remote == is_remote)

    # Typ rekrutera
    if recruiter_type:
        query = query.where(JobOffer.recruiter_type == recruiter_type)

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


@router.get("/popular-searches")
async def popular_searches(db: AsyncSession = Depends(get_db)):
    """Top 6 najpopularniejszych wyszukiwań z ostatnich 30 dni."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=30)
    result = await db.execute(
        select(SearchLog.query, func.count().label("cnt"))
        .where(SearchLog.created_at > cutoff)
        .group_by(SearchLog.query)
        .order_by(func.count().desc())
        .limit(6)
    )
    rows = result.all()
    if not rows:
        # Fallback: zwróć domyślne tagi jeśli brak danych
        return ["spawacz", "kierowca", "opiekun", "kelner", "budowa", "sprzątanie"]
    return [row[0] for row in rows]


@router.get("/suggestions")
async def job_suggestions(
    q: str = Query(..., min_length=2, max_length=100),
    db: AsyncSession = Depends(get_db),
):
    """Podpowiedzi tytułów ofert (od 3 znaków)."""
    escaped_q = q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
    result = await db.execute(
        select(JobOffer.title)
        .where(
            JobOffer.status == "active",
            or_(JobOffer.expires_at.is_(None), JobOffer.expires_at > func.now()),
            JobOffer.title.ilike(f"%{escaped_q}%"),
        )
        .distinct()
        .order_by(JobOffer.title)
        .limit(8)
    )
    return [row[0] for row in result.all()]


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    """Szczegóły oferty pracy."""
    result = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .where(
            JobOffer.id == job_id,
            JobOffer.status == "active",
            or_(JobOffer.expires_at.is_(None), JobOffer.expires_at > func.now()),
        )
    )
    job = result.scalar_one_or_none()

    if not job:
        raise NotFoundError("Oferta nie została znaleziona")

    # Inkrementuj wyświetlenia (fire-and-forget)
    job.views_count += 1

    return job


@router.get("/{job_id}/similar", response_model=list[JobListResponse])
async def get_similar_jobs(job_id: str, db: AsyncSession = Depends(get_db)):
    """Zwróć 4-6 podobnych ofert do danej oferty."""
    # Pobierz bieżącą ofertę
    result = await db.execute(
        select(JobOffer).where(JobOffer.id == job_id, JobOffer.status == "active")
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Oferta nie została znaleziona")

    # Bazowy filtr: aktywne, nie wygasłe, wykluczamy bieżącą
    base_filter = [
        JobOffer.status == "active",
        JobOffer.id != job_id,
        or_(JobOffer.expires_at.is_(None), JobOffer.expires_at > func.now()),
    ]

    similar_ids: list[str] = []

    # Priorytet -1: Dopasowanie po skills (najlepsze dopasowanie)
    if job.skills:
        for skill in job.skills[:5]:
            if len(similar_ids) >= 6:
                break
            escaped_skill = skill.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
            q = (
                select(JobOffer.id)
                .where(
                    *base_filter,
                    JobOffer.skills.isnot(None),
                    cast(JobOffer.skills, String).ilike(f"%{escaped_skill}%"),
                    JobOffer.id.not_in(similar_ids) if similar_ids else True,
                )
                .order_by(JobOffer.published_at.desc())
                .limit(6 - len(similar_ids))
            )
            res = await db.execute(q)
            similar_ids.extend(r[0] for r in res.all() if r[0] not in similar_ids)

    # Priorytet 0: Dopasowanie po AI keywords (najlepsze dopasowanie)
    if job.ai_keywords:
        keywords = [kw.strip().lower() for kw in job.ai_keywords.split(";") if kw.strip()]
        for kw in keywords[:5]:  # max 5 keywords to avoid too many queries
            if len(similar_ids) >= 6:
                break
            q = (
                select(JobOffer.id)
                .where(
                    *base_filter,
                    JobOffer.ai_keywords.isnot(None),
                    JobOffer.ai_keywords.ilike(f"%{kw}%"),
                    JobOffer.id.not_in(similar_ids) if similar_ids else True,
                )
                .order_by(JobOffer.published_at.desc())
                .limit(6 - len(similar_ids))
            )
            res = await db.execute(q)
            similar_ids.extend(r[0] for r in res.all() if r[0] not in similar_ids)

    # Priorytet 1: Ta sama kategoria + ten sam kanton (najlepsze dopasowanie)
    if job.category_id and job.canton:
        q = (
            select(JobOffer.id)
            .where(
                *base_filter,
                JobOffer.category_id == job.category_id,
                JobOffer.canton == job.canton,
            )
            .order_by(JobOffer.published_at.desc())
            .limit(6)
        )
        res = await db.execute(q)
        similar_ids.extend(r[0] for r in res.all() if r[0] not in similar_ids)

    # Priorytet 2: Ta sama kategoria (cała Szwajcaria)
    if len(similar_ids) < 6 and job.category_id:
        q = (
            select(JobOffer.id)
            .where(
                *base_filter,
                JobOffer.category_id == job.category_id,
                JobOffer.id.not_in(similar_ids) if similar_ids else True,
            )
            .order_by(JobOffer.published_at.desc())
            .limit(6 - len(similar_ids))
        )
        res = await db.execute(q)
        similar_ids.extend(r[0] for r in res.all() if r[0] not in similar_ids)

    # Priorytet 3: Ten sam kanton (dowolna kategoria)
    if len(similar_ids) < 6 and job.canton:
        q = (
            select(JobOffer.id)
            .where(
                *base_filter,
                JobOffer.canton == job.canton,
                JobOffer.id.not_in(similar_ids) if similar_ids else True,
            )
            .order_by(JobOffer.published_at.desc())
            .limit(6 - len(similar_ids))
        )
        res = await db.execute(q)
        similar_ids.extend(r[0] for r in res.all() if r[0] not in similar_ids)

    # Priorytet 4: Podobne wynagrodzenie (+-30%)
    if len(similar_ids) < 6 and (job.salary_min or job.salary_max):
        ref_salary = job.salary_max or job.salary_min
        low = int(ref_salary * 0.7)
        high = int(ref_salary * 1.3)
        q = (
            select(JobOffer.id)
            .where(
                *base_filter,
                JobOffer.id.not_in(similar_ids) if similar_ids else True,
                or_(
                    JobOffer.salary_min.between(low, high),
                    JobOffer.salary_max.between(low, high),
                ),
            )
            .order_by(JobOffer.published_at.desc())
            .limit(6 - len(similar_ids))
        )
        res = await db.execute(q)
        similar_ids.extend(r[0] for r in res.all() if r[0] not in similar_ids)

    if not similar_ids:
        return []

    # Pobierz pełne dane ofert z relacjami
    result = await db.execute(
        select(JobOffer)
        .options(selectinload(JobOffer.employer), selectinload(JobOffer.category))
        .where(JobOffer.id.in_(similar_ids))
        .order_by(JobOffer.published_at.desc())
    )
    jobs = result.scalars().all()

    return [JobListResponse.model_validate(j) for j in jobs[:6]]


@router.post("/{job_id}/view", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def record_job_view(
    job_id: str,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Zapisz wyświetlenie oferty (tylko dla zalogowanych użytkowników)."""
    # Sprawdź czy oferta istnieje
    result = await db.execute(
        select(JobOffer).where(JobOffer.id == job_id, JobOffer.status == "active")
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Oferta nie została znaleziona")

    if current_user is None:
        return MessageResponse(message="OK")

    # Sprawdź czy nie zapisano wyświetlenia w ostatnich 30 minutach (deduplikacja)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=30)
    existing = await db.execute(
        select(JobView).where(
            JobView.user_id == current_user.id,
            JobView.job_offer_id == job_id,
            JobView.viewed_at > cutoff,
        )
    )
    if existing.scalar_one_or_none():
        return MessageResponse(message="OK")

    view = JobView(
        user_id=current_user.id,
        job_offer_id=job_id,
    )
    db.add(view)

    return MessageResponse(message="Wyświetlenie zapisane")


@router.post("/{job_id}/apply-click", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def record_apply_click(
    job_id: str,
    click_type: str = Query(..., pattern="^(portal|external|email)$"),
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_db),
):
    """Record an apply button click (portal, external URL, or email)."""
    result = await db.execute(
        select(JobOffer).where(JobOffer.id == job_id, JobOffer.status == "active")
    )
    job = result.scalar_one_or_none()
    if not job:
        raise NotFoundError("Oferta nie została znaleziona")

    click = ApplicationClick(
        job_offer_id=job_id,
        click_type=click_type,
        user_id=current_user.id if current_user else None,
    )
    db.add(click)

    return MessageResponse(message="OK")
