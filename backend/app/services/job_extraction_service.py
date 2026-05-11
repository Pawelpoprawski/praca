"""Job metadata extraction service.

Handles background AI extraction of metadata from Polish job text.
Part 2 of the two-step pipeline:
1. Translation (job_translation_service): DE/FR/IT -> Polish (scraped jobs only)
2. Extraction (this service): metadata from Polish text (all jobs)

Manual employer jobs skip step 1 (already Polish + already active).
"""
import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.config import get_settings
from app.database import async_session
from app.models.job_offer import JobOffer
from app.services.activity_logger import log_activity
from app.services.job_ai import SWISS_CANTONS_MAP, CATEGORY_SLUGS

logger = logging.getLogger(__name__)

# Bump this to trigger re-extraction of all jobs
EXTRACTION_VERSION = 6

MAX_EXTRACTION_ATTEMPTS = 3

JOB_EXTRACTION_PROMPT = """Przeanalizuj ponizszy tekst oferty pracy i wyciagnij metadane.

Tytul: {title}
Firma: {company}
Opis: {description}

Zwroc JSON z polami:
{{
  "category_slug": "<JEDNO z: budownictwo, gastronomia, opieka, transport, it, sprzatanie, produkcja, handel, finanse, administracja, rolnictwo, inne>",
  "seniority_level": "<junior|mid|senior|lead|manager lub null — null dla prac fizycznych>",
  "contract_type": "<full_time|part_time|temporary|contract|internship|freelance>",
  "salary_min": "<liczba — stawka godzinowa lub miesieczna, np. 33.5 lub 5500, null jesli brak>",
  "salary_max": "<liczba lub null>",
  "salary_type": "<monthly|hourly|yearly|negotiable>",
  "per_diem": "<dzienna dieta/Spesen w CHF jako liczba, np. 16 lub 20, null jesli brak>",
  "experience_min": "<lata doswiadczenia jako liczba, 0 jesli brak wymagan>",
  "hours_per_week": "<godziny tygodniowo jako liczba, np. 42 lub 45, null jesli brak>",
  "city": "<KONKRETNE miasto, np. 'Wadenswil', 'Sursee', 'Lachen'. NIE wpisuj nazwy kantonu (Zurich, Bern...). NIE wpisuj fragmentow 'Cała Szwajcaria'/'Inne lokalizacje'/'cała'. Jezeli oferta dotyczy calego kantonu bez konkretnego miasta — null. 'okolice X' tylko gdy X to MIASTO, nie kanton.>",
  "canton_raw": "<DOKLADNIE JEDNA z 26 nazw szwajcarskich kantonow (po polsku): Zurych | Berno | Lucerna | Uri | Schwyz | Obwalden | Nidwalden | Glarus | Zug | Fribourg | Solura | Bazylea-Miasto | Bazylea-Okręg | Szafuza | Appenzell-Ausserrhoden | Appenzell-Innerrhoden | St. Gallen | Gryzonia | Argowia | Turgowia | Ticino | Vaud | Wallis | Neuchatel | Genewa | Jura. NULL w 2 przypadkach: a) oferta dotyczy 'calej Szwajcarii'/wielu kantonow bez glownego, b) brak danych geo. ZASADA: jeden konkretny kanton albo NULL — nie wybieraj 'glownego' z listy 3-4 kantonow, wtedy zwroc NULL.>",
  "required_skills": ["<umiejetnosc 1>", "<umiejetnosc 2>"],
  "nice_to_have_skills": ["<opcjonalna umiejetnosc>"],
  "languages": [{{"lang": "<pl|de|fr|it|en|hr|ro|hu|sr|ru|tr|pt|es>", "level": "<A1|A2|B1|B2|C1|C2>"}}],
  "driving_license_required": "<true TYLKO jesli opis jednoznacznie wymaga prawa jazdy (np. 'wymagane prawo jazdy kat. B', 'Fuhrerschein erforderlich'). Brak wzmianki = false. NIE zgaduj!>",
  "car_required": "<true TYLKO jesli opis jednoznacznie wymaga wlasnego samochodu (np. 'wlasny samochod wymagany', 'eigenes Auto'). Brak wzmianki = false. NIE zgaduj!>",
  "own_tools_required": "<true TYLKO jesli opis jednoznacznie wymaga wlasnych narzedzi. Brak wzmianki = false. NIE zgaduj!>",
  "education_required": "<wymagane wyksztalcenie/kwalifikacje lub null>",
  "certifications_required": ["<konkretny certyfikat: 'spawalniczy MIG/TIG', 'VCA/BHP', 'PSA/PPE'>"],
  "cv_german_required": "<true TYLKO gdy w opisie jednoznacznie pisze 'CV po niemiecku/Lebenslauf'. Brak wzmianki = false.>",
  "accommodation_provided": "<true TYLKO gdy opis jednoznacznie mowi 'zapewniamy zakwaterowanie/mieszkanie/Unterkunft'. Brak wzmianki = false.>",
  "accommodation_organized": "<true TYLKO gdy opis pisze o organizacji/pomocy znalezienia mieszkania. Brak wzmianki = false.>",
  "accommodation_deducted": "<true TYLKO gdy opis pisze ze koszt zakwaterowania potracany z wyplaty. Brak wzmianki = false.>",
  "relocation_support": "<true TYLKO gdy opis jednoznacznie wspomina o pomocy z relokacja/formalnosciami/pozwoleniami. Brak wzmianki = false.>",
  "coordinator_support": "<true TYLKO gdy opis wspomina o polskojezycznym koordynatorze/opiekunie. Brak wzmianki = false.>",
  "start_date_text": "<termin rozpoczecia: 'od zaraz', 'marzec 2026' lub null>",
  "contract_duration": "<czas trwania: '3 miesiace', 'nieokreslony', 'sezonowy' lub null>",
  "trial_period": "<okres probny: '3 miesiace', '1 miesiac' lub null — NIE mylij z contract_duration!>",
  "benefits": ["<benefit: szkolenia, ubezpieczenie, karta sportowa, 13. pensja, dodatek urlopowy itp.>"],
  "responsibilities": ["<obowiazek 1>", "<obowiazek 2>"],
  "keywords": "<5-10 polskich synonimow stanowiska oddzielonych srednikiem>",
  "industry_tags": ["<branza: budownictwo, gastronomia, medycyna, logistyka, rolnictwo itp.>"]
}}

Zasady:
- WSZYSTKIE pola boolean (true/false): default = FALSE. Zwracaj true TYLKO gdy konkretny tekst opisu to potwierdza. NIE ZGADUJ. NIE WNIOSKUJ. NIE DOMYSLAJ SIE. Lepiej false niz halucynacja.
- Domyslnie contract_type="full_time"
- salary: "33.50-36 CHF/h brutto" -> salary_min=33.5, salary_max=36, salary_type="hourly"
- salary: "2800 CHF netto" -> salary_min=2800, salary_type="monthly"
- per_diem: "Spesen" = diety. "17 CHF Spesen" -> per_diem=17. null jesli brak
- hours_per_week: "45 godzin tygodniowo" -> 45. Bez konkretnej liczby -> null
- contract_duration: "nieokreslony", "12 miesiecy", "sezonowy". Nie mylij z trial_period!
- trial_period: "okres probny 3 miesiace" -> "3 miesiace"
- canton_raw: JEDEN konkretny kanton albo NULL. Nie wybieraj "glownego" z listy kilku kantonow — wtedy NULL ("Cala Szwajcaria").
- languages: jesli "wymagany niemiecki" bez poziomu -> domyslnie B1
- accommodation_organized: true nawet gdy koszt po stronie pracownika
- seniority_level: null dla wiekszosci prac fizycznych
- benefits: wpisuj WSZYSTKO co oferuje pracodawca: 13. pensja, dodatek urlopowy, odziez robocza, wyzywienie, auto firmowe, szkolenia, ubezpieczenie itp.
"""


