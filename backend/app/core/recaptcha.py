import httpx
from fastapi import Depends, HTTPException, Request, status
from app.config import get_settings


async def verify_recaptcha(request: Request):
    """Dependency that verifies reCAPTCHA v3 token from X-Recaptcha-Token header."""
    settings = get_settings()

    if not settings.RECAPTCHA_ENABLED:
        return

    token = request.headers.get("X-Recaptcha-Token")
    if not token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Brak tokena reCAPTCHA",
        )

    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://www.google.com/recaptcha/api/siteverify",
            data={
                "secret": settings.RECAPTCHA_SECRET_KEY,
                "response": token,
            },
        )

    result = resp.json()

    if not result.get("success") or result.get("score", 0) < settings.RECAPTCHA_SCORE_THRESHOLD:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Weryfikacja reCAPTCHA nie powiodła się",
        )
