"""Company-level overrides for the apply flow.

When a job is sourced from one of these companies (matched by employer.company_name,
case-insensitive, with surrounding whitespace stripped), we force the apply path to go
through our internal email form instead of an external URL.

The list lives in the DB table `company_overrides` (manage via /admin) with a small
hardcoded fallback for resilience if the table is empty.
"""
from __future__ import annotations

import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session
from app.models.company_override import CompanyOverride

logger = logging.getLogger(__name__)

# Fallback used if the DB lookup fails (e.g. on fresh deploy before migration).
_FALLBACK_OVERRIDES: dict[str, str] = {
    "njujob": "praca@njujob.pl",
}

# Module-level cache (loaded on demand, invalidated by admin endpoints after edits).
_cache: dict[str, str] | None = None


def _normalize(name: str | None) -> str:
    return (name or "").strip().lower()


async def _load_cache(db: AsyncSession | None = None) -> dict[str, str]:
    global _cache
    try:
        if db is None:
            async with async_session() as session:
                result = await session.execute(select(CompanyOverride))
                rows = result.scalars().all()
        else:
            result = await db.execute(select(CompanyOverride))
            rows = result.scalars().all()
        loaded = {row.company_key: row.apply_email for row in rows}
        # Hardcoded entries fill gaps but do not override DB
        for k, v in _FALLBACK_OVERRIDES.items():
            loaded.setdefault(k, v)
        _cache = loaded
    except Exception as e:
        logger.warning(f"company_overrides DB load failed: {e}; falling back to hardcoded list")
        _cache = dict(_FALLBACK_OVERRIDES)
    return _cache


def invalidate_cache() -> None:
    """Call after admin updates the overrides table."""
    global _cache
    _cache = None


def get_override_email_sync(company_name: str | None) -> str | None:
    """Sync lookup against the cache (cache must already be warm)."""
    key = _normalize(company_name)
    if not key:
        return None
    cache = _cache if _cache is not None else _FALLBACK_OVERRIDES
    return cache.get(key)


async def ensure_cache_loaded() -> None:
    if _cache is None:
        await _load_cache()


def apply_company_override(job) -> None:
    """Mutate a JobOffer-like object in place so apply_via -> 'email' for overridden companies.

    Sync; assumes the cache has been warmed up. If cache is cold, falls back to hardcoded list.
    """
    employer = getattr(job, "employer", None)
    company_name = getattr(employer, "company_name", None) if employer else None
    override_email = get_override_email_sync(company_name)
    if not override_email:
        return
    job.apply_via = "email"
    job.contact_email = override_email
    job.external_url = None


async def apply_company_overrides_async(jobs: list) -> None:
    """Warm the cache then apply to a list of jobs."""
    await ensure_cache_loaded()
    for job in jobs:
        apply_company_override(job)
