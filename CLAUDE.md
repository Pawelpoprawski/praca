# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

### Backend (from `backend/`)
```bash
# Run dev server
uvicorn app.main:app --reload --port 8000

# Run all tests
python -m pytest tests/ -v

# Run single test file / single test
python -m pytest tests/test_auth.py -v
python -m pytest tests/test_auth.py::TestLogin::test_login_success -v

# Database migrations
alembic revision --autogenerate -m "description"
alembic upgrade head

# Install dependencies
pip install -r requirements.txt
```

### Frontend (from `frontend/`)
```bash
npm run dev          # Dev server (port 3000)
npm run build        # Production build (standalone)
npm run lint         # ESLint
```

### Docker
```bash
docker-compose up                                    # Dev (all services)
docker-compose -f docker-compose.prod.yml up -d      # Production
```

## Architecture

**Stack**: FastAPI (async) + Next.js 14 App Router + PostgreSQL + Redis

### Backend (`backend/`)

**Request flow**: Router → Dependencies (auth/recaptcha) → Service logic → SQLAlchemy models → Response schemas

- **`app/main.py`** — App entry. Seeds database on startup (settings, categories, admin user). Starts APScheduler for background tasks (quota reset, job expiration).
- **`app/config.py`** — Pydantic Settings. All env vars defined here with defaults.
- **`app/database.py`** — Async SQLAlchemy engine. `get_db()` dependency provides sessions with auto-commit/rollback. Supports SQLite (dev) and PostgreSQL (prod) via conditional pool config.
- **`app/dependencies.py`** — Auth dependencies: `get_current_user()`, `get_current_worker()`, `get_current_employer()`, `get_current_admin()`. All validate JWT Bearer tokens.
- **`app/core/security.py`** — bcrypt hashing, JWT creation/decode (access: 15min, refresh: 7d).
- **`app/core/recaptcha.py`** — FastAPI dependency reading `X-Recaptcha-Token` header. Disabled by default via `RECAPTCHA_ENABLED`.
- **`app/services/email.py`** — Resend-based email. Disabled by default via `EMAIL_ENABLED`. Uses module-level `_resend` import (important for test mocking: patch `app.services.email._resend`).

**Routers**: `auth`, `jobs`, `worker`, `employer`, `admin`, `companies` — all mounted under `/api/v1/`.

**Key model relationships**:
- User → WorkerProfile (1:1) or EmployerProfile (1:1) based on role
- EmployerProfile → JobOffer (1:N) → Application (1:N) ← User/WorkerProfile
- EmployerProfile → PostingQuota (1:1) — 3-tier limit: custom override > quota limit > system default

**Posting quota**: Validated on job creation. Monthly limit resets via scheduler. Configurable per-employer override by admin.

**Job lifecycle**: pending → active (after moderation) → expired (auto by scheduler). Featured jobs always sort to top.

### Frontend (`frontend/src/`)

**State management**:
- **Server state**: React Query (`@tanstack/react-query`) with automatic cache/refetch
- **Auth state**: Zustand store (`store/authStore.ts`) — persists tokens to localStorage, auto-fetches user on mount via `providers.tsx`
- **Form state**: React Hook Form + Zod validation

**API layer** (`services/api.ts`): Axios instance with request interceptor (adds Bearer token) and response interceptor (auto-refreshes on 401, retries original request).

**Server vs Client components**:
- Job detail (`oferty/[id]/page.tsx`) and company (`firmy/[slug]/page.tsx`) are **server components** with `generateMetadata()` for SEO. They fetch from `BACKEND_INTERNAL_URL` (direct backend access) and pass data to client components via `initialData` prop for React Query hydration.
- Panel pages, forms, and interactive UI use `"use client"` directive.

**Frontend API proxy**: `next.config.js` rewrites `/api/*` → backend URL. Client components call `/api/...` (proxied), server components call backend directly.

**Panel routes use Polish names**: `/panel/pracownik` (worker), `/panel/pracodawca` (employer), `/panel/admin`.

## Important Patterns

- **Next.js 14 params are NOT Promises** — use `params: { id: string }`, not `Promise<{ id: string }>`. The Promise pattern is Next.js 15+ only and causes worker crashes.
- **Backend `per_page` max is 100** — API validates this. Sitemap and bulk fetches must paginate.
- **Company slugs** are auto-generated from name via `slugify()` with UUID suffix on collision.
- **Job descriptions** allow limited HTML (sanitized via bleach). Other inputs are fully stripped.
- **Auth register** requires `first_name` + `last_name` (not `full_name`), plus `role` and optionally `company_name` for employers.
- **Protected endpoints return 403** (not 401) for unauthenticated requests — this is by design in the auth middleware.
- **Test environment**: `conftest.py` sets `RECAPTCHA_ENABLED=false` and `EMAIL_ENABLED=false`. Email mock target is `app.services.email._resend`.
- **Seeding is idempotent** — runs on every startup, checks existence before insert.
- **File uploads**: UUID-based filenames in `uploads/cv/` and `uploads/logos/`. MIME validation + size limits enforced.

## Environment Variables

Backend key vars: `DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `RESEND_API_KEY`, `EMAIL_ENABLED`, `RECAPTCHA_SECRET_KEY`, `RECAPTCHA_ENABLED`, `FIRST_ADMIN_EMAIL`, `FIRST_ADMIN_PASSWORD`.

Frontend key vars: `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SITE_URL`, `NEXT_PUBLIC_RECAPTCHA_SITE_KEY`, `BACKEND_INTERNAL_URL` (for server components, defaults to `http://127.0.0.1:8000`).

See `.env.example` files in root and `backend/` for full list.

## TODO before production

- **Sprawdzić porządnie miasta i kantony w ofertach** — XML feed JOBSPL ma puste `<locations>` dla 91% ofert (328 z 360), głównie NJU JOB. AI prompt działa poprawnie (24/24 OK w lokalnych testach `backend/prompt_iteration/test_canton/`), ale dane geo nie istnieją w źródle. Opcje:
  1. Filtr UI „Cała Szwajcaria (X)" w dropdownie kantonów na `/oferty` (Recommended, ~15 min)
  2. Kontakt z NJU JOB / jobs.pl żeby wypełnili `<locations>` w XML (HTML jobs.pl jest chroniony anti-botem 403, scraping nie wchodzi w grę)
  3. Headless browser (Playwright) — drogie, kruche, ryzyko blokady IP serwera
