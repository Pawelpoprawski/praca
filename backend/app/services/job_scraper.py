"""Job scraper orchestrator.

Thin orchestration layer that coordinates source fetchers with the
generic job processor. Manages sync state and status reporting.
"""
import logging
from datetime import datetime, timezone

from sqlalchemy import select, func as sa_func

from app.config import get_settings
from app.database import async_session
from app.models.job_offer import JobOffer
from app.services.job_processor import SyncResult, process_jobs
from app.services.sources.jobspl import fetch_jobspl
from app.services.sources.fachpraca import fetch_fachpraca
from app.services.sources.roljob import fetch_roljob
from app.services.sources.adecco import fetch_adecco

logger = logging.getLogger(__name__)


# ── Sync state ───────────────────────────────────────────────────────────

_last_sync_result: dict | None = None
_last_sync_time: datetime | None = None
_sync_in_progress: bool = False


def get_scraper_status() -> dict:
    """Return current scraper status."""
    settings = get_settings()
    return {
        "scraper_enabled": settings.SCRAPER_ENABLED,
        "last_sync_time": _last_sync_time.isoformat() if _last_sync_time else None,
        "last_sync_result": _last_sync_result,
        "sync_in_progress": _sync_in_progress,
        "scheduled_hour": settings.SCRAPER_JOBSPL_HOUR,
        "scheduled_minute": settings.SCRAPER_JOBSPL_MINUTE,
        "feed_url": settings.JOBSPL_FEED_URL,
    }


async def get_source_counts() -> dict:
    """Get counts of jobs per source_name for status reporting."""
    async with async_session() as db:
        result = await db.execute(
            select(JobOffer.source_name, sa_func.count())
            .where(JobOffer.source_name.isnot(None))
            .group_by(JobOffer.source_name)
        )
        counts = {row[0]: row[1] for row in result.all()}

        total_scraped = sum(counts.values())

        manual_count = await db.scalar(
            select(sa_func.count()).where(JobOffer.source_name.is_(None))
        )

        return {
            "by_source": counts,
            "total_scraped": total_scraped,
            "total_manual": manual_count or 0,
        }


# ── Generic sync helper ─────────────────────────────────────────────────


async def _sync_source(
    source_name: str,
    fetch_fn,
    limit: int | None = None,
) -> dict:
    """Generic sync function for any source.

    1. Fetch feed -> list of RawJobData
    2. Diff feed source_ids vs DB source_ids
    3. Remove stale jobs (in DB but not in feed)
    4. Process new jobs through generic pipeline (AI + save)
    """
    global _last_sync_result, _last_sync_time, _sync_in_progress

    if _sync_in_progress:
        return {"error": "Sync already in progress"}

    _sync_in_progress = True
    result = SyncResult()

    try:
        logger.info(f"{source_name} sync starting: fetching feed...")
        feed_jobs = await fetch_fn()

        if not feed_jobs:
            result.errors.append("Feed returned no jobs")
            result.finished_at = datetime.now(timezone.utc)
            _last_sync_result = result.to_dict()
            _last_sync_time = datetime.now(timezone.utc)
            return result.to_dict()

        feed_source_ids = {j.source_id for j in feed_jobs}
        feed_by_id = {j.source_id: j for j in feed_jobs}

        logger.info(f"Feed contains {len(feed_source_ids)} offer(s)")

        async with async_session() as db:
            db_result = await db.execute(
                select(JobOffer.source_id).where(
                    JobOffer.source_name == source_name
                )
            )
            db_source_ids = {row[0] for row in db_result.all() if row[0]}

            logger.info(f"DB contains {len(db_source_ids)} {source_name} job(s)")

            new_ids = feed_source_ids - db_source_ids
            stale_ids = db_source_ids - feed_source_ids
            existing_ids = feed_source_ids & db_source_ids

            result.skipped = len(existing_ids)
            logger.info(
                f"New: {len(new_ids)}, Stale: {len(stale_ids)}, "
                f"Existing: {len(existing_ids)}"
            )

            # Remove stale jobs
            if stale_ids:
                stale_result = await db.execute(
                    select(JobOffer).where(
                        JobOffer.source_name == source_name,
                        JobOffer.source_id.in_(stale_ids),
                    )
                )
                stale_jobs = stale_result.scalars().all()
                for stale_job in stale_jobs:
                    await db.delete(stale_job)
                    result.removed += 1
                await db.commit()
                logger.info(f"Removed {result.removed} stale job(s)")

            # Process new jobs
            new_raw_jobs = [feed_by_id[sid] for sid in new_ids]
            process_result = await process_jobs(new_raw_jobs, db, limit=limit)

            result.added = process_result.added
            result.errors.extend(process_result.errors)

    except Exception as e:
        result.errors.append(f"Sync failed: {str(e)}")
        logger.error(f"{source_name} sync failed: {e}", exc_info=True)
    finally:
        _sync_in_progress = False
        result.finished_at = datetime.now(timezone.utc)
        _last_sync_result = result.to_dict()
        _last_sync_time = datetime.now(timezone.utc)

    logger.info(
        f"{source_name} sync complete: "
        f"added={result.added}, removed={result.removed}, "
        f"skipped={result.skipped}, filtered={result.filtered}, "
        f"errors={len(result.errors)}"
    )

    return result.to_dict()


# ── Source-specific sync functions ───────────────────────────────────────


async def sync_jobspl(limit: int | None = None) -> dict:
    """Sync JOBSPL feed."""
    return await _sync_source("JOBSPL", fetch_jobspl, limit=limit)


async def sync_fachpraca(limit: int | None = None) -> dict:
    """Sync FACHPRACA feed."""
    return await _sync_source("FACHPRACA", fetch_fachpraca, limit=limit)


async def sync_roljob(limit: int | None = None) -> dict:
    """Sync ROLJOB feed."""
    return await _sync_source("ROLJOB", fetch_roljob, limit=limit)


async def sync_adecco(limit: int | None = None) -> dict:
    """Sync ADECCO feed."""
    return await _sync_source("ADECCO", fetch_adecco, limit=limit)
