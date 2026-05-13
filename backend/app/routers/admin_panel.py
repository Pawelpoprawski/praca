"""Admin panel endpoints (separate from the JWT-based /admin/* role panel).

Auth: shared password sent via X-Admin-Password header, compared against
settings.ADMIN_PANEL_PASSWORD. Intended for the site owner only.
"""
from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone, date
from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select, distinct, case, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.page_visit import PageVisit
from app.models.company_override import CompanyOverride
from app.models.cv_review import CVReview
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.application_click import ApplicationClick
from app.models.employer_profile import EmployerProfile
from app.services.company_overrides import invalidate_cache

router = APIRouter(prefix="/admin-panel", tags=["admin-panel"])


def require_admin_password(
    x_admin_password: Annotated[str | None, Header(alias="X-Admin-Password")] = None,
):
    settings = get_settings()
    expected = settings.ADMIN_PANEL_PASSWORD
    if not x_admin_password or not secrets.compare_digest(x_admin_password, expected):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Niepoprawne hasło administratora",
        )
    return True


# ────────────────────────────────────────────────────────────────────────────
# Login (so the frontend can validate the password before storing it)
# ────────────────────────────────────────────────────────────────────────────


class LoginBody(BaseModel):
    password: str


@router.post("/login")
async def login(body: LoginBody):
    settings = get_settings()
    if not secrets.compare_digest(body.password, settings.ADMIN_PANEL_PASSWORD):
        raise HTTPException(status_code=401, detail="Niepoprawne hasło")
    return {"ok": True}


# ────────────────────────────────────────────────────────────────────────────
# Overview stats (last 7d / 30d / YTD + % vs previous period)
# ────────────────────────────────────────────────────────────────────────────


async def _count_between(db: AsyncSession, model, dt_col, start: datetime, end: datetime, extra_filters=None) -> int:
    q = select(func.count()).select_from(model).where(dt_col >= start, dt_col < end)
    if extra_filters is not None:
        q = q.where(*extra_filters)
    return (await db.execute(q)).scalar() or 0


async def _unique_ips_between(db: AsyncSession, start: datetime, end: datetime) -> int:
    q = select(func.count(distinct(PageVisit.ip))).where(
        PageVisit.created_at >= start, PageVisit.created_at < end
    )
    return (await db.execute(q)).scalar() or 0


def _pct_change(curr: int, prev: int) -> float | None:
    if prev <= 0:
        return None  # division by zero / no baseline → frontend renders as "—"
    return round(((curr - prev) / prev) * 100.0, 1)


@router.get("/overview", dependencies=[Depends(require_admin_password)])
async def overview(db: AsyncSession = Depends(get_db)):
    now = datetime.now(timezone.utc)
    today = now.date()
    ytd_start = datetime(today.year, 1, 1, tzinfo=timezone.utc)
    prev_ytd_start = datetime(today.year - 1, 1, 1, tzinfo=timezone.utc)
    prev_ytd_end = ytd_start  # same calendar window in previous year (truncated by now diff)

    # Windows
    windows = {
        "7d": (now - timedelta(days=7), now, now - timedelta(days=14), now - timedelta(days=7)),
        "30d": (now - timedelta(days=30), now, now - timedelta(days=60), now - timedelta(days=30)),
        "ytd": (ytd_start, now, prev_ytd_start, prev_ytd_end),
    }

    metrics = {
        "visits_unique_ips": ("page_visits_uniq", None),
        "cv_scans": (CVReview, CVReview.created_at),
        "jobs_published": (JobOffer, JobOffer.created_at),
        "applications_internal": (Application, Application.created_at),
        "apply_clicks_external": (ApplicationClick, ApplicationClick.created_at),
    }

    result: dict = {}
    for metric_key, (model, dt_col) in metrics.items():
        windows_out = {}
        for win_key, (cs, ce, ps, pe) in windows.items():
            if metric_key == "visits_unique_ips":
                curr = await _unique_ips_between(db, cs, ce)
                prev = await _unique_ips_between(db, ps, pe)
            else:
                curr = await _count_between(db, model, dt_col, cs, ce)
                prev = await _count_between(db, model, dt_col, ps, pe)
            windows_out[win_key] = {"current": curr, "previous": prev, "pct_change": _pct_change(curr, prev)}
        result[metric_key] = windows_out

    return result


