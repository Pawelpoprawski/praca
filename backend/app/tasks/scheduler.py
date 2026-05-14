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


def _pl_jobs_count(n: int) -> str:
    """Polish plural for offers: '1 nowa oferta' / '2 nowe oferty' / '5 nowych ofert'."""
    if n == 1:
        return "1 nowa oferta"
    last_two = n % 100
    last = n % 10
    if 2 <= last <= 4 and not (12 <= last_two <= 14):
        return f"{n} nowe oferty"
    return f"{n} nowych ofert"


async def check_public_alerts():
    """Send weekly digest to no-login subscribers — one email per address (merged).

    Multiple alerts on the same email are coalesced into a single digest covering
    all their keywords. Cooldown is computed per address (most recent send).
    """
    import re
    import random
    from urllib.parse import quote_plus
    from sqlalchemy import or_ as sa_or
    from app.models.public_job_alert import PublicJobAlert
    from app.services.email import _send_email

    settings = get_settings()
    now = datetime.now(timezone.utc)
    sent_count = 0

    async with async_session() as db:
        result = await db.execute(select(PublicJobAlert))
        alerts = result.scalars().all()

        # Group alerts by email (lowercased) so each address receives a single digest
        alerts_by_email: dict[str, list[PublicJobAlert]] = {}
        for a in alerts:
            alerts_by_email.setdefault((a.email or "").lower(), []).append(a)

        for email, group in alerts_by_email.items():
            if not email or not group:
                continue

            # Most recent send across this address's alerts → weekly cooldown
            last_sents: list[datetime] = []
            for a in group:
                if a.last_sent_at:
                    ls = a.last_sent_at
                    if ls.tzinfo is None:
                        ls = ls.replace(tzinfo=timezone.utc)
                    last_sents.append(ls)
            most_recent = max(last_sents) if last_sents else None
            if most_recent and (now - most_recent) < timedelta(days=6, hours=23):
                continue
            since = most_recent or (now - timedelta(days=7))

            # Aggregate keywords across all alerts on this email (dedup, case-insensitive)
            seen: set[str] = set()
            merged_keywords: list[str] = []
            for a in group:
                raw = list(a.queries) if a.queries else ([a.query] if a.query else [])
                for kw_raw in raw:
                    if not kw_raw:
                        continue
                    kw_clean = re.sub(r"[%_\\]", "", kw_raw).strip()
                    if len(kw_clean) < 2:
                        continue
                    key = kw_clean.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    merged_keywords.append(kw_clean)
            if not merged_keywords:
                continue

            keyword_clauses = []
            for kw in merged_keywords:
                like = f"%{kw}%"
                keyword_clauses.append(JobOffer.title.ilike(like))
                keyword_clauses.append(JobOffer.description.ilike(like))

            jobs_q = (
                select(JobOffer)
                .options(selectinload(JobOffer.employer))
                .where(
                    JobOffer.status == "active",
                    JobOffer.created_at > since,
                    sa_or(*keyword_clauses),
                )
                .limit(30)
            )
            matching_jobs = list((await db.execute(jobs_q)).scalars().all())

            if not matching_jobs:
                continue

            polish_jobs = [j for j in matching_jobs if j.recruiter_type == "polish"]
            swiss_jobs = [j for j in matching_jobs if j.recruiter_type == "swiss"]
            other_jobs = [j for j in matching_jobs if j.recruiter_type not in ("polish", "swiss")]
            random.shuffle(polish_jobs)
            random.shuffle(swiss_jobs)
            random.shuffle(other_jobs)
            polish_jobs = polish_jobs + other_jobs

            site_url = settings.FRONTEND_URL.rstrip("/")
            primary = group[0]
            unsub_url = f"{site_url}/alerty/wypisz?token={primary.unsubscribe_token}"
            query_display = ", ".join(merged_keywords)
            # ; is a separator on the search page → links back to a multi-keyword OR view
            search_url = f"{site_url}/oferty?q={quote_plus('; '.join(merged_keywords))}"

            html = _render_alert_email(
                query=query_display,
                jobs_count=len(matching_jobs),
                polish_jobs=polish_jobs,
                swiss_jobs=swiss_jobs,
                site_url=site_url,
                search_url=search_url,
                unsub_url=unsub_url,
            )

            subject = f"{_pl_jobs_count(len(matching_jobs))}: {query_display} - Praca w Szwajcarii"
            success = _send_email(email, subject, html)
            if success:
                for a in group:
                    a.last_sent_at = now
                sent_count += 1

        await db.commit()

    if sent_count:
        logger.info(f"Public alerts: sent {sent_count} digest email(s)")


