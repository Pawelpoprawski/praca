"""Public no-auth tracking endpoint for page visits (called from Next.js client)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.page_visit import PageVisit

router = APIRouter(prefix="/track", tags=["tracking"])


class VisitPayload(BaseModel):
    path: str = Field("/", max_length=500)
    referrer: str | None = Field(None, max_length=500)


def _client_ip(request: Request) -> str:
    # Honour the typical reverse-proxy chain (Nginx adds X-Forwarded-For).
    xff = request.headers.get("x-forwarded-for")
    if xff:
        return xff.split(",")[0].strip()
    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        return real_ip.strip()
    return request.client.host if request.client else "unknown"


@router.post("/visit", status_code=204)
async def track_visit(
    payload: VisitPayload,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Record one page visit. Best-effort: never fails the caller."""
    try:
        ua = request.headers.get("user-agent", "")[:1000]
        visit = PageVisit(
            ip=_client_ip(request)[:64],
            path=payload.path[:500] or "/",
            user_agent=ua or None,
            referrer=(payload.referrer or None),
        )
        db.add(visit)
        await db.flush()
    except Exception:
        # Tracking must never break the user-facing flow
        pass
    return None