# ── Validation helpers ────────────────────────────────────────────────


VALID_CONTRACT_TYPES = {"full_time", "part_time", "temporary", "contract", "internship", "freelance"}
VALID_SALARY_TYPES = {"monthly", "yearly", "hourly", "negotiable"}
VALID_SENIORITY = {"junior", "mid", "senior", "lead", "manager"}


def _safe_int(val) -> int | None:
    if val is None:
        return None
    try:
        v = int(round(float(val)))
        return v if v >= 0 else None
    except (ValueError, TypeError):
        return None


def _safe_number(val) -> float | None:
    """Parse salary values that can be floats (e.g. 33.50 CHF/h)."""
    if val is None:
        return None
    try:
        v = float(val)
        return round(v, 2) if v > 0 else None
    except (ValueError, TypeError):
        return None


def _resolve_canton_from_city(city_name: str | None) -> str | None:
    if not city_name:
        return None
    from app.services.job_processor import CITY_TO_CANTON
    city_lower = city_name.lower().strip()
    if city_lower in CITY_TO_CANTON:
        return CITY_TO_CANTON[city_lower]
    for city_key, canton in CITY_TO_CANTON.items():
        if city_key in city_lower or city_lower in city_key:
            return canton
    return None


def _resolve_canton(canton_raw: str | None, city_name: str | None = None) -> str | None:
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