def _render_alert_email(
    *,
    query: str,
    jobs_count: int,
    polish_jobs: list,
    swiss_jobs: list,
    site_url: str,
    search_url: str,
    unsub_url: str,
) -> str:
    """Render the weekly digest email with separate Polish/Swiss recruiter sections."""
    from html import escape

    canton_names = {
        "zurich": "Zurych", "bern": "Berno", "luzern": "Lucerna",
        "uri": "Uri", "schwyz": "Schwyz", "obwalden": "Obwalden",
        "nidwalden": "Nidwalden", "glarus": "Glarus", "zug": "Zug",
        "fribourg": "Fryburg", "solothurn": "Solura",
        "basel-stadt": "Bazylea-Miasto", "basel-landschaft": "Bazylea-Okręg",
        "schaffhausen": "Szafuza",
        "appenzell-ausserrhoden": "Appenzell Ausserrhoden",
        "appenzell-innerrhoden": "Appenzell Innerrhoden",
        "st-gallen": "St. Gallen", "graubunden": "Gryzonia",
        "aargau": "Argowia", "thurgau": "Turgowia", "ticino": "Ticino",
        "vaud": "Vaud", "valais": "Valais", "neuchatel": "Neuchâtel",
        "geneve": "Genewa", "jura": "Jura",
    }

    def _row(job) -> str:
        title = escape(job.title or "")
        company = ""
        if getattr(job, "employer", None) and getattr(job.employer, "company_name", None):
            company = escape(job.employer.company_name)
        location_parts = []
        if job.city:
            location_parts.append(escape(job.city))
        if job.canton:
            location_parts.append(canton_names.get(job.canton, escape(job.canton)))
        location = " · ".join(location_parts) or "Cała Szwajcaria"

        salary = ""
        if job.salary_min and job.salary_max:
            salary = f'{int(job.salary_min):,}–{int(job.salary_max):,} CHF'.replace(",", " ")
        elif job.salary_min:
            salary = f'od {int(job.salary_min):,} CHF'.replace(",", " ")

        url = f"{site_url}/oferty/{job.id}"
        return f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #EEF1F5;">
            <a href="{url}" style="display:inline-block;color:#0D2240;text-decoration:none;font-weight:700;font-size:15px;line-height:1.3;">
              {title}
            </a>
            <div style="margin-top:4px;color:#5B6478;font-size:13px;line-height:1.4;">
              {('<span style=\"font-weight:600;color:#0D2240;\">' + company + '</span> · ') if company else ''}{location}
            </div>
            {('<div style=\"margin-top:6px;color:#0D2240;font-size:13px;font-weight:600;\">' + salary + '</div>') if salary else ''}
            <div style="margin-top:12px;">
              <a href="{url}" style="display:inline-block;padding:9px 18px;background:#E1002A;color:white;text-decoration:none;border-radius:999px;font-weight:600;font-size:13px;">
                Zobacz ofertę →
              </a>
            </div>
          </td>
        </tr>
        """

    def _section(title_text: str, subtitle: str, jobs: list, flag_emoji: str, accent: str) -> str:
        if not jobs:
            return ""
        rows = "".join(_row(j) for j in jobs)
        return f"""
        <div style="margin-top:28px;">
          <div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">
            <span style="display:inline-block;width:4px;height:22px;background:{accent};border-radius:2px;"></span>
            <h3 style="margin:0;font-size:17px;font-weight:800;color:#0D2240;letter-spacing:-0.01em;">
              {flag_emoji} {title_text} <span style="color:#8693A6;font-weight:600;">({len(jobs)})</span>
            </h3>
          </div>
          <p style="margin:0 0 12px;color:#6B7484;font-size:12px;">{subtitle}</p>
          <table cellspacing="0" cellpadding="0" border="0" width="100%" style="border-collapse:collapse;border:1px solid #E0E3E8;border-radius:10px;overflow:hidden;">
            {rows}
          </table>
        </div>
        """

    polish_section = _section(
        "Polscy rekruterzy",
        "Mówimy po polsku, znamy specyfikę pracy w Szwajcarii.",
        polish_jobs,
        "🇵🇱",
        "#E1002A",
    )
    swiss_section = _section(
        "Szwajcarscy pracodawcy",
        "Bezpośrednio od pracodawców w Szwajcarii.",
        swiss_jobs,
        "🇨🇭",
        "#0D2240",
    )

    query_safe = escape(query)
    headline = _pl_jobs_count(jobs_count)

    return f"""<!DOCTYPE html>
