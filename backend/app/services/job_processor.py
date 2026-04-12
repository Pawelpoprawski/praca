"""Generic job processing pipeline.

Provides a standardized interface (RawJobData) for job sources and a generic
pipeline that saves raw jobs to DB (no AI). AI extraction happens later via
job_extraction_service.py scheduler.
Also provides process_single_text() for the employer "Create job by AI" feature.
"""
import logging
import re
import secrets
import uuid
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.sanitize import sanitize_html
from app.core.security import hash_password
from app.models.employer_profile import EmployerProfile
from app.models.job_offer import JobOffer
from app.models.posting_quota import PostingQuota
from app.models.user import User
from app.services.job_ai import SWISS_CANTONS_MAP

logger = logging.getLogger(__name__)


# ── Standardized raw job data ────────────────────────────────────────────


@dataclass
class RawJobData:
    """Standardized format all job sources must return."""

    source_id: str
    source_name: str
    title: str
    company_name: str
    description: str = ""
    requirements: str = ""
    benefits: str = ""
    city: str | None = None
    country: str = "Szwajcaria"
    url: str | None = None
    salary_from: str | None = None
    salary_to: str | None = None
    salary_currency: str = "CHF"
    recruiter_type: str | None = None


# ── Sync result tracking ────────────────────────────────────────────────


class SyncResult:
    """Holds the results of a scraper sync operation."""

    def __init__(self):
        self.added: int = 0
        self.removed: int = 0
        self.skipped: int = 0
        self.filtered: int = 0
        self.errors: list[str] = []
        self.started_at: datetime = datetime.now(timezone.utc)
        self.finished_at: datetime | None = None

    def to_dict(self) -> dict:
        return {
            "added": self.added,
            "removed": self.removed,
            "skipped": self.skipped,
            "filtered": self.filtered,
            "errors": self.errors[:50],
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "duration_seconds": (
                (self.finished_at - self.started_at).total_seconds()
                if self.finished_at
                else None
            ),
        }


# ── Swiss city-to-canton mapping ─────────────────────────────────────────

CITY_TO_CANTON: dict[str, str] = {
    # Zurich
    "zurich": "zurich", "zurych": "zurich", "zürich": "zurich",
    "winterthur": "zurich", "uster": "zurich", "dübendorf": "zurich",
    "dietikon": "zurich", "wetzikon": "zurich", "bülach": "zurich",
    "horgen": "zurich", "adliswil": "zurich", "wallisellen": "zurich",
    "illnau-effretikon": "zurich", "regensdorf": "zurich", "kloten": "zurich",
    "opfikon": "zurich", "volketswil": "zurich", "wädenswil": "zurich",
    "gossau zh": "zurich", "thalwil": "zurich", "schlieren": "zurich",
    # Bern
    "bern": "bern", "berno": "bern", "biel/bienne": "bern", "biel": "bern",
    "thun": "bern", "köniz": "bern", "burgdorf": "bern",
    "steffisburg": "bern", "spiez": "bern", "langenthal": "bern",
    "lyss": "bern", "muri bei bern": "bern", "ittigen": "bern",
    "ostermundigen": "bern", "interlaken": "bern", "moutier": "bern",
    # Luzern
    "luzern": "luzern", "lucerna": "luzern", "lucerne": "luzern",
    "emmen": "luzern", "kriens": "luzern", "horw": "luzern",
    "ebikon": "luzern", "sursee": "luzern", "rothenburg": "luzern",
    # Uri
    "altdorf": "uri",
    # Schwyz
    "schwyz": "schwyz", "einsiedeln": "schwyz", "freienbach": "schwyz",
    "küssnacht": "schwyz",
    # Obwalden
    "sarnen": "obwalden",
    # Nidwalden
    "stans": "nidwalden",
    # Glarus
    "glarus": "glarus",
    # Zug
    "zug": "zug", "baar": "zug", "cham": "zug", "rotkreuz": "zug",
    "steinhausen": "zug",
    # Fribourg
    "fribourg": "fribourg", "fryburg": "fribourg", "freiburg": "fribourg",
    "bulle": "fribourg", "murten": "fribourg", "villars-sur-glâne": "fribourg",
    # Solothurn
    "solothurn": "solothurn", "olten": "solothurn", "grenchen": "solothurn",
    "zuchwil": "solothurn",
    # Basel-Stadt
    "basel": "basel-stadt", "bazylea": "basel-stadt",
    # Basel-Landschaft
    "liestal": "basel-landschaft", "allschwil": "basel-landschaft",
    "reinach": "basel-landschaft", "muttenz": "basel-landschaft",
    "binningen": "basel-landschaft", "oberwil": "basel-landschaft",
    "münchenstein": "basel-landschaft", "pratteln": "basel-landschaft",
    # Schaffhausen
    "schaffhausen": "schaffhausen", "szafuza": "schaffhausen",
    "neuhausen am rheinfall": "schaffhausen",
    # Appenzell Ausserrhoden
    "herisau": "appenzell-ausserrhoden", "heiden": "appenzell-ausserrhoden",
    "teufen": "appenzell-ausserrhoden",
    # Appenzell Innerrhoden
    "appenzell": "appenzell-innerrhoden",
    # St. Gallen
    "st. gallen": "st-gallen", "st gallen": "st-gallen", "rapperswil-jona": "st-gallen",
    "wil": "st-gallen", "gossau sg": "st-gallen", "rorschach": "st-gallen",
    "buchs sg": "st-gallen", "uzwil": "st-gallen", "flawil": "st-gallen",
    # Graubünden
    "chur": "graubunden", "davos": "graubunden", "st. moritz": "graubunden",
    "landquart": "graubunden", "ilanz": "graubunden",
    # Aargau
    "aarau": "aargau", "wettingen": "aargau", "baden": "aargau",
    "lenzburg": "aargau", "brugg": "aargau", "oftringen": "aargau",
    "zofingen": "aargau", "rheinfelden": "aargau", "möhlin": "aargau",
    "wohlen": "aargau", "spreitenbach": "aargau", "windisch": "aargau",
    "obersiggenthal": "aargau", "suhr": "aargau",
    # Thurgau
    "frauenfeld": "thurgau", "kreuzlingen": "thurgau", "arbon": "thurgau",
    "amriswil": "thurgau", "weinfelden": "thurgau",
    # Ticino
    "lugano": "ticino", "bellinzona": "ticino", "locarno": "ticino",
    "mendrisio": "ticino", "chiasso": "ticino",
    # Vaud
    "lausanne": "vaud", "yverdon-les-bains": "vaud", "montreux": "vaud",
    "nyon": "vaud", "renens": "vaud", "morges": "vaud", "vevey": "vaud",
    "pully": "vaud", "prilly": "vaud", "ecublens": "vaud", "aigle": "vaud",
    # Valais
    "sion": "valais", "martigny": "valais", "monthey": "valais",
    "brig": "valais", "visp": "valais", "sierre": "valais",
    "zermatt": "valais", "naters": "valais",
    # Neuchatel
    "neuchâtel": "neuchatel", "la chaux-de-fonds": "neuchatel",
    "le locle": "neuchatel",
    # Geneve
    "geneve": "geneve", "genève": "geneve", "genewa": "geneve",
    "geneva": "geneve", "genf": "geneve",
    "carouge": "geneve", "vernier": "geneve", "lancy": "geneve",
    "meyrin": "geneve", "onex": "geneve", "thônex": "geneve",
    # Jura
    "delémont": "jura", "porrentruy": "jura",
}


