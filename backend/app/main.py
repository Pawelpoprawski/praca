import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from sqlalchemy import select
from app.config import get_settings
from app.database import engine, Base, async_session
from app.core.security import hash_password
from app.core.rate_limit import limiter
from app.models import *  # noqa: F401,F403 - register all models
from app.models.user import User
from app.models.system_setting import SystemSetting
from app.routers import auth, auth_oauth, jobs, worker, employer, companies, admin, notifications, reviews, job_alerts, cv_review, files
from app.tasks.scheduler import start_scheduler, stop_scheduler

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

settings = get_settings()

SEED_SETTINGS = [
    ("default_monthly_posting_limit", "200", "integer", "Domyślny limit ogłoszeń miesięcznie"),
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
    title="Praca w Szwajcarii API",
    description="Portal pracy dla Polaków w Szwajcarii",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Rate limiter
app.state.limiter = limiter


async def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom 429 handler - JSON response instead of default HTML."""
    return JSONResponse(
        status_code=429,
        content={
            "detail": "Zbyt wiele żądań. Spróbuj ponownie za chwilę.",
            "retry_after": str(exc.detail),
        },
    )


app.add_exception_handler(RateLimitExceeded, custom_rate_limit_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS — w produkcji tylko whitelisted origins, lokalne hosty tylko gdy ENVIRONMENT != production
_cors_origins = [settings.FRONTEND_URL]
if os.getenv("ENVIRONMENT", "development").lower() != "production":
    _cors_origins.extend(["http://localhost:3000", "http://localhost:3002"])
# Dodatkowo: jezeli ALLOWED_ORIGINS w env (comma-separated)
_extra = os.getenv("ALLOWED_ORIGINS", "")
if _extra:
    _cors_origins.extend([o.strip() for o in _extra.split(",") if o.strip()])
# Usun duplikaty zachowujac kolejnosc
_cors_origins = list(dict.fromkeys(_cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Recaptcha-Token", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
    max_age=600,
)


# Audit log: wszystkie mutacje na /api/v1/admin/* logowane do activity_logs
@app.middleware("http")
async def admin_audit_log(request: Request, call_next):
    response = await call_next(request)
    try:
        path = request.url.path
        method = request.method
        if (
            path.startswith("/api/v1/admin/")
            and method in ("POST", "PUT", "PATCH", "DELETE")
            and 200 <= response.status_code < 400
        ):
            # Pobranie user_id z tokena (nie request.state — bo nie zawsze jest)
            user_id = None
            auth = request.headers.get("authorization", "")
            if auth.startswith("Bearer "):
                try:
                    from app.core.security import decode_token
                    payload = decode_token(auth[7:])
                    if payload:
                        user_id = payload.get("sub")
                except Exception:
                    pass
            from app.services.activity_logger import log_activity
            await log_activity(
                event_type=f"admin_{method.lower()}",
                summary=f"{method} {path} -> {response.status_code}",
                entity_type="admin_action",
                entity_id=user_id,
                details={"path": path, "method": method, "status": response.status_code},
            )
    except Exception:
        # Nigdy nie blokuj response z powodu audit logu
        pass
    return response


# Security headers
@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "geolocation=(), microphone=(), camera=(), payment=(), usb=(), "
        "fullscreen=(self), interest-cohort=()"
    )
    # HSTS tylko jezeli aplikacja serwowana po HTTPS (production)
    if request.url.scheme == "https" or request.headers.get("x-forwarded-proto") == "https":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains; preload"
    # CSP — pozwala na JSON-LD inline, reCAPTCHA, Google Fonts, samego siebie
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://www.google.com https://www.gstatic.com; "
        "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
        "font-src 'self' https://fonts.gstatic.com data:; "
        "img-src 'self' data: https: blob:; "
        "connect-src 'self' https://www.google.com https://api.resend.com; "
        "frame-src https://www.google.com; "
        "object-src 'none'; "
        "base-uri 'self'; "
        "form-action 'self'; "
        "frame-ancestors 'none'"
    )
    return response


# Static files (uploads)
# UWAGA: tylko publiczne assety (logos firm). Prywatne pliki (CV) IDZIE PRZEZ /api/v1/files/cv/* (signed URL lub auth).
_logos_dir = os.path.join(settings.UPLOAD_DIR, "logos")
os.makedirs(_logos_dir, exist_ok=True)
app.mount("/uploads/logos", StaticFiles(directory=_logos_dir), name="logos")

# Routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(auth_oauth.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(worker.router, prefix="/api/v1")
app.include_router(employer.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(notifications.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(job_alerts.router, prefix="/api/v1")
app.include_router(cv_review.router, prefix="/api/v1")
app.include_router(files.router, prefix="/api/v1")


@app.get("/api/health")
async def health_check():
    return {"status": "ok", "service": "Praca w Szwajcarii API"}
