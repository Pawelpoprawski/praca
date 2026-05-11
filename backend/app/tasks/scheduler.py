import logging
from datetime import date, datetime, timedelta, timezone
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sqlalchemy import update, select
from sqlalchemy.orm import selectinload
from app.database import async_session
from app.models.posting_quota import PostingQuota
from app.models.job_offer import JobOffer
from app.models.job_alert import JobAlert
from app.config import get_settings

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


async def sync_jobspl_scheduled():
    """Scheduled daily JOBSPL feed sync."""
    settings = get_settings()
    if not settings.SCRAPER_ENABLED:
        logger.info("JOBSPL scraper disabled, skipping scheduled sync")
        return

    logger.info("Starting scheduled JOBSPL sync...")
    try:
        from app.services.job_scraper import sync_jobspl
        result = await sync_jobspl()
        logger.info(
            f"Scheduled JOBSPL sync complete: "
            f"added={result.get('added', 0)}, "
            f"removed={result.get('removed', 0)}, "
            f"errors={len(result.get('errors', []))}"
        )
    except Exception as e:
        logger.error(f"Scheduled JOBSPL sync failed: {e}", exc_info=True)


async def check_job_alerts():
    """Sprawdzanie alertów o pracy i wysyłanie emaili (co godzinę)."""
    now = datetime.now(timezone.utc)
    settings = get_settings()
    sent_count = 0

    async with async_session() as db:
        # Fetch all active alerts with user data
        result = await db.execute(
            select(JobAlert)
            .options(selectinload(JobAlert.user))
            .where(JobAlert.is_active.is_(True))
        )
        alerts = result.scalars().all()

        for alert in alerts:
            # Determine if this alert should be checked based on frequency
            if alert.last_sent_at:
                if alert.frequency == "daily":
                    if (now - alert.last_sent_at) < timedelta(hours=23):
                        continue
                elif alert.frequency == "weekly":
                    if (now - alert.last_sent_at) < timedelta(days=6, hours=23):
                        continue
                # "instant" - always check

            # Build query for matching active job offers
            # Only look at jobs created after last_sent_at (or last 24h for new alerts)
            since = alert.last_sent_at or (now - timedelta(hours=24))

            query = select(JobOffer).where(
                JobOffer.status == "active",
                JobOffer.created_at > since,
            )

            filters = alert.filters or {}

            if filters.get("category_id"):
                query = query.where(JobOffer.category_id == filters["category_id"])

            if filters.get("canton"):
                query = query.where(JobOffer.canton == filters["canton"])

            if filters.get("min_salary"):
                query = query.where(
                    (JobOffer.salary_max >= filters["min_salary"])
                    | (JobOffer.salary_max.is_(None))
                )

            if filters.get("max_salary"):
                query = query.where(
                    (JobOffer.salary_min <= filters["max_salary"])
                    | (JobOffer.salary_min.is_(None))
                )

            if filters.get("work_mode"):
                query = query.where(JobOffer.is_remote == filters["work_mode"])

            if filters.get("keywords"):
                kw = f"%{filters['keywords']}%"
                query = query.where(
                    JobOffer.title.ilike(kw) | JobOffer.description.ilike(kw)
                )

            query = query.order_by(JobOffer.created_at.desc()).limit(20)

            job_result = await db.execute(query)
            matching_jobs = job_result.scalars().all()

            if not matching_jobs:
                continue

            # Send email notification
            user = alert.user
            if not user or not user.email:
                continue

            job_list_html = "".join(
                f'<li style="margin-bottom:8px;">'
                f'<a href="{settings.FRONTEND_URL}/oferty/{j.id}" '
                f'style="color:#dc2626;text-decoration:none;font-weight:600;">'
                f'{j.title}</a>'
                f' &mdash; {j.canton}'
                f'{"  (" + str(j.salary_min) + "-" + str(j.salary_max) + " CHF)" if j.salary_min and j.salary_max else ""}'
                f'</li>'
                for j in matching_jobs
            )

            frequency_label = {
                "instant": "natychmiastowy",
                "daily": "dzienny",
                "weekly": "tygodniowy",
            }.get(alert.frequency, alert.frequency)

            html = f"""
            <h2>Nowe oferty pracy pasujące do alertu: {alert.name}</h2>
            <p>Cześć {user.first_name or ""},</p>
            <p>Znaleźliśmy <strong>{len(matching_jobs)}</strong> nowe oferty pasujące
            do Twojego alertu <strong>"{alert.name}"</strong> ({frequency_label}):</p>
            <ul style="padding-left:20px;">{job_list_html}</ul>
            <p style="margin-top:16px;">
                <a href="{settings.FRONTEND_URL}/panel/pracownik/alerty"
                   style="display:inline-block;padding:10px 20px;background:#dc2626;color:white;
                          text-decoration:none;border-radius:6px;">
                    Zarządzaj alertami
                </a>
            </p>
            <p style="color:#666;font-size:12px;margin-top:16px;">
                Aby wyłączyć ten alert, przejdź do ustawień alertów w panelu pracownika.
            </p>
            """

            from app.services.email import _send_email
            success = _send_email(
                user.email,
                f"Nowe oferty pracy: {alert.name} ({len(matching_jobs)}) - Praca w Szwajcarii",
                html,
            )

            if success:
                alert.last_sent_at = now
                sent_count += 1

        await db.commit()

    if sent_count:
        logger.info(f"Sent {sent_count} job alert email(s)")