# ────────────────────────────────────────────────────────────────────────────
# 30-day daily time series — unique IPs / CV scans / applications / jobs
# ────────────────────────────────────────────────────────────────────────────


@router.get("/timeseries", dependencies=[Depends(require_admin_password)])
async def timeseries(days: int = 30, db: AsyncSession = Depends(get_db)):
    days = max(1, min(180, days))
    now = datetime.now(timezone.utc)
    start = (now - timedelta(days=days)).replace(hour=0, minute=0, second=0, microsecond=0)

    def trunc_day(col):
        return func.date_trunc("day", col)

    async def daily_count(model, dt_col, *, distinct_col=None):
        if distinct_col is not None:
            q = (
                select(trunc_day(dt_col).label("d"), func.count(distinct(distinct_col)))
                .where(dt_col >= start)
                .group_by("d")
                .order_by("d")
            )
        else:
            q = (
                select(trunc_day(dt_col).label("d"), func.count())
                .where(dt_col >= start)
                .group_by("d")
                .order_by("d")
            )
        rows = (await db.execute(q)).all()
        return {row[0].date().isoformat(): int(row[1]) for row in rows}

    visits = await daily_count(PageVisit, PageVisit.created_at, distinct_col=PageVisit.ip)
    visits_total = await daily_count(PageVisit, PageVisit.created_at)
    cv_scans = await daily_count(CVReview, CVReview.created_at)
    jobs_added = await daily_count(JobOffer, JobOffer.created_at)
    apps_internal = await daily_count(Application, Application.created_at)
    apps_external = await daily_count(ApplicationClick, ApplicationClick.created_at)

    # Fill all days, even those with 0
    series = []
    for i in range(days + 1):
        day = (start + timedelta(days=i)).date()
        key = day.isoformat()
        series.append({
            "date": key,
            "visits_unique_ips": visits.get(key, 0),
            "visits_total": visits_total.get(key, 0),
            "cv_scans": cv_scans.get(key, 0),
            "jobs_added": jobs_added.get(key, 0),
            "applications_internal": apps_internal.get(key, 0),
            "apply_clicks_external": apps_external.get(key, 0),
        })
    return {"days": days, "series": series}


# ────────────────────────────────────────────────────────────────────────────
# Per-company stats — jobs / views / internal apps / external clicks
# ────────────────────────────────────────────────────────────────────────────


