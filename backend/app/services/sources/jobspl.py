"""JOBSPL source fetcher.

Fetches job postings from jobs.pl XML feed and returns them as
standardized RawJobData objects for the generic job processor.
"""
import html
import logging
import xml.etree.ElementTree as ET

import httpx

from app.config import get_settings
from app.services.job_processor import RawJobData

logger = logging.getLogger(__name__)

# ── Blocked companies (skipped during import) ────────────────────────────

BLOCKED_COMPANIES = [
    "Pemsa",
    "Soccey",
    "yellowshark\u00ae AG",
    "Gastro",
    "Prima",
    "Excellent",
    "Astral Limited",
    "MICHA\u0141 KU\u015a",
    "ISMIRA",
    "Veragouth",
    "SILVERHAND",
]


# ── XML helpers ──────────────────────────────────────────────────────────

def _decode_html_entities(element: ET.Element) -> None:
    """Recursively decode HTML entities in XML element text."""
    if element.text:
        element.text = html.unescape(element.text)
    if element.tail:
        element.tail = html.unescape(element.tail)
    for child in element:
        _decode_html_entities(child)


def _get_element_text(ad: ET.Element, path: str) -> str | None:
    """Safely extract text from an XML element at the given path."""
    el = ad.find(path)
    if el is not None and el.text:
        return html.unescape(el.text.strip())
    return None


def _is_company_blocked(employer_name: str) -> bool:
    """Check if the employer is in the blocked list."""
    for blocked in BLOCKED_COMPANIES:
        if blocked.lower() in employer_name.lower():
            return True
    return False


def _normalize_employer(name: str) -> str:
    """Normalize known employer name variants."""
    if "PolFach" in name:
        return "PolFach"
    if "Excellent Personal" in name:
        return "Excellent Personal"
    if "ADK Sp. z o.o." in name:
        return "ADK"
    return name


# ── Main fetch function ──────────────────────────────────────────────────

async def fetch_jobspl() -> list[RawJobData]:
    """Fetch and parse the JOBSPL XML feed.

    Returns list of RawJobData, with blocked companies already filtered out.
    """
    settings = get_settings()
    url = settings.JOBSPL_FEED_URL

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
        logger.error(f"Failed to fetch JOBSPL feed: {e}")
        return []

    try:
        root = ET.fromstring(response.content)
        _decode_html_entities(root)
    except ET.ParseError as e:
        logger.error(f"Failed to parse JOBSPL XML: {e}")
        return []

    jobs: list[RawJobData] = []
    filtered_count = 0

    for ad in root.findall("Ad"):
        offer_id = _get_element_text(ad, "offer_id")
        if not offer_id:
            continue

        employer_name = _get_element_text(ad, "employer_name") or ""
        employer_name = _normalize_employer(employer_name)

        # Filter blocked companies during fetch
        if _is_company_blocked(employer_name):
            filtered_count += 1
            continue

        jobs.append(RawJobData(
            source_id=f"JOBSPL{offer_id}",
            source_name="JOBSPL",
            title=_get_element_text(ad, "job_title") or "",
            company_name=employer_name,
            description=_get_element_text(ad, "job_desc") or "",
            requirements=_get_element_text(ad, "job_needs") or "",
            benefits=_get_element_text(ad, "job_company_offers") or "",
            city=_get_element_text(ad, "locations/locations_1/city_name"),
            country=_get_element_text(ad, "locations/locations_1/country_name") or "Szwajcaria",
            url=_get_element_text(ad, "en_offer_url"),
            salary_from=_get_element_text(ad, "salary_scope_from"),
            salary_to=_get_element_text(ad, "salary_scope_to"),
            salary_currency=_get_element_text(ad, "salary_currency") or "CHF",
            recruiter_type="polish",
        ))

    logger.info(
        f"Fetched {len(jobs)} jobs from JOBSPL feed "
        f"(filtered {filtered_count} blocked)"
    )
    return jobs
