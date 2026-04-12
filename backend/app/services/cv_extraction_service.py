"""Unified CV data extraction service.

Handles background AI extraction for both CV intake flows:
- Flow 1: "Sprawdz CV" → "Zapisz do bazy" (has CVReview)
- Flow 2: Worker uploads CV to profile (has CVFile)

Extracts normalized columns for programmatic job-CV matching.
"""
import json
import logging

from sqlalchemy import select
from app.config import get_settings
from app.database import async_session
from app.models.cv_database import CVDatabase
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)

# Bump this when prompt changes to trigger re-extraction
EXTRACTION_VERSION = 1

CV_UNIFIED_EXTRACTION_PROMPT = """Przeanalizuj poniższy tekst CV i wyciągnij z niego strukturalne dane. Zwróć wynik jako czysty JSON (bez markdown code blocks).

Zwróć JSON z następującymi polami:
{
  "full_name": "<imię i nazwisko lub null>",
  "email": "<email lub null>",
  "phone": "<numer telefonu lub null>",
  "location": "<kraj zamieszkania osoby, np. 'Polska', 'Szwajcaria', 'Niemcy'. Jeśli nie podano wprost, wywnioskuj z ostatniego miejsca pracy lub adresu. Null jeśli brak danych>",
  "experience_years": <łączna liczba lat doświadczenia jako integer, zsumuj okresy pracy. 0 jeśli brak>,
  "experience_entries": [
    {
      "position": "<stanowisko>",
      "company": "<firma>",
      "from": "<rok rozpoczęcia np. '2020'>",
      "to": "<rok zakończenia np. '2023' lub 'obecnie'>",
      "months": <przybliżona liczba miesięcy>
    }
  ],
  "category_slugs": ["<slug kategorii z listy poniżej>"],
  "skills": ["<konkretna umiejętność 1>", "<konkretna umiejętność 2>"],
  "keywords": "<słowa kluczowe oddzielone średnikiem, np. 'spawacz; spawanie; MIG; MAG; monter'>",
  "languages": [
    {"lang": "<kod ISO 639-1: pl, de, fr, en, it, etc.>", "level": "<poziom CEFR: A1, A2, B1, B2, C1, C2 lub native>"}
  ],
  "driving_license": ["<kategoria np. B, C, CE lub pusta lista>"],
  "has_car": <true/false - czy posiada samochód>,
  "education": [
    {"degree": "<tytuł/stopień/kierunek>", "institution": "<uczelnia/szkoła>", "year": "<rok ukończenia lub null>"}
  ]
}

Dostępne kategorie (category_slugs) - wybierz pasujące z listy:
budownictwo, gastronomia, opieka, transport, it, sprzatanie, produkcja, handel, finanse, administracja, rolnictwo, inne

Zasady:
- Jeśli jakiegoś pola nie da się wyciągnąć, ustaw null, 0 lub pustą tablicę []
- Języki: zawsze używaj kodów ISO 639-1 (pl, de, fr, en, it, etc.) i poziomów CEFR
- Prawo jazdy: zwracaj jako tablicę kategorii, np. ["B"] lub ["B", "C", "CE"]
- Kategorie: dopasuj do listy powyżej na podstawie doświadczenia i umiejętności
- Keywords: wypisz synonimy stanowisk, umiejętności i słowa kluczowe po średniku
- experience_years: oblicz sumę miesięcy ze wszystkich pozycji i zaokrąglij do lat
- location: kraj zamieszkania, NIE kraj pracy

TEKST CV:
"""


async def extract_cv_data_unified(cv_text: str) -> dict | None:
    """Call OpenAI to extract structured data from CV text.

    Returns parsed dict or None on failure.
    """
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping AI extraction")
        return None

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś asystentem HR. Odpowiadasz wyłącznie czystym JSON bez żadnego formatowania markdown.",
                },
                {
                    "role": "user",
                    "content": CV_UNIFIED_EXTRACTION_PROMPT + cv_text[:8000],
                },
            ],
            temperature=0.1,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty response from OpenAI CV extraction")
            return None

        return json.loads(content)

    except ImportError:
        logger.error("openai package not installed")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI extraction response: {e}")
        return None
    except Exception as e:
        logger.error(f"OpenAI CV extraction error: {e}")
        return None