@router.get("/companies", dependencies=[Depends(require_admin_password)])
async def companies(db: AsyncSession = Depends(get_db)):
    # Aggregate by employer.company_name across all active jobs (lifetime).
    job_agg = (
        select(
            EmployerProfile.id.label("employer_id"),
            EmployerProfile.company_name.label("company_name"),
            func.count(JobOffer.id).label("job_count"),
            func.coalesce(func.sum(JobOffer.views_count), 0).label("views_total"),
        )
        .join(JobOffer, JobOffer.employer_id == EmployerProfile.id, isouter=True)
        .group_by(EmployerProfile.id, EmployerProfile.company_name)
    ).subquery()

    internal_apps = (
        select(
            EmployerProfile.id.label("employer_id"),
            func.count(Application.id).label("apps_internal"),
        )
        .join(JobOffer, JobOffer.employer_id == EmployerProfile.id)
        .join(Application, Application.job_offer_id == JobOffer.id)
        .group_by(EmployerProfile.id)
    ).subquery()

    external_clicks = (
        select(
            EmployerProfile.id.label("employer_id"),
            func.count(ApplicationClick.id).label("clicks_external"),
        )
        .join(JobOffer, JobOffer.employer_id == EmployerProfile.id)
        .join(ApplicationClick, ApplicationClick.job_offer_id == JobOffer.id)
        .group_by(EmployerProfile.id)
    ).subquery()

    overrides_q = await db.execute(select(CompanyOverride))
    overrides = {o.company_key: o for o in overrides_q.scalars().all()}

    q = (
        select(
            job_agg.c.employer_id,
            job_agg.c.company_name,
            job_agg.c.job_count,
            job_agg.c.views_total,
            func.coalesce(internal_apps.c.apps_internal, 0).label("apps_internal"),
            func.coalesce(external_clicks.c.clicks_external, 0).label("clicks_external"),
        )
        .select_from(job_agg)
        .outerjoin(internal_apps, internal_apps.c.employer_id == job_agg.c.employer_id)
        .outerjoin(external_clicks, external_clicks.c.employer_id == job_agg.c.employer_id)
        .order_by(job_agg.c.views_total.desc().nulls_last(), job_agg.c.company_name)
    )
    rows = (await db.execute(q)).all()

    out = []
    for row in rows:
        key = (row.company_name or "").strip().lower()
        ovr = overrides.get(key)
        out.append({
            "employer_id": row.employer_id,
            "company_name": row.company_name,
            "company_key": key,
            "job_count": int(row.job_count or 0),
            "views_total": int(row.views_total or 0),
            "applications_internal": int(row.apps_internal or 0),
            "apply_clicks_external": int(row.clicks_external or 0),
            "override_email": ovr.apply_email if ovr else None,
            "override_id": ovr.id if ovr else None,
            "override_note": ovr.note if ovr else None,
        })
    return {"companies": out}


# ────────────────────────────────────────────────────────────────────────────
# Company overrides CRUD
# ────────────────────────────────────────────────────────────────────────────


class OverrideCreate(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    apply_email: EmailStr
    note: str | None = Field(None, max_length=500)


class OverrideUpdate(BaseModel):
    apply_email: EmailStr | None = None
    note: str | None = Field(None, max_length=500)


@router.get("/overrides", dependencies=[Depends(require_admin_password)])
async def list_overrides(db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CompanyOverride).order_by(CompanyOverride.company_name))
    rows = res.scalars().all()
    return {
        "overrides": [
            {
                "id": r.id,
                "company_name": r.company_name,
                "company_key": r.company_key,
                "apply_email": r.apply_email,
                "note": r.note,
                "created_at": r.created_at.isoformat() if r.created_at else None,
                "updated_at": r.updated_at.isoformat() if r.updated_at else None,
            }
            for r in rows
        ]
    }


@router.post("/overrides", dependencies=[Depends(require_admin_password)])
async def create_override(body: OverrideCreate, db: AsyncSession = Depends(get_db)):
    key = body.company_name.strip().lower()
    existing = await db.execute(select(CompanyOverride).where(CompanyOverride.company_key == key))
    if existing.scalar_one_or_none():
        raise HTTPException(409, "Override dla tej firmy już istnieje — edytuj zamiast tworzyć")
    o = CompanyOverride(
        company_key=key,
        company_name=body.company_name.strip(),
        apply_email=body.apply_email,
        note=body.note,
    )
    db.add(o)
    await db.flush()
    invalidate_cache()
    return {"id": o.id, "company_key": o.company_key}


@router.patch("/overrides/{override_id}", dependencies=[Depends(require_admin_password)])
async def update_override(override_id: str, body: OverrideUpdate, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CompanyOverride).where(CompanyOverride.id == override_id))
    o = res.scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Override nie znaleziony")
    if body.apply_email is not None:
        o.apply_email = body.apply_email
    if body.note is not None:
        o.note = body.note
    await db.flush()
    invalidate_cache()
    return {"ok": True}


@router.delete("/overrides/{override_id}", dependencies=[Depends(require_admin_password)])
async def delete_override(override_id: str, db: AsyncSession = Depends(get_db)):
    res = await db.execute(select(CompanyOverride).where(CompanyOverride.id == override_id))
    o = res.scalar_one_or_none()
    if not o:
        raise HTTPException(404, "Override nie znaleziony")
    await db.delete(o)
    invalidate_cache()
    return {"ok": True}
