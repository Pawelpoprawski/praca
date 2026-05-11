"""Signed URLs dla prywatnych plikow (CV).

Generuje krotkozyciowe podpisy HMAC, ktore pozwalaja na pobranie pliku
przez okreslony czas. Po wygasnieciu link jest niewazny.

Wzor URL: /api/v1/files/cv/<storage_key>?exp=<unix>&sig=<hmac>
"""
import base64
import hashlib
import hmac
import time
from typing import Optional

from app.config import get_settings


DEFAULT_TTL_SECONDS = 3600  # 1h


def _key() -> bytes:
    """HMAC key derived from JWT_SECRET (separate purpose to avoid token confusion)."""
    s = get_settings()
    return hashlib.sha256(("file-sig:" + s.JWT_SECRET).encode("utf-8")).digest()


def _sign(payload: str) -> str:
    sig = hmac.new(_key(), payload.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(sig).rstrip(b"=").decode("ascii")


def make_signed_url(storage_key: str, ttl_seconds: int = DEFAULT_TTL_SECONDS) -> str:
    """Zwraca relatywny URL (bez domeny) z exp + sig.

    `storage_key` to identyfikator pliku, np. "external/abc-uuid.pdf".
    """
    exp = int(time.time()) + ttl_seconds
    payload = f"{storage_key}|{exp}"
    sig = _sign(payload)
    return f"/api/v1/files/cv/{storage_key}?exp={exp}&sig={sig}"


def verify_signed_url(storage_key: str, exp: Optional[int], sig: Optional[str]) -> bool:
    """Weryfikuje podpis i czy nie wygasl. Constant-time compare."""
    if not exp or not sig:
        return False
    try:
        exp_int = int(exp)
    except (TypeError, ValueError):
        return False
    if exp_int < int(time.time()):
        return False
    expected = _sign(f"{storage_key}|{exp_int}")
    # Constant-time comparison
    return hmac.compare_digest(expected, sig)
