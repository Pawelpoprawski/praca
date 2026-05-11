"""Zabezpieczone pobieranie plikow prywatnych (CV).

Dwie sciezki dostepu:
1. Signed URL z exp + sig — uzywany do tymczasowego udostepnienia (np. email do pracodawcy).
2. Auth zalogowanego usera — admin albo wlasciciel CV (worker).

Pliki dostepne tylko przez ten router, NIE przez publiczne StaticFiles.
"""
import os
import mimetypes
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.core.signed_urls import verify_signed_url
from app.dependencies import get_current_user_optional
from app.models.user import User

router = APIRouter(prefix="/files", tags=["files"])


_ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".odt", ".txt", ".rtf"}


def _safe_resolve(base_dir: str, relative_path: str) -> Path:
    """Zabezpiecz przed path traversal — wymusza ze plik lezy wewnatrz base_dir."""
    base = Path(base_dir).resolve()
    target = (base / relative_path).resolve()
    try:
        target.relative_to(base)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid path")
    return target


async def _is_admin(user: User | None) -> bool:
    return user is not None and user.role == "admin"


@router.get("/cv/{storage_key:path}")
async def download_cv(
    storage_key: str,
    request: Request,
    exp: int | None = Query(None),
    sig: str | None = Query(None),
    current_user: User | None = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    """Pobierz CV przez signed URL lub jako admin/wlasciciel.

    - signed URL: ?exp=...&sig=... (sprawdzane przez HMAC, TTL ~1h)
    - admin: zalogowany user z role=admin
    - wlasciciel: zalogowany worker ktorego CV jest w storage_key (TODO)
    """
    # Walidacja rozszerzenia
    ext = os.path.splitext(storage_key)[1].lower()
    if ext not in _ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Nieprawidlowe rozszerzenie")

    # Autoryzacja: signed URL ALBO admin
    if verify_signed_url(storage_key, exp, sig):
        pass  # OK
    elif await _is_admin(current_user):
        pass  # OK
    else:
        # TODO: sprawdz czy worker jest wlascicielem (po WorkerProfile.cv_path)
        raise HTTPException(status_code=403, detail="Brak uprawnien")

    settings = get_settings()
    cv_base = os.path.join(settings.UPLOAD_DIR, "cv")
    file_path = _safe_resolve(cv_base, storage_key)

    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Plik nie istnieje")

    media_type, _ = mimetypes.guess_type(str(file_path))
    media_type = media_type or "application/octet-stream"

    return FileResponse(
        path=str(file_path),
        media_type=media_type,
        filename=file_path.name,
        headers={
            # Ostry cache-control — plik z signed URL nie powinien byc cachowany
            "Cache-Control": "private, no-store, max-age=0",
            "Content-Disposition": f'attachment; filename="{file_path.name}"',
            "X-Content-Type-Options": "nosniff",
        },
    )
