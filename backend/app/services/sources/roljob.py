"""ROLJOB source fetcher.

Fetches job postings from rol-jobhliwa.ch XML feed and returns them as
standardized RawJobData objects for the generic job processor.
"""
import html
import logging
import re
import xml.etree.ElementTree as ET

import httpx

from app.config import get_settings
from app.services.job_processor import RawJobData

logger = logging.getLogger(__name__)


# ── Helpers ──────────────────────────────────────────────────────────────

def _parse_salary_from_description(desc: str) -> tuple[str | None, str | None, str]:
    """Extract salary info from job description text.

    Returns (salary_from, salary_to, currency).
    """
    match = re.search(
        r'Wynagrodzenie:\s*(?:od)?\s*([\d\s.,]+)'
        r'(?:\s*[-\u2013]\s*([\d\s.,]+))?\s*(CHF)?',
        desc,
    )
    if not match:
        return None, None, "CHF"

    salary_from = match.group(1).replace(" ", "").replace(",", ".")
    salary_to = match.group(2)
    if salary_to:
        salary_to = salary_to.replace(" ", "").replace(",", ".")
    currency = match.group(3) or "CHF"
    return salary_from, salary_to, currency


def _parse_requirements(desc: str) -> str:
    """Extract requirements from <li> tags in description."""
    items = re.findall(r'<li[^>]*>(.*?)</li>', desc, re.DOTALL)
    cleaned = [
        html.unescape(re.sub(r'<[^<]+?>', '', item)).strip()
        for item in items
    ]
    return "\n".join(cleaned)


def _parse_offers(desc: str) -> str:
    """Extract employer offers from <b>Key:</b> Value patterns."""
    matches = re.findall(r'<b>([^:]+):</b>\s*([^<]+)', desc)
    return "\n".join(f"{k.strip()}: {v.strip()}" for k, v in matches)


# ── Main fetch function ──────────────────────────────────────────────────

async def fetch_roljob() -> list[RawJobData]:
    """Fetch and parse the ROLJOB XML feed.

    Returns list of RawJobData.
    """
    settings = get_settings()
    url = settings.ROLJOB_FEED_URL

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
        logger.error(f"Failed to fetch ROLJOB feed: {e}")
        return []

    try:
        root = ET.fromstring(response.content)
    except ET.ParseError as e:
        logger.error(f"Failed to parse ROLJOB XML: {e}")
        return []

    jobs: list[RawJobData] = []

    for job_el in root.findall("job"):
        job_id = job_el.findtext("id")
        if not job_id:
            continue

        title = job_el.findtext("title") or ""
        link = job_el.findtext("link")
        company = job_el.findtext("company") or ""
        country = job_el.findtext("country") or "Szwajcaria"
        region = job_el.findtext("region")

        desc_raw = job_el.findtext("description") or ""
        desc = html.unescape(desc_raw) if desc_raw else ""

        salary_from, salary_to, currency = _parse_salary_from_description(desc)
        requirements = _parse_requirements(desc)
        offers = _parse_offers(desc)

        jobs.append(RawJobData(
            source_id=f"ROLJOB{job_id}",
            source_name="ROLJOB",
            title=title,
            company_name=company,
            description=desc.strip(),
            requirements=requirements,
            benefits=offers,
            city=region,
            country=country,
            url=link,
            salary_from=salary_from,
            salary_to=salary_to,
            salary_currency=currency,
            recruiter_type="polish",
        ))

    logger.info(f"Fetched {len(jobs)} jobs from ROLJOB feed")
    return jobs