def map_extraction_to_cv_database(cv_db: CVDatabase, data: dict) -> None:
    """Map AI extraction result to CVDatabase normalized columns.

    Does NOT overwrite human-provided name/email/phone if already set.
    """
    # Only fill name/email/phone if not already set by form
    if not cv_db.full_name and data.get("full_name"):
        cv_db.full_name = data["full_name"]
    if not cv_db.email and data.get("email"):
        cv_db.email = data["email"]
    if not cv_db.phone and data.get("phone"):
        cv_db.phone = data["phone"]

    # Always overwrite AI-derived fields
    cv_db.location = data.get("location")
    cv_db.experience_years = data.get("experience_years") or 0
    cv_db.experience_entries = data.get("experience_entries") or []
    cv_db.category_slugs = data.get("category_slugs") or []
    cv_db.skills = data.get("skills") or []
    cv_db.ai_keywords = data.get("keywords") or ""
    cv_db.education = data.get("education") or []

    # Languages: merge form-provided + AI-extracted (AI fills gaps)
    ai_languages = data.get("languages") or []
    if ai_languages and not cv_db.languages:
        cv_db.languages = ai_languages

    # Driving license: AI extraction as list
    ai_license = data.get("driving_license")
    if ai_license and not cv_db.driving_license:
        if isinstance(ai_license, list):
            cv_db.driving_license = ai_license
        elif isinstance(ai_license, str):
            cv_db.driving_license = [ai_license]

    # has_car: only set from AI if not already True
    if not cv_db.has_car and data.get("has_car"):
        cv_db.has_car = True

    # Store full AI response as extracted_data
    cv_db.extracted_data = data


async def process_single_cv_extraction(cv_db_id: str, session_factory=None) -> bool:
    """Full pipeline: fetch record -> mark processing -> AI call -> save results.

    Args:
        cv_db_id: CVDatabase record ID to process.
        session_factory: Optional async session factory (for testing).
            Defaults to app.database.async_session.

    Returns True if extraction succeeded, False otherwise.
    """
    _session_factory = session_factory or async_session
    async with _session_factory() as db:
        result = await db.execute(
            select(CVDatabase).where(CVDatabase.id == cv_db_id)
        )
        cv_db = result.scalar_one_or_none()
        if not cv_db:
            logger.error(f"CVDatabase {cv_db_id} not found")
            return False

        if not cv_db.cv_text:
            logger.warning(f"CVDatabase {cv_db_id} has no cv_text, marking failed")
            cv_db.extraction_status = "failed"
            await db.commit()
            return False

        # Mark as processing
        cv_db.extraction_status = "processing"
        await db.commit()

        # AI extraction
        data = await extract_cv_data_unified(cv_db.cv_text)

        if data is None:
            cv_db.extraction_status = "failed"
            await db.commit()
            await log_activity(
                "cv_extraction_failed",
                f"AI extraction failed for CV: {cv_db.full_name or cv_db.email or cv_db_id}",
                entity_type="cv_database", entity_id=cv_db_id,
                session_factory=_session_factory,
            )
            return False

        # Map results to columns
        map_extraction_to_cv_database(cv_db, data)
        cv_db.extraction_status = "completed"
        cv_db.extraction_version = EXTRACTION_VERSION
        cv_db.match_ready = True
        await db.commit()

        await log_activity(
            "cv_extraction_completed",
            f"AI extraction completed for CV: {cv_db.full_name or cv_db.email or cv_db_id}",
            entity_type="cv_database", entity_id=cv_db_id,
            details={"categories": data.get("category_slugs"), "experience_years": data.get("experience_years")},
            session_factory=_session_factory,
        )
        logger.info(f"CV extraction completed for {cv_db_id}")
        return True


async def process_pending_cv_extractions(session_factory=None) -> int:
    """Pick up ALL pending CVDatabase records and process them sequentially.

    Called by scheduler every 2 minutes. Processes every pending record
    in one run, oldest first.

    Args:
        session_factory: Optional async session factory (for testing).

    Returns number of successfully processed records.
    """
    _session_factory = session_factory or async_session
    async with _session_factory() as db:
        result = await db.execute(
            select(CVDatabase.id)
            .where(CVDatabase.extraction_status == "pending")
            .where(CVDatabase.cv_text.isnot(None))
            .order_by(CVDatabase.created_at.asc())
        )
        pending_ids = [row[0] for row in result.all()]

    if not pending_ids:
        return 0

    logger.info(f"Processing {len(pending_ids)} pending CV extraction(s)")
    success_count = 0
    for cv_id in pending_ids:
        if await process_single_cv_extraction(cv_id, session_factory=_session_factory):
            success_count += 1

    logger.info(f"CV extraction batch: {success_count}/{len(pending_ids)} succeeded")
    return success_count