# ── AI call ───────────────────────────────────────────────────────────


async def _call_extraction_ai(title: str, company: str, description: str, job_id: str | None = None) -> dict | None:
    """Call OpenAI with job extraction prompt. Returns parsed dict or None."""
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping job extraction")
        return None

    prompt = JOB_EXTRACTION_PROMPT.format(
        title=title,
        company=company,
        description=description[:5000],
    )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Jestes ekspertem HR specjalizujacym sie w rynku pracy w Szwajcarii. "
                        "Odpowiadasz wylacznie czystym JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_completion_tokens=4000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty AI response for job extraction")
            return None

        # Track tokens
        try:
            from app.services.ai_usage import track_usage
            if response.usage:
                track_usage(
                    service="extraction",
                    model=response.model or "gpt-4o-mini",
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    job_id=job_id,
                )
        except Exception as e:
            logger.error(f"track_usage failed: {e}")

        return json.loads(content)

    except ImportError:
        logger.error("openai package not installed")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI job extraction response: {e}")
        return None
    except Exception as e:
        logger.error(f"AI job extraction error: {e}")
        return None


# ── Validation ────────────────────────────────────────────────────────


def _validate_extraction(data: dict) -> dict:
    """Validate and normalize all fields from AI response."""
    contract_type = data.get("contract_type", "full_time")
    if contract_type not in VALID_CONTRACT_TYPES:
        contract_type = "full_time"

    salary_type = data.get("salary_type", "monthly")
    if salary_type not in VALID_SALARY_TYPES:
        salary_type = "monthly"

    category_slug = data.get("category_slug", "inne")
    if category_slug not in CATEGORY_SLUGS:
        category_slug = "inne"

    seniority = data.get("seniority_level")
    if seniority and seniority not in VALID_SENIORITY:
        seniority = None

    experience_min = data.get("experience_min", 0)
    if not isinstance(experience_min, int):
        try:
            experience_min = int(experience_min)
        except (ValueError, TypeError):
            experience_min = 0
    experience_min = max(0, min(50, experience_min))

    # Validate languages
    valid_langs = {"de", "fr", "it", "en", "pl", "pt", "es", "hr", "ro", "hu", "sr", "ru", "tr"}
    valid_levels = {"A1", "A2", "B1", "B2", "C1", "C2"}
    cleaned_langs = []
    for entry in (data.get("languages") or []):
        if isinstance(entry, dict):
            lc = entry.get("lang", "")
            lv = entry.get("level", "B1")
            if lc in valid_langs and lv in valid_levels:
                cleaned_langs.append({"lang": lc, "level": lv})

    # Skills
    required_skills = data.get("required_skills") or []
    if not isinstance(required_skills, list):
        required_skills = []
    required_skills = [s for s in required_skills if isinstance(s, str) and s.strip()][:20]

    nice_to_have = data.get("nice_to_have_skills") or []
    if not isinstance(nice_to_have, list):
        nice_to_have = []
    nice_to_have = [s for s in nice_to_have if isinstance(s, str) and s.strip()][:20]

    # Industry tags
    industry_tags = data.get("industry_tags") or []
    if not isinstance(industry_tags, list):
        industry_tags = []
    industry_tags = [t for t in industry_tags if isinstance(t, str) and t.strip()][:10]

    # Keywords
    keywords = data.get("keywords", "")
    if keywords:
        keywords = str(keywords)[:1000]

    # Extended fields
    start_date_text = data.get("start_date_text")
    if start_date_text:
        start_date_text = str(start_date_text).strip()[:100]

    contract_duration = data.get("contract_duration")
    if contract_duration:
        contract_duration = str(contract_duration).strip()[:100]

    per_diem = _safe_int(data.get("per_diem"))
    if per_diem is not None and (per_diem < 1 or per_diem > 200):
        per_diem = None

    hours_per_week = _safe_int(data.get("hours_per_week"))
    if hours_per_week is not None and (hours_per_week < 1 or hours_per_week > 80):
        hours_per_week = None

    benefits = data.get("benefits") or []
    if not isinstance(benefits, list):
        benefits = []
    benefits = [b for b in benefits if isinstance(b, str) and b.strip()][:20]

    education_required = data.get("education_required")
    if education_required:
        education_required = str(education_required).strip()[:200]

    responsibilities = data.get("responsibilities") or []
    if not isinstance(responsibilities, list):
        responsibilities = []
    responsibilities = [r for r in responsibilities if isinstance(r, str) and r.strip()][:20]

    certifications_required = data.get("certifications_required") or []
    if not isinstance(certifications_required, list):
        certifications_required = []
    certifications_required = [c for c in certifications_required if isinstance(c, str) and c.strip()][:10]

    trial_period = data.get("trial_period")
    if trial_period:
        trial_period = str(trial_period).strip()[:100]

    return {
        "category_slug": category_slug,
        "seniority_level": seniority,
        "contract_type": contract_type,
        "city": data.get("city"),
        "canton_raw": data.get("canton_raw"),
        "salary_min": _safe_number(data.get("salary_min")),
        "salary_max": _safe_number(data.get("salary_max")),
        "salary_type": salary_type,
        "experience_min": experience_min,
        "required_skills": required_skills,
        "nice_to_have_skills": nice_to_have,
        "languages": cleaned_langs,
        "driving_license_required": bool(data.get("driving_license_required", False)),
        "car_required": bool(data.get("car_required", False)),
        "own_tools_required": bool(data.get("own_tools_required", False)),
        "accommodation_provided": bool(data.get("accommodation_provided", False)),
        "accommodation_organized": bool(data.get("accommodation_organized", False)),
        "accommodation_deducted": bool(data.get("accommodation_deducted", False)),
        "relocation_support": bool(data.get("relocation_support", False)),
        "coordinator_support": bool(data.get("coordinator_support", False)),
        "cv_german_required": bool(data.get("cv_german_required", False)),
        "keywords": keywords,
        "industry_tags": industry_tags,
        "start_date_text": start_date_text,
        "contract_duration": contract_duration,
        "trial_period": trial_period,
        "per_diem": per_diem,
        "hours_per_week": hours_per_week,
        "benefits": benefits,
        "education_required": education_required,
        "responsibilities": responsibilities,
        "certifications_required": certifications_required,
    }


