"""
Shared fixtures for PolacySzwajcaria backend tests.
Uses an in-memory SQLite database for isolation.
"""
import os
import uuid
import asyncio
from datetime import date, timedelta, datetime, timezone

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# Override env BEFORE importing app modules
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["DATABASE_URL_SYNC"] = "sqlite:///:memory:"
os.environ["JWT_SECRET"] = "test-secret-key-for-testing-only"
os.environ["UPLOAD_DIR"] = "./test_uploads"
os.environ["REDIS_URL"] = ""
os.environ["RECAPTCHA_ENABLED"] = "false"
os.environ["EMAIL_ENABLED"] = "false"
os.environ["RATELIMIT_ENABLED"] = "false"

# Ensure the test_uploads directory exists (required by StaticFiles)
os.makedirs("./test_uploads", exist_ok=True)
os.makedirs("./test_uploads/cv", exist_ok=True)
os.makedirs("./test_uploads/logos", exist_ok=True)

# Clear the settings cache so it picks up test env vars
from app.config import get_settings as _get_settings
_get_settings.cache_clear()

from app.database import Base, get_db
from app.core.security import hash_password, create_access_token
from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.models.employer_profile import EmployerProfile
from app.models.category import Category
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.posting_quota import PostingQuota
from app.models.system_setting import SystemSetting
from app.models.cv_file import CVFile


# ── Engine / session for tests ──────────────────────────────────────

test_engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


# ── Fixtures ─────────────────────────────────────────────────────────

