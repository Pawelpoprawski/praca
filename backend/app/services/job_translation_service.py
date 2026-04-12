"""Job translation service — DE/FR/IT -> Polish.

Step 1 of the two-step pipeline for scraped jobs:
1. Translation (this service): translate foreign-language title/description to Polish, activate job
2. Extraction (job_extraction_service): extract metadata from Polish text

Manual employer jobs skip translation entirely (already Polish + already active).
"""
import json
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.config import get_settings
from app.database import async_session
from app.models.job_offer import JobOffer
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)

TRANSLATION_VERSION = 1
MAX_TRANSLATION_ATTEMPTS = 3

JOB_TRANSLATION_PROMPT = """Przetlumacz ponizszy tekst oferty pracy na jezyk polski.

Tytul: {title}
Firma: {company}
Opis: {description}

Zwroc JSON z polami:
{{
  "translated_title": "<oczyszczony tytul po polsku - usun '100%', '(w/m/d)', '(m/w/d)', 'EFZ', procenty, kody stanowisk>",
  "translated_description": "<HTML z sekcjami: <h3>Opis stanowiska</h3>, <h3>Wymagania</h3>, <h3>Oferujemy</h3>. Uzyj tagow: p, br, strong, em, ul, ol, li, h3, h4. Sformatuj profesjonalnie>"
}}

Zasady:
- Przetlumacz caly tekst na polski (z niemieckiego, francuskiego lub wloskiego)
- Usun z tytulu: EFZ, 100%, (m/w/d), (w/m/d), procenty, kody
- Formatowanie: punkty z duzej litery, zdania z kropka, profesjonalny styl
- USUN znaki specjalne: =>  -> ➜ ► ★ ✓ ●. Wypunktowania jako <ul><li>
- Zachowaj nazwy wlasne firm i certyfikatow w oryginale
"""


# ── AI call ───────────────────────────────────────────────────────────


async def _call_translation_ai(title: str, company: str, description: str) -> dict | None:
    """Call OpenAI with translation prompt. Returns parsed dict or None."""
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping job translation")
        return None

    prompt = JOB_TRANSLATION_PROMPT.format(
        title=title,
        company=company,
        description=description[:5000],
    )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Jestes profesjonalnym tlumaczem specjalizujacym sie "
                        "w tlumaczeniu ofert pracy z niemieckiego, francuskiego "
                        "i wloskiego na polski. Odpowiadasz wylacznie czystym JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=2000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty AI response for job translation")
            return None

        return json.loads(content)

    except ImportError:
        logger.error("openai package not installed")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI translation response: {e}")
        return None
    except Exception as e:
        logger.error(f"AI job translation error: {e}")
        return None


# ── Validation ────────────────────────────────────────────────────────


def _validate_translation(data: dict) -> dict:
    """Validate translation response fields."""
    translated_title = data.get("translated_title", "")
    if not isinstance(translated_title, str):
        translated_title = ""
    translated_title = translated_title.strip()[:255]

    translated_description = data.get("translated_description", "")
    if not isinstance(translated_description, str):
        translated_description = ""
    translated_description = translated_description.strip()

    return {
        "translated_title": translated_title,
        "translated_description": translated_description,
    }


# ── Single job translation pipeline ──────────────────────────────────


async def translate_single_job(job_id: str, session_factory=None) -> bool:
    """Full translation pipeline for a single scraped job.

    Status flow: pending -> processing -> completed/failed
    On success: overwrites title/description with Polish, activates job,
    ensures extraction_status='pending' so extraction picks it up next.

    Returns True if translation succeeded, False otherwise.
    """
    _sf = session_factory or async_session
    async with _sf() as db:
        result = await db.execute(
            select(JobOffer).where(JobOffer.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"JobOffer {job_id} not found for translation")
            return False

        if not job.description:
            logger.warning(f"JobOffer {job_id} has no description, marking translation failed")
            job.translation_status = "failed"
            await db.commit()
            return False

        # Check max attempts
        if job.translation_attempts >= MAX_TRANSLATION_ATTEMPTS:
            logger.warning(f"JobOffer {job_id} exceeded max translation attempts")
            job.translation_status = "failed"
            await db.commit()
            return False

        # Mark as processing
        job.translation_status = "processing"
        job.translation_attempts += 1
        await db.commit()

        # Strip HTML for AI input
        from app.core.sanitize import strip_all_html
        raw_text = strip_all_html(job.description)

        # Call AI
        ai_data = await _call_translation_ai(
            title=job.title,
            company="",
            description=raw_text,
        )

        if ai_data is None:
            job.translation_status = "pending" if job.translation_attempts < MAX_TRANSLATION_ATTEMPTS else "failed"
            await db.commit()
            await log_activity(
                "job_translation_failed",
                f"AI translation failed for: {job.title[:80]} (attempt {job.translation_attempts})",
                entity_type="job_offer",
                entity_id=job.id,
                session_factory=_sf,
            )
            return False

        # Validate
        validated = _validate_translation(ai_data)

        if not validated["translated_title"] and not validated["translated_description"]:
            job.translation_status = "pending" if job.translation_attempts < MAX_TRANSLATION_ATTEMPTS else "failed"
            await db.commit()
            return False

        # Apply translation
        from app.core.sanitize import sanitize_html

        if validated["translated_title"]:
            job.title = validated["translated_title"]
        if validated["translated_description"]:
            job.description = sanitize_html(validated["translated_description"])

        # Activate job
        now = datetime.now(timezone.utc)
        job.status = "active"
        job.published_at = now
        job.expires_at = now + timedelta(days=30)

        # Mark translation complete, ensure extraction picks it up
        job.translation_status = "completed"
        job.extraction_status = "pending"

        await db.commit()

        await log_activity(
            "job_translation_completed",
            f"AI translation completed for: {job.title[:80]}",
            entity_type="job_offer",
            entity_id=job.id,
            session_factory=_sf,
        )
        logger.info(f"Job translation completed for {job_id}")
        return True


# ── Batch processor ──────────────────────────────────────────────────


async def process_pending_job_translations(session_factory=None) -> int:
    """Process pending job translations in batches.

    Called by scheduler every 2 minutes. Processes up to 10 at a time.
    Only picks up scraped jobs (source_name IS NOT NULL).
    Returns number of successfully processed jobs.
    """
    _sf = session_factory or async_session
    async with _sf() as db:
        result = await db.execute(
            select(JobOffer.id)
            .where(
                JobOffer.translation_status == "pending",
                JobOffer.source_name.isnot(None),
                JobOffer.description.isnot(None),
                JobOffer.translation_attempts < MAX_TRANSLATION_ATTEMPTS,
            )
            .order_by(JobOffer.created_at.asc())
            .limit(10)
        )
        pending_ids = [row[0] for row in result.all()]

    if not pending_ids:
        return 0

    logger.info(f"Processing {len(pending_ids)} pending job translation(s)")
    success_count = 0
    for job_id in pending_ids:
        if await translate_single_job(job_id, session_factory=_sf):
            success_count += 1

    logger.info(f"Job translation batch: {success_count}/{len(pending_ids)} succeeded")
    return success_count
