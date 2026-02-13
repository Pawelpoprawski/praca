import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select
from app.config import get_settings
from app.database import engine, Base, async_session
from app.core.security import hash_password
from app.models import *  # noqa: F401,F403 - register all models
from app.models.user import User
from app.models.system_setting import SystemSetting
from app.routers import auth, jobs, worker, employer, companies, admin
from app.tasks.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

SEED_SETTINGS = [
    ("default_monthly_posting_limit", "5", "integer", "Domyślny limit ogłoszeń miesięcznie"),
    ("job_expiry_days", "30", "integer", "Domyślny czas wygaśnięcia oferty (dni)"),
    ("max_job_expiry_days", "60", "integer", "Maksymalny czas wygaśnięcia oferty (dni)"),
    ("max_cv_size_mb", "5", "integer", "Maksymalny rozmiar CV w MB"),
    ("require_moderation", "true", "boolean", "Czy ogłoszenia wymagają moderacji"),
    ("registration_enabled", "true", "boolean", "Czy rejestracja jest otwarta"),
]

SEED_CATEGORIES = [
    ("Budownictwo i remonty", "budownictwo", "Hammer"),
    ("Gastronomia i hotelarstwo", "gastronomia", "ChefHat"),
    ("Opieka i pielęgniarstwo", "opieka", "HeartPulse"),
    ("Transport i logistyka", "transport", "Truck"),
    ("IT i technologia", "it", "Monitor"),
    ("Sprzątanie i utrzymanie", "sprzatanie", "Sparkles"),
    ("Produkcja i przemysł", "produkcja", "Factory"),
    ("Handel i sprzedaż", "handel", "ShoppingCart"),
    ("Finanse i księgowość", "finanse", "Calculator"),
    ("Administracja i biuro", "administracja", "Briefcase"),
    ("Rolnictwo i ogrodnictwo", "rolnictwo", "Leaf"),
    ("Inne", "inne", "MoreHorizontal"),
]


async def seed_database():
    """Seed default settings, categories, and admin user."""
    async with async_session() as db:
        # System settings
        for key, value, vtype, desc in SEED_SETTINGS:
            existing = await db.execute(
                select(SystemSetting).where(SystemSetting.key == key)
            )
            if not existing.scalar_one_or_none():
                db.add(SystemSetting(key=key, value=value, value_type=vtype, description=desc))
                logger.info(f"Seeded setting: {key}")

        # Categories
        from app.models.category import Category
        for name, slug, icon in SEED_CATEGORIES:
            existing = await db.execute(
                select(Category).where(Category.slug == slug)
            )
            if not existing.scalar_one_or_none():
                db.add(Category(name=name, slug=slug, icon=icon, sort_order=SEED_CATEGORIES.index((name, slug, icon))))
                logger.info(f"Seeded category: {name}")

        # Admin user
        admin_email = settings.FIRST_ADMIN_EMAIL
        existing_admin = await db.execute(select(User).where(User.email == admin_email))
        if not existing_admin.scalar_one_or_none():
            admin_user = User(
                email=admin_email,
                password_hash=hash_password(settings.FIRST_ADMIN_PASSWORD),
                role="admin",
                first_name="Admin",
                last_name="System",
                is_active=True,
                is_verified=True,
            )
            db.add(admin_user)
            logger.info(f"Seeded admin user: {admin_email}")

        await db.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created")

    await seed_database()
    logger.info("Database seeded")

    from app.seed_data import seed_demo_data
    await seed_demo_data()

    start_scheduler()

    yield

    # Shutdown
    stop_scheduler()
    await engine.dispose()


app = FastAPI(
    title="PolacySzwajcaria API",
    description="Portal pracy dla Polaków w Szwajcarii",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Security headers
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


# Static files (uploads)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(worker.router, prefix="/api/v1")
app.include_router(employer.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "PolacySzwajcaria API"}