@pytest_asyncio.fixture(autouse=True)
async def setup_database():
    """Create all tables before each test, drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db_session() -> AsyncSession:
    """Provide an async session scoped to a single test."""
    async with TestSession() as session:
        yield session


async def _override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


@pytest_asyncio.fixture
async def client():
    """HTTPX AsyncClient backed by the FastAPI app with test DB."""
    # Import app lazily so env vars are already set
    from app.main import app
    app.dependency_overrides[get_db] = _override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ── Helper: seed system settings ────────────────────────────────────

@pytest_asyncio.fixture
async def seed_settings(db_session: AsyncSession):
    """Seed default system settings needed by most endpoints."""
    settings_data = [
        ("default_monthly_posting_limit", "5", "integer", "Limit"),
        ("job_expiry_days", "30", "integer", "Expiry"),
        ("require_moderation", "true", "boolean", "Mod"),
        ("registration_enabled", "true", "boolean", "Reg"),
        ("max_cv_size_mb", "5", "integer", "CV"),
        ("max_job_expiry_days", "60", "integer", "Max expiry"),
    ]
    for key, val, vtype, desc in settings_data:
        db_session.add(SystemSetting(key=key, value=val, value_type=vtype, description=desc))
    await db_session.commit()


# ── Helper: create users ────────────────────────────────────────────

@pytest_asyncio.fixture
async def worker_user(db_session: AsyncSession) -> User:
    """Create a verified worker user with profile."""
    user = User(
        id=str(uuid.uuid4()),
        email="worker@test.pl",
        password_hash=hash_password("testpass123"),
        role="worker",
        first_name="Jan",
        last_name="Testowy",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = WorkerProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        canton="zurich",
        work_permit="permit_b",
        experience_years=3,
        bio="Test bio",
        languages=[{"lang": "pl", "level": "C2"}],
        skills=["python", "testing"],
    )
    db_session.add(profile)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def employer_user(db_session: AsyncSession, seed_settings) -> User:
    """Create a verified employer user with profile and quota."""
    user = User(
        id=str(uuid.uuid4()),
        email="employer@test.ch",
        password_hash=hash_password("testpass123"),
        role="employer",
        first_name="HR",
        last_name="Manager",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = EmployerProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        company_name="Test GmbH",
        company_slug="test-gmbh",
        description="Test company",
        canton="zurich",
        city="Zurich",
        is_verified=True,
    )
    db_session.add(profile)
    await db_session.flush()

    today = date.today()
    quota = PostingQuota(
        id=str(uuid.uuid4()),
        employer_id=profile.id,
        used_count=0,
        period_start=today,
        period_end=today + timedelta(days=30),
        plan_type="free",
        monthly_limit=5,
    )
    db_session.add(quota)
    await db_session.commit()
    return user


@pytest_asyncio.fixture
async def admin_user(db_session: AsyncSession) -> User:
    """Create an admin user."""
    user = User(
        id=str(uuid.uuid4()),
        email="admin@test.ch",
        password_hash=hash_password("adminpass123"),
        role="admin",
        first_name="Admin",
        last_name="Testowy",
        is_active=True,
        is_verified=True,
    )
    db_session.add(user)
    await db_session.commit()
    return user


# ── Helper: tokens ──────────────────────────────────────────────────

@pytest_asyncio.fixture
def worker_token(worker_user: User) -> str:
    return create_access_token(worker_user.id, "worker")


@pytest_asyncio.fixture
def employer_token(employer_user: User) -> str:
    return create_access_token(employer_user.id, "employer")


@pytest_asyncio.fixture
def admin_token(admin_user: User) -> str:
    return create_access_token(admin_user.id, "admin")


def auth_header(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# ── Helper: category and job ────────────────────────────────────────

@pytest_asyncio.fixture
async def category(db_session: AsyncSession) -> Category:
    cat = Category(
        id=str(uuid.uuid4()),
        name="IT i technologia",
        slug="it",
        icon="Monitor",
        sort_order=0,
        is_active=True,
    )
    db_session.add(cat)
    await db_session.commit()
    return cat


@pytest_asyncio.fixture
async def active_job(db_session: AsyncSession, employer_user: User, category: Category) -> JobOffer:
    """Create an active job offer belonging to employer_user."""
    from sqlalchemy import select
    result = await db_session.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
    )
    profile = result.scalar_one()

    job = JobOffer(
        id=str(uuid.uuid4()),
        employer_id=profile.id,
        category_id=category.id,
        title="Test Developer",
        description="This is a test job description with enough text to pass validation minimum length.",
        canton="zurich",
        city="Zurich",
        contract_type="full_time",
        salary_min=8000,
        salary_max=12000,
        salary_type="monthly",
        experience_min=2,
        is_remote="hybrid",
        languages_required=[{"lang": "en", "level": "B2"}],
        apply_via="portal",
        status="active",
        published_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        views_count=10,
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest_asyncio.fixture
async def pending_job(db_session: AsyncSession, employer_user: User, category: Category) -> JobOffer:
    """Create a pending job offer (awaiting moderation)."""
    from sqlalchemy import select
    result = await db_session.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
    )
    profile = result.scalar_one()

    job = JobOffer(
        id=str(uuid.uuid4()),
        employer_id=profile.id,
        category_id=category.id,
        title="Pending Job",
        description="This is a pending job description that needs moderation approval from admin.",
        canton="bern",
        city="Bern",
        contract_type="part_time",
        salary_min=4000,
        salary_max=5000,
        salary_type="monthly",
        experience_min=0,
        is_remote="no",
        languages_required=[],
        apply_via="portal",
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest_asyncio.fixture
async def worker_cv(db_session: AsyncSession, worker_user: User) -> CVFile:
    """Create a mock CV file record for the worker."""
    cv = CVFile(
        id=str(uuid.uuid4()),
        user_id=worker_user.id,
        original_filename="test_cv.pdf",
        stored_filename=f"{uuid.uuid4()}.pdf",
        file_path="test_uploads/cv/test.pdf",
        file_size=50000,
        mime_type="application/pdf",
        is_active=True,
        extraction_status="completed",
        extracted_name="Jan Testowy",
        extracted_email="worker@test.pl",
        extracted_phone="+41 79 000 00 00",
        extracted_languages=[{"lang": "pl", "level": "C2"}],
        extracted_text="Mock CV text with doswiadczenie zawodowe experience Erfahrung wyksztalcenie education Ausbildung",
    )
    db_session.add(cv)
    await db_session.flush()

    # Link CV to worker profile
    from sqlalchemy import select
    result = await db_session.execute(
        select(WorkerProfile).where(WorkerProfile.user_id == worker_user.id)
    )
    profile = result.scalar_one()
    profile.active_cv_id = cv.id
    await db_session.commit()
    return cv
