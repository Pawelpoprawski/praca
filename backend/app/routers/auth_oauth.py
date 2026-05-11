"""OAuth login flow (Google + Facebook).

Endpointy redirectuja uzytkownika na ekran logowania providera.
Callback odbiera `code`, probuje wymienic na token. Aktualnie credentials sa
dummy — flow konczy sie redirektem na frontend z `?error=oauth_unavailable`.
Po uzupelnieniu prawdziwych CLIENT_ID/SECRET callback zaczyna dzialac.
"""
import secrets
import urllib.parse
from typing import Literal

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from app.config import get_settings

router = APIRouter(prefix="/auth", tags=["oauth"])


# ── Provider config ──────────────────────────────────────────────────────


def _provider_config(provider: str):
    s = get_settings()
    if provider == "google":
        return {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth",
            "token_url": "https://oauth2.googleapis.com/token",
            "userinfo_url": "https://openidconnect.googleapis.com/v1/userinfo",
            "client_id": s.GOOGLE_CLIENT_ID,
            "client_secret": s.GOOGLE_CLIENT_SECRET,
            "scope": "openid email profile",
        }
    if provider == "facebook":
        return {
            "auth_url": "https://www.facebook.com/v18.0/dialog/oauth",
            "token_url": "https://graph.facebook.com/v18.0/oauth/access_token",
            "userinfo_url": "https://graph.facebook.com/me?fields=id,name,email,first_name,last_name",
            "client_id": s.FACEBOOK_CLIENT_ID,
            "client_secret": s.FACEBOOK_CLIENT_SECRET,
            "scope": "email public_profile",
        }
    return None


def _redirect_uri(provider: str) -> str:
    s = get_settings()
    return f"{s.OAUTH_REDIRECT_BASE_URL}/api/v1/auth/{provider}/callback"


# ── Login: redirect na ekran providera ───────────────────────────────────


@router.get("/{provider}/login")
async def oauth_login(provider: Literal["google", "facebook"]):
    cfg = _provider_config(provider)
    if not cfg:
        return RedirectResponse(
            f"{get_settings().FRONTEND_URL}/login?error=unknown_provider"
        )

    state = secrets.token_urlsafe(32)
    params = {
        "client_id": cfg["client_id"],
        "redirect_uri": _redirect_uri(provider),
        "response_type": "code",
        "scope": cfg["scope"],
        "state": state,
    }
    if provider == "google":
        params["access_type"] = "offline"
        params["prompt"] = "consent"

    url = f"{cfg['auth_url']}?{urllib.parse.urlencode(params)}"

    response = RedirectResponse(url, status_code=302)
    # Zachowaj state w cookie do walidacji w callbacku
    response.set_cookie(
        key=f"oauth_state_{provider}",
        value=state,
        httponly=True,
        max_age=600,
        samesite="lax",
    )
    return response


# ── Callback: odbior code i wymiana na token ─────────────────────────────


@router.get("/{provider}/callback")
async def oauth_callback(
    request: Request,
    provider: Literal["google", "facebook"],
    code: str | None = None,
    state: str | None = None,
    error: str | None = None,
):
    settings = get_settings()
    frontend = settings.FRONTEND_URL

    if error:
        return RedirectResponse(f"{frontend}/login?error={urllib.parse.quote(error)}")

    if not code:
        return RedirectResponse(f"{frontend}/login?error=oauth_missing_code")

    # Walidacja state z cookie
    expected_state = request.cookies.get(f"oauth_state_{provider}")
    if not expected_state or expected_state != state:
        return RedirectResponse(f"{frontend}/login?error=oauth_state_mismatch")

    cfg = _provider_config(provider)
    if not cfg:
        return RedirectResponse(f"{frontend}/login?error=unknown_provider")

    # Wymiana code -> token
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            token_resp = await client.post(
                cfg["token_url"],
                data={
                    "code": code,
                    "client_id": cfg["client_id"],
                    "client_secret": cfg["client_secret"],
                    "redirect_uri": _redirect_uri(provider),
                    "grant_type": "authorization_code",
                },
            )
            if token_resp.status_code != 200:
                return RedirectResponse(
                    f"{frontend}/login?error=oauth_token_exchange_failed"
                )

            tok = token_resp.json()
            access_token = tok.get("access_token")
            if not access_token:
                return RedirectResponse(
                    f"{frontend}/login?error=oauth_no_access_token"
                )

            # Pobierz dane uzytkownika
            user_resp = await client.get(
                cfg["userinfo_url"],
                headers={"Authorization": f"Bearer {access_token}"},
            )
            if user_resp.status_code != 200:
                return RedirectResponse(
                    f"{frontend}/login?error=oauth_userinfo_failed"
                )

            user_info = user_resp.json()

    except httpx.HTTPError:
        return RedirectResponse(f"{frontend}/login?error=oauth_network_error")

    # TODO: znajdz/utworz uzytkownika po email, wystaw JWT, redirect do panelu
    # Na razie - placeholder: redirect z info ze flow zadzialal (gdy realne credentials)
    email = user_info.get("email", "unknown")
    return RedirectResponse(
        f"{frontend}/login?info=oauth_not_implemented&email={urllib.parse.quote(email)}"
    )