# ── Mapping to JobOffer ──────────────────────────────────────────────


def map_extraction_to_job(job: JobOffer, data: dict) -> None:
    """Map validated extraction data to a JobOffer instance.

    Metadata only — title/description are never modified by extraction.
    Translation handles title/description for scraped jobs separately.
    """
    job.contract_type = data["contract_type"]
    job.experience_min = data["experience_min"]
    job.car_required = data["car_required"]
    job.driving_license_required = data["driving_license_required"]
    job.own_tools_required = data.get("own_tools_required", False)

    if data["languages"]:
        job.languages_required = data["languages"]

    if data["salary_min"] is not None:
        job.salary_min = float(data["salary_min"])
    if data["salary_max"] is not None:
        job.salary_max = float(data["salary_max"])
    if data["salary_type"]:
        job.salary_type = data["salary_type"]

    # Resolve canton from AI response (single canton or NULL = Cała Szwajcaria)
    canton = _resolve_canton(data.get("canton_raw"), data.get("city"))
    # NIE nadpisuj scraped city/canton wartoscia NULL — zachowaj dane ze scrapera
    if canton:
        job.canton = canton
    job.cantons = None  # multi-canton deprecated
    if data.get("city"):
        job.city = data["city"][:100]

    job.seniority_level = data.get("seniority_level")
    job.accommodation_provided = data.get("accommodation_provided", False)
    job.accommodation_organized = data.get("accommodation_organized", False)
    job.accommodation_deducted = data.get("accommodation_deducted", False)
    job.relocation_support = data.get("relocation_support", False)
    job.coordinator_support = data.get("coordinator_support", False)
    job.cv_german_required = data.get("cv_german_required", False)
    job.skills = data.get("required_skills") or []
    job.nice_to_have_skills = data.get("nice_to_have_skills") or []
    job.industry_tags = data.get("industry_tags") or []

    keywords = data.get("keywords", "")
    if keywords:
        job.ai_keywords = keywords[:1000]

    if data.get("start_date_text"):
        job.start_date_text = data["start_date_text"]
    if data.get("contract_duration"):
        job.contract_duration = data["contract_duration"]
    if data.get("trial_period"):
        job.trial_period = data["trial_period"]
    if data.get("per_diem") is not None:
        job.per_diem = data["per_diem"]
    if data.get("hours_per_week") is not None:
        job.hours_per_week = data["hours_per_week"]
    if data.get("benefits"):
        job.benefits = data["benefits"]
    if data.get("education_required"):
        job.education_required = data["education_required"]
    if data.get("responsibilities"):
        job.responsibilities = data["responsibilities"]
    if data.get("certifications_required"):
        job.certifications_required = data["certifications_required"]

    # Store full extraction result
    job.extracted_data = data