<html lang="pl">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Liczba nowych ofert: {jobs_count}</title>
</head>
<body style="margin:0;padding:0;background:#F4F6FA;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif;color:#0D2240;">
  <table cellspacing="0" cellpadding="0" border="0" width="100%" style="background:#F4F6FA;padding:24px 12px;">
    <tr>
      <td align="center">
        <table cellspacing="0" cellpadding="0" border="0" width="640" style="max-width:640px;width:100%;background:white;border-radius:12px;overflow:hidden;box-shadow:0 2px 12px rgba(13,34,64,0.06);">
          <tr>
            <td style="background:linear-gradient(135deg,#0D2240 0%,#1B3157 100%);padding:32px 28px;color:white;">
              <div style="height:3px;width:44px;background:#E1002A;border-radius:2px;margin-bottom:18px;"></div>
              <div style="font-size:12px;font-weight:700;letter-spacing:0.12em;text-transform:uppercase;color:rgba(255,255,255,0.65);margin-bottom:6px;">
                Cotygodniowy alert
              </div>
              <h1 style="margin:0;font-size:26px;font-weight:800;line-height:1.2;letter-spacing:-0.02em;">
                {headline} dla &quot;{query_safe}&quot;
              </h1>
              <p style="margin:8px 0 0;color:rgba(255,255,255,0.75);font-size:14px;">
                Oferty pojawiły się w ciągu ostatniego tygodnia. Najlepsze przeglądasz pierwszy.
              </p>
            </td>
          </tr>
          <tr>
            <td style="padding:8px 28px 28px;background:white;">
              {polish_section}
              {swiss_section}

              <div style="margin-top:32px;padding-top:24px;border-top:1px solid #E0E3E8;text-align:center;">
                <a href="{search_url}" style="display:inline-block;padding:13px 24px;background:#0D2240;color:white;text-decoration:none;border-radius:999px;font-weight:700;font-size:14px;letter-spacing:0.01em;line-height:1.3;">
                  Zobacz wszystkie oferty →
                </a>
                <p style="margin:10px 0 0;color:#6B7484;font-size:12px;">
                  dla fraz: &quot;{query_safe}&quot;
                </p>
              </div>
            </td>
          </tr>
          <tr>
            <td style="padding:20px 28px;background:#F8F9FC;border-top:1px solid #E0E3E8;text-align:center;">
              <p style="margin:0 0 6px;color:#0D2240;font-size:13px;font-weight:700;">
                Praca w Szwajcarii
              </p>
              <p style="margin:0;color:#8693A6;font-size:11px;line-height:1.5;">
                Otrzymujesz ten email, bo zapisałeś się na powiadomienia o nowych ofertach.<br>
                <a href="{unsub_url}" style="color:#8693A6;text-decoration:underline;">Wypisz się z powiadomień</a>
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


async def purge_unconsented_cv_reviews():
    """Delete CV file + clear cv_text for reviews older than 24h without user consent (hourly)."""
    import os
    from app.models.cv_review import CVReview

    cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    upload_dir = os.path.join("uploads", "cv-review")
    deleted = 0

    async with async_session() as db:
        result = await db.execute(
            select(CVReview).where(
                CVReview.retention_status == "temporary",
                CVReview.created_at < cutoff,
            )
        )
        reviews = result.scalars().all()

        for review in reviews:
            if review.cv_filename:
                file_path = os.path.join(upload_dir, review.cv_filename)
                try:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                except OSError as e:
                    logger.warning(f"Failed to delete CV file {file_path}: {e}")
            review.cv_text = None
            review.cv_filename = ""
            review.retention_status = "purged"
            deleted += 1

        await db.commit()

    if deleted:
        logger.info(f"CV retention: purged {deleted} unconsented CV review(s)")


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
        purge_unconsented_cv_reviews,
        "interval",
        hours=1,
        id="purge_cv_reviews",
    )
    scheduler.add_job(
        check_public_alerts,
        "interval",
        hours=1,
        id="check_public_alerts",
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
