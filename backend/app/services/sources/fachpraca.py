"""FACHPRACA source fetcher.

Fetches job postings from fachpraca.pl XML feed and returns them as
standardized RawJobData objects for the generic job processor.
"""
import asyncio
import html
import logging
import xml.etree.ElementTree as ET

import cloudscraper

from app.config import get_settings
from app.services.job_processor import RawJobData

logger = logging.getLogger(__name__)

# ── Blocked companies (same list as JOBSPL) ─────────────────────────────

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


# ── Helpers ──────────────────────────────────────────────────────────────

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

async def fetch_fachpraca() -> list[RawJobData]:
    """Fetch and parse the FACHPRACA XML feed.

    Returns list of RawJobData, with blocked companies already filtered out.
    """
    settings = get_settings()
    url = settings.FACHPRACA_FEED_URL

    try:
        # Use cloudscraper to bypass Cloudflare JS challenge
        scraper = cloudscraper.create_scraper()
        response = await asyncio.to_thread(scraper.get, url, timeout=60)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"Failed to fetch FACHPRACA feed: {e}")
        return []

    try:
        root = ET.fromstring(response.content)
        _decode_html_entities(root)
    except ET.ParseError as e:
        logger.error(f"Failed to parse FACHPRACA XML: {e}")
        return []

    jobs: list[RawJobData] = []
    filtered_count = 0

    for ad in root.findall("Advert"):
        offer_id = _get_element_text(ad, "Id")
        if not offer_id:
            continue

        employer_name = _get_element_text(ad, "CompanyName") or ""
        employer_name = _normalize_employer(employer_name)

        if _is_company_blocked(employer_name):
            filtered_count += 1
            continue

        jobs.append(RawJobData(
            source_id=f"FACHPRACA{offer_id}",
            source_name="FACHPRACA",
            title=_get_element_text(ad, "Title") or "",
            company_name=employer_name,
            description=_get_element_text(ad, "Description") or "",
            requirements="",
            benefits="",
            city=_get_element_text(ad, "City"),
            country=_get_element_text(ad, "Country") or "Szwajcaria",
            url=_get_element_text(ad, "ApplicationUrl"),
            salary_from=_get_element_text(ad, "SalaryFrom"),
            salary_to=_get_element_text(ad, "SalaryTo"),
            salary_currency=_get_element_text(ad, "Currency") or "CHF",
            recruiter_type="polish",
        ))

    logger.info(
        f"Fetched {len(jobs)} jobs from FACHPRACA feed "
        f"(filtered {filtered_count} blocked)"
    )
    return jobs
