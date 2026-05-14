"""Public (no-login) email alerts for new job offers matching a search query.

Flow:
  POST /api/v1/public-alerts/subscribe  { email, query }  → 201, alert created (active)
  GET  /api/v1/public-alerts/unsubscribe?token=...        → 200, alert deleted

Anti-abuse:
  - reCAPTCHA v3 (header X-Recaptcha-Token)
  - Rate limit 5 subscribe/h/IP
  - Per-email cap: max 10 active alerts on the same address
  - Same (email, query) → updates the existing row instead of creating a duplicate
"""
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.rate_limit import limiter
from app.core.recaptcha import verify_recaptcha
from app.database import get_db
from app.models.public_job_alert import PublicJobAlert
from app.models.unsubscribed_email import UnsubscribedEmail
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/public-alerts", tags=["public-alerts"])

MAX_ALERTS_PER_EMAIL = 10


MAX_KEYWORDS = 5


class SubscribeBody(BaseModel):
    email: EmailStr
    # One single keyword (legacy) or a list of keywords (new). At least one is required.
    query: str | None = Field(None, min_length=2, max_length=120)
    queries: list[str] | None = Field(None, max_length=MAX_KEYWORDS)


def _normalise_keywords(body: SubscribeBody) -> list[str]:
    """Collect & normalise keywords from body, return list of unique lowercase keywords."""
    raw: list[str] = []
    if body.queries:
        raw.extend(body.queries)
    if body.query:
        raw.append(body.query)
    seen: set[str] = set()
    out: list[str] = []
    for kw in raw:
        if not kw:
            continue
        norm = " ".join(kw.split()).strip()
        if len(norm) < 2 or len(norm) > 120:
            continue
        key = norm.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(norm)
        if len(out) >= MAX_KEYWORDS:
            break
    return out


@router.post("/subscribe", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("5/hour")
async def subscribe(
    request: Request,
    body: SubscribeBody,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_recaptcha),
):
    email = body.email.strip().lower()
    keywords = _normalise_keywords(body)
    if not keywords:
        raise HTTPException(
            status_code=422,
            detail="Wymagana jest przynajmniej jedna fraza (2–120 znaków).",
        )

    # display + dedup key — comma-joined, truncated to 255 chars
    display_query = ", ".join(keywords)[:255]
    query_key = ", ".join(k.lower() for k in keywords)[:255]
    queries_lower = [k.lower() for k in keywords]

    # Per-email cap (basic anti-abuse)
    count_res = await db.execute(
        select(func.count(PublicJobAlert.id)).where(PublicJobAlert.email == email)
    )
    if (count_res.scalar() or 0) >= MAX_ALERTS_PER_EMAIL:
        raise HTTPException(
            status_code=400,
            detail=f"Osiągnięto limit {MAX_ALERTS_PER_EMAIL} aktywnych powiadomień dla tego adresu email.",
        )

    # Dedup: same (email, query_key) → acknowledge silently
    existing_res = await db.execute(
        select(PublicJobAlert).where(
            PublicJobAlert.email == email,
            PublicJobAlert.query_key == query_key,
        )
    )
    if existing_res.scalar_one_or_none():
        return MessageResponse(message="Powiadomienia są już aktywne dla tych fraz.")

    alert = PublicJobAlert(
        email=email,
        query=display_query,
        query_key=query_key,
        queries=queries_lower,
    )
    db.add(alert)
    await db.flush()

    return MessageResponse(
        message="Zapisano. Co tydzień otrzymasz email z nowymi ofertami pasującymi do Twoich fraz.",
    )


@router.get("/unsubscribe", response_model=MessageResponse)
async def unsubscribe(
    token: str = Query(..., min_length=10, max_length=64),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(PublicJobAlert).where(PublicJobAlert.unsubscribe_token == token))
    alert = res.scalar_one_or_none()
    if not alert:
        # Idempotent — already unsubscribed or invalid token
        return MessageResponse(message="Powiadomienia są wyłączone.")

    # Merged-digest model: one email = one weekly digest with all keywords combined.
    # Unsubscribing therefore removes EVERY alert on this email (anti-orphan).
    email = alert.email
    all_for_email = (
        await db.execute(select(PublicJobAlert).where(PublicJobAlert.email == email))
    ).scalars().all()
    for a in all_for_email:
        db.add(
            UnsubscribedEmail(
                email=a.email,
                query=a.query,
                subscribed_at=a.created_at,
            )
        )
        await db.delete(a)
    return MessageResponse(message="Powiadomienia zostały wyłączone.")
