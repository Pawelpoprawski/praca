import re
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException, status
from app.database import get_db
from app.dependencies import get_current_user
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token,
    decode_token, create_verification_token,
)
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.models.employer_profile import EmployerProfile
from app.models.posting_quota import PostingQuota
from app.schemas.auth import (
    RegisterRequest, LoginRequest, TokenResponse,
    RefreshRequest, UserResponse, ForgotPasswordRequest,
    ResetPasswordRequest,
)
from app.schemas.common import MessageResponse

router = APIRouter(prefix="/auth", tags=["Autoryzacja"])


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(data: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """Rejestracja nowego użytkownika (pracownik lub pracodawca)."""
    # Sprawdź czy email zajęty
    existing = await db.execute(select(User).where(User.email == data.email))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Konto z tym adresem email już istnieje",
        )

    # Pracodawca musi podać nazwę firmy
    if data.role == "employer" and not data.company_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nazwa firmy jest wymagana dla konta pracodawcy",
        )

    # Utwórz użytkownika
    user = User(
        email=data.email,
        password_hash=hash_password(data.password),
        role=data.role,
        first_name=data.first_name,
        last_name=data.last_name,
        verification_token=create_verification_token(),
        is_verified=False,
    )
    db.add(user)
    await db.flush()

    # Utwórz profil w zależności od roli
    if data.role == "worker":
        profile = WorkerProfile(user_id=user.id)
        db.add(profile)
    elif data.role == "employer":
        slug = slugify(data.company_name)
        # Upewnij się że slug jest unikalny
        existing_slug = await db.execute(
            select(EmployerProfile).where(EmployerProfile.company_slug == slug)
        )
        if existing_slug.scalar_one_or_none():
            slug = f"{slug}-{str(user.id)[:8]}"

        profile = EmployerProfile(
            user_id=user.id,
            company_name=data.company_name,
            company_slug=slug,
        )
        db.add(profile)
        await db.flush()

        # Utwórz quota (limit ogłoszeń)
        today = date.today()
        quota = PostingQuota(
            employer_id=profile.id,
            used_count=0,
            period_start=today,
            period_end=today + timedelta(days=30),
            plan_type="free",
        )
        db.add(quota)

    # TODO: Wysłanie emaila weryfikacyjnego
    return user


@router.post("/login", response_model=TokenResponse)
async def login(data: LoginRequest, db: AsyncSession = Depends(get_db)):
    """Logowanie - zwraca access token i refresh token."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy email lub hasło",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Konto zostało dezaktywowane",
        )

    access_token = create_access_token(user.id, user.role)
    refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(data: RefreshRequest, db: AsyncSession = Depends(get_db)):
    """Odświeżenie access tokena przy pomocy refresh tokena."""
    payload = decode_token(data.refresh_token)

    if payload is None or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Nieprawidłowy refresh token",
        )

    user_id = payload.get("sub")
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Użytkownik nie istnieje lub jest nieaktywny",
        )

    access_token = create_access_token(user.id, user.role)
    new_refresh_token = create_refresh_token(user.id)

    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Dane aktualnie zalogowanego użytkownika."""
    return current_user


@router.get("/verify-email/{token}", response_model=MessageResponse)
async def verify_email(token: str, db: AsyncSession = Depends(get_db)):
    """Weryfikacja adresu email."""
    result = await db.execute(
        select(User).where(User.verification_token == token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nieprawidłowy lub wygasły link weryfikacyjny",
        )

    user.is_verified = True
    user.verification_token = None

    return MessageResponse(message="Email został zweryfikowany. Możesz się zalogować.")


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(data: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Wysyła email z linkiem do resetu hasła."""
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    # Zawsze zwracamy sukces (bezpieczeństwo - nie ujawniamy czy email istnieje)
    if user:
        user.reset_token = create_verification_token()
        # TODO: Wysłanie emaila z linkiem

    return MessageResponse(
        message="Jeśli konto istnieje, wysłaliśmy link do resetowania hasła."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(data: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    """Reset hasła przy użyciu tokena z emaila."""
    result = await db.execute(
        select(User).where(User.reset_token == data.token)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nieprawidłowy lub wygasły link",
        )

    user.password_hash = hash_password(data.new_password)
    user.reset_token = None
    user.reset_token_expires = None

    return MessageResponse(message="Hasło zostało zmienione. Możesz się zalogować.")