# ── Validation helpers ───────────────────────────────────────────────────


def _resolve_canton_from_city(city_name: str | None) -> str | None:
    """Try to resolve canton from city name using the city-to-canton mapping."""
    if not city_name:
        return None
    city_lower = city_name.lower().strip()

    if city_lower in CITY_TO_CANTON:
        return CITY_TO_CANTON[city_lower]

    for city_key, canton in CITY_TO_CANTON.items():
        if city_key in city_lower or city_lower in city_key:
            return canton

    return None


def _resolve_canton(canton_raw: str | None, city_name: str | None = None) -> str | None:
    """Resolve canton from AI-provided canton_raw or fall back to city mapping."""
    if canton_raw:
        canton_lower = canton_raw.lower().strip()
        for canton_value, aliases in SWISS_CANTONS_MAP.items():
            if canton_lower in aliases or canton_lower == canton_value:
                return canton_value
        for canton_value, aliases in SWISS_CANTONS_MAP.items():
            for alias in aliases:
                if alias in canton_lower or canton_lower in alias:
                    return canton_value

    return _resolve_canton_from_city(city_name)


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        v = int(val)
        return v if v >= 0 else None
    except (ValueError, TypeError):
        return None


def _slugify(text: str) -> str:
    """Create a URL-friendly slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


# ── Employer auto-creation ───────────────────────────────────────────────


async def get_or_create_employer(
    db: AsyncSession, company_name: str
) -> EmployerProfile:
    """Find existing employer by company_name, or create a new one."""
    result = await db.execute(
        select(EmployerProfile).where(EmployerProfile.company_name == company_name)
    )
    existing = result.scalar_one_or_none()
    if existing:
        return existing

    slug = _slugify(company_name)
    slug_check = await db.execute(
        select(EmployerProfile).where(EmployerProfile.company_slug == slug)
    )
    if slug_check.scalar_one_or_none():
        slug = f"{slug}-{str(uuid.uuid4())[:8]}"

    slug_for_email = re.sub(r"[^a-z0-9-]", "", slug)[:50]
    auto_email = f"import-{slug_for_email}@praca-szwajcaria.ch"

    email_check = await db.execute(
        select(User).where(User.email == auto_email)
    )
    if email_check.scalar_one_or_none():
        auto_email = f"import-{slug_for_email}-{str(uuid.uuid4())[:6]}@praca-szwajcaria.ch"

    random_password = secrets.token_urlsafe(32)
    user = User(
        email=auto_email,
        password_hash=hash_password(random_password),
        role="employer",
        first_name="Import",
        last_name=company_name[:100],
        is_active=True,
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    profile = EmployerProfile(
        user_id=user.id,
        company_name=company_name,
        company_slug=slug,
        is_verified=False,
    )
    db.add(profile)
    await db.flush()

    today = date.today()
    quota = PostingQuota(
        employer_id=profile.id,
        monthly_limit=1000,
        custom_limit=1000,
        used_count=0,
        period_start=today,
        period_end=today + timedelta(days=365),
        plan_type="import",
    )
    db.add(quota)

    logger.info(f"Created auto-import employer: {company_name} (slug: {slug})")
    return profile


# ── Generic job processing pipeline ─────────────────────────────────────


async def process_jobs(
    raw_jobs: list[RawJobData],
    db: AsyncSession,
    limit: int | None = None,
) -> SyncResult:
    """Save raw jobs to DB without AI. AI extraction happens later via scheduler.

    For each job: basic sanitization -> employer creation -> DB save with
    extraction_status='pending', status='pending'.
    Each job is committed individually for incremental visibility.
    """
    result = SyncResult()

    total = len(raw_jobs)

    for raw in raw_jobs:
        if limit is not None and result.added >= limit:
            logger.info(f"Reached limit of {limit} new jobs, stopping")
            break

        try:
            # Get or create employer
            employer = await get_or_create_employer(db, raw.company_name)

            # Resolve canton from raw city
            canton = _resolve_canton_from_city(raw.city) or "zurich"

            # Build description from raw parts
            description = raw.description or ""
            if raw.requirements:
                description += f"\n\n<h3>Wymagania</h3>\n{raw.requirements}"
            if raw.benefits:
                description += f"\n\n<h3>Oferujemy</h3>\n{raw.benefits}"
            description = sanitize_html(description)

            # City
            city = raw.city[:100] if raw.city else None

            # Salary
            salary_min = _safe_int(raw.salary_from)
            salary_max = _safe_int(raw.salary_to)

            # Create job offer — raw data, no AI
            job = JobOffer(
                employer_id=employer.id,
                title=raw.title[:255],
                description=description,
                canton=canton,
                city=city,
                contract_type="full_time",
                salary_min=salary_min,
                salary_max=salary_max,
                salary_type="monthly",
                salary_currency=raw.salary_currency or "CHF",
                is_remote="no",
                apply_via="external_url",
                external_url=raw.url,
                source_id=raw.source_id,
                source_name=raw.source_name,
                recruiter_type=raw.recruiter_type,
                status="pending",
                extraction_status="pending",
                translation_status="pending",
            )
            db.add(job)
            await db.commit()
            result.added += 1

            logger.info(
                f"[{result.added}/{total}] Saved raw: {raw.title[:80]} "
                f"({raw.source_id}) for {raw.company_name}"
            )

        except Exception as e:
            await db.rollback()
            result.errors.append(
                f"Error creating {raw.source_id} ({raw.title}): {str(e)}"
            )
            logger.error(
                f"Error processing job {raw.source_id}: {e}", exc_info=True
            )

    return result


# ── Single text processing (for employer "Create by AI") ─────────────────


async def process_single_text(text: str) -> dict | None:
    """Parse raw job posting text using AI and return structured data.

    Used by the employer "Create job by AI" feature. No DB save.
    Two-step pipeline:
    1. Translation: DE/FR/IT -> Polish title + description
    2. Extraction: metadata from the (now Polish) text

    Returns dict ready for form pre-fill, or None if parsing fails.
    """
    from app.services.job_translation_service import _call_translation_ai
    from app.services.job_extraction_service import _call_extraction_ai, _validate_extraction, _resolve_canton

    # Step 1: Translate to Polish
    translation = await _call_translation_ai(
        title="",
        company="",
        description=text[:10000],
    )

    if translation:
        title = translation.get("translated_title", "")
        description = translation.get("translated_description", "")
    else:
        # If translation fails, try extraction on raw text
        title = ""
        description = text[:10000]

    # Step 2: Extract metadata from Polish text
    ai_data = await _call_extraction_ai(
        title=title,
        company="",
        description=description[:5000],
    )

    if not ai_data:
        return None

    processed = _validate_extraction(ai_data)

    # Resolve canton
    canton = _resolve_canton(
        processed.get("canton_raw"),
        processed.get("city"),
    )

    # Sanitize description from translation
    clean_desc = description
    if clean_desc:
        clean_desc = sanitize_html(clean_desc)

    return {
        "title": title or None,
        "description": clean_desc or None,
        "city": processed.get("city"),
        "canton": canton,
        "contract_type": processed["contract_type"],
        "salary_min": processed["salary_min"],
        "salary_max": processed["salary_max"],
        "salary_type": processed["salary_type"],
        "is_remote": processed["is_remote"],
        "experience_min": processed["experience_min"],
        "requirements": [],
        "benefits": [],
        "languages": processed["languages"],
        "category_slug": processed["category_slug"],
        "car_required": processed["car_required"],
        "driving_license_required": processed["driving_license_required"],
        "keywords": processed.get("keywords"),
    }
