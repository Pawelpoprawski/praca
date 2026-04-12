"""ADECCO source fetcher.

Fetches job postings from Adecco Channable XML feed and returns them as
standardized RawJobData objects for the generic job processor.
"""
import logging
import xml.etree.ElementTree as ET

import httpx

from app.config import get_settings
from app.services.job_processor import RawJobData

logger = logging.getLogger(__name__)

# ── German words filter (untranslated titles are skipped) ────────────────

GERMAN_TITLE_FILTERS = [
    "monteur", "praktik", "beiter", "montage", "dichter",
    "ü", "Fach", "fach", "Facilit", "bauer", "Hoch",
    "Kauf", "Immobilie", "kunde",
]

GERMAN_DESC_FILTERS = [
    "unseren",
]


def _is_untranslated(title: str, description: str) -> bool:
    """Check if the job appears to be untranslated German."""
    for word in GERMAN_TITLE_FILTERS:
        if word in title:
            return True
    for word in GERMAN_DESC_FILTERS:
        if word in description:
            return True
    return False


# ── Main fetch function ──────────────────────────────────────────────────

async def fetch_adecco() -> list[RawJobData]:
    """Fetch and parse the Adecco Channable XML feed.

    Returns list of RawJobData. Untranslated German jobs are filtered out.
    """
    settings = get_settings()
    url = settings.ADECCO_FEED_URL

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
    except httpx.HTTPError as e:
        logger.error(f"Failed to fetch ADECCO feed: {e}")
        return []

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        logger.error(f"Failed to parse ADECCO XML: {e}")
        return []

    jobs: list[RawJobData] = []
    seen_ids: set[str] = set()
    filtered_count = 0

    # Adecco XML has flat row elements; detect tag name from first child
    for item in root:
        id_ref = item.findtext("id_reference")
        if not id_ref:
            continue

        # Deduplicate (Adecco feed can have duplicate id_reference)
        if id_ref in seen_ids:
            continue
        seen_ids.add(id_ref)

        title = item.findtext("job_title") or ""
        description = item.findtext("text_description") or ""

        # Filter untranslated German titles
        if _is_untranslated(title, description):
            filtered_count += 1
            continue

        city = item.findtext("location_city")
        apply_url = item.findtext("url_apply")

        jobs.append(RawJobData(
            source_id=f"ADECCO{id_ref}",
            source_name="ADECCO",
            title=title,
            company_name="Adecco",
            description=description,
            requirements="",
            benefits="",
            city=city,
            country="Szwajcaria",
            url=apply_url,
            salary_from=None,
            salary_to=None,
            salary_currency="CHF",
            recruiter_type="swiss",
        ))

    logger.info(
        f"Fetched {len(jobs)} jobs from ADECCO feed "
        f"(filtered {filtered_count} untranslated, "
        f"deduplicated from {len(seen_ids) + filtered_count} total)"
    )
    return jobs