async def process_cv_extractions_scheduled():
    """Background CV data extraction (every 2 minutes)."""
    try:
        from app.services.cv_extraction_service import process_pending_cv_extractions
        count = await process_pending_cv_extractions()
        if count:
            logger.info(f"CV extraction: processed {count} record(s)")
    except Exception as e:
        logger.error(f"CV extraction job failed: {e}", exc_info=True)


async def process_job_translations_scheduled():
    """Background job translation DE/FR/IT -> PL (every 2 minutes)."""
    try:
        from app.services.job_translation_service import process_pending_job_translations
        count = await process_pending_job_translations()
        if count:
            logger.info(f"Job translation: processed {count} record(s)")
    except Exception as e:
        logger.error(f"Job translation job failed: {e}", exc_info=True)


async def process_job_extractions_scheduled():
    """Background job metadata extraction (every 3 minutes)."""
    try:
        from app.services.job_extraction_service import process_pending_job_extractions
        count = await process_pending_job_extractions()
        if count:
            logger.info(f"Job extraction: processed {count} record(s)")
    except Exception as e:
        logger.error(f"Job extraction job failed: {e}", exc_info=True)


def start_scheduler():
    settings = get_settings()
    scheduler.add_job(reset_expired_quotas, "cron", hour=0, minute=5, id="reset_quotas")
    scheduler.add_job(expire_old_jobs, "cron", hour=1, minute=0, id="expire_jobs")
    scheduler.add_job(check_job_alerts, "interval", hours=1, id="check_job_alerts")
    scheduler.add_job(
        sync_jobspl_scheduled,
        "cron",
        hour=settings.SCRAPER_JOBSPL_HOUR,
        minute=settings.SCRAPER_JOBSPL_MINUTE,
        id="sync_jobspl",
    )
    scheduler.add_job(
        process_cv_extractions_scheduled,
        "interval",
        minutes=2,
        id="cv_extraction",
    )
    scheduler.add_job(
        process_job_translations_scheduled,
        "interval",
        minutes=2,
        id="job_translation",
    )
    scheduler.add_job(
        process_job_extractions_scheduled,
        "interval",
        minutes=3,
        id="job_extraction",
    )
    scheduler.start()
    logger.info("Scheduler started (JOBSPL sync at %02d:%02d, CV extraction/2min, Job translation/2min, Job extraction/3min)",
                settings.SCRAPER_JOBSPL_HOUR, settings.SCRAPER_JOBSPL_MINUTE)


def stop_scheduler():
    scheduler.shutdown()
    logger.info("Scheduler stopped")