# ── Single job extraction pipeline ───────────────────────────────────


async def extract_single_job(job_id: str, session_factory=None) -> bool:
    """Full metadata extraction pipeline for a single job.

    Status flow: pending -> processing -> completed/failed
    Extracts metadata only — title/description are not modified.

    Returns True if extraction succeeded, False otherwise.
    """
    _sf = session_factory or async_session
    async with _sf() as db:
        from sqlalchemy.orm import selectinload
        result = await db.execute(
            select(JobOffer)
            .options(selectinload(JobOffer.employer))
            .where(JobOffer.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"JobOffer {job_id} not found")
            return False

        if not job.description:
            logger.warning(f"JobOffer {job_id} has no description, marking failed")
            job.extraction_status = "failed"
            await db.commit()
            return False

        # Check max attempts
        if job.extraction_attempts >= MAX_EXTRACTION_ATTEMPTS:
            logger.warning(f"JobOffer {job_id} exceeded max extraction attempts")
            job.extraction_status = "failed"
            await db.commit()
            return False

        # Mark as processing
        job.extraction_status = "processing"
        job.extraction_attempts += 1
        await db.commit()

        # Strip HTML for AI input
        from app.core.sanitize import strip_all_html
        raw_text = strip_all_html(job.description)

        # Get company name from employer profile
        company_name = ""
        if job.employer:
            company_name = job.employer.company_name or ""

        # Call AI
        ai_data = await _call_extraction_ai(
            title=job.title,
            company=company_name,
            description=raw_text,
            job_id=str(job.id),
        )

        if ai_data is None:
            job.extraction_status = "pending" if job.extraction_attempts < MAX_EXTRACTION_ATTEMPTS else "failed"
            await db.commit()
            await log_activity(
                "job_extraction_failed",
                f"AI extraction failed for: {job.title[:80]} (attempt {job.extraction_attempts})",
                entity_type="job_offer",
                entity_id=job.id,
                session_factory=_sf,
            )
            return False

        # Validate and map
        validated = _validate_extraction(ai_data)

        map_extraction_to_job(job, validated)

        # Resolve category
        from app.models.category import Category
        cat_slug = validated.get("category_slug", "inne")
        cat_result = await db.execute(
            select(Category.id).where(Category.slug == cat_slug)
        )
        cat_id = cat_result.scalar_one_or_none()
        if cat_id:
            job.category_id = cat_id

        # Mark completed
        job.extraction_status = "completed"
        job.extraction_version = EXTRACTION_VERSION
        job.match_ready = True
        job.ai_extracted = True

        await db.commit()

        await log_activity(
            "job_extraction_completed",
            f"AI extraction completed for: {job.title[:80]}",
            entity_type="job_offer",
            entity_id=job.id,
            details={
                "category": cat_slug,
                "skills_count": len(validated.get("required_skills", [])),
            },
            session_factory=_sf,
        )
        logger.info(f"Job extraction completed for {job_id}")
        return True


# ── Batch processor ──────────────────────────────────────────────────


async def process_pending_job_extractions(session_factory=None) -> int:
    """Process pending job extractions in batches.

    Called by scheduler every 3 minutes. Processes up to 10 at a time.
    Only picks up active jobs (scraped jobs must be translated+activated first).
    Returns number of successfully processed jobs.
    """
    _sf = session_factory or async_session
    async with _sf() as db:
        result = await db.execute(
            select(JobOffer.id)
            .where(
                JobOffer.extraction_status == "pending",
                JobOffer.status == "active",
                JobOffer.description.isnot(None),
                JobOffer.extraction_attempts < MAX_EXTRACTION_ATTEMPTS,
            )
            .order_by(JobOffer.created_at.asc())
            .limit(10)
        )
        pending_ids = [row[0] for row in result.all()]

    if not pending_ids:
        return 0

    logger.info(f"Processing {len(pending_ids)} pending job extraction(s)")
    success_count = 0
    for job_id in pending_ids:
        if await extract_single_job(job_id, session_factory=_sf):
            success_count += 1

    logger.info(f"Job extraction batch: {success_count}/{len(pending_ids)} succeeded")
    return success_count
