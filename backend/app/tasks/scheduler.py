import logging
from datetime import date, datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import update, select
from app.database import async_session
from app.models.posting_quota import PostingQuota
from app.models.job_offer import JobOffer

logger = logging.getLogger(__name__)
scheduler = AsyncIOScheduler()


async def reset_expired_quotas():
    """Reset limitów ogłoszeń po zakończeniu okresu (codziennie o 00:05)."""
    today = date.today()
    async with async_session() as db:
        result = await db.execute(
            update(PostingQuota)
            .where(PostingQuota.period_end <= today)
            .values(
                used_count=0,
                period_start=today,
                period_end=today + timedelta(days=30),
            )
            .returning(PostingQuota.id)
        )
        reset_count = len(result.all())
        await db.commit()

    if reset_count:
        logger.info(f"Reset {reset_count} quota(s)")


async def expire_old_jobs():
    """Wygaszanie ofert po upłynięciu expires_at (codziennie o 01:00)."""
    now = datetime.now(timezone.utc)
    async with async_session() as db:
        result = await db.execute(
            update(JobOffer)
            .where(
                JobOffer.status == "active",
                JobOffer.expires_at.isnot(None),
                JobOffer.expires_at <= now,
            )
            .values(status="expired")
            .returning(JobOffer.id)
        )
        expired_count = len(result.all())
        await db.commit()

    if expired_count:
        logger.info(f"Expired {expired_count} job(s)")


def start_scheduler():
    scheduler.add_job(reset_expired_quotas, "cron", hour=0, minute=5, id="reset_quotas")
    scheduler.add_job(expire_old_jobs, "cron", hour=1, minute=0, id="expire_jobs")
    scheduler.start()
    logger.info("Scheduler started")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped")
