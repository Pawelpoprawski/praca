# PolacySzwajcaria - Portal Pracy dla Polakow w Szwajcarii

Portal ogloszen o prace skierowany do polskiej spolecznosci w Szwajcarii. Laczy pracodawcow szukajacych pracownikow z kandydatami szukajacymi zatrudnienia, z wbudowanym systemem AI do analizy CV i automatycznej ekstrakcji danych z ofert pracy.

## Stos technologiczny

| Warstwa | Technologia |
|---------|-------------|
| Backend | FastAPI (Python 3.12, async) |
| Frontend | Next.js 14 (App Router, TypeScript) |
| Baza danych | PostgreSQL 16 |
| Cache | Redis 7 |
| Reverse proxy | Nginx 1.25 |
| AI | OpenAI GPT-4o-mini (ekstrakcja CV/ofert, tlumaczenia) |
| Email | Resend API |
| Konteneryzacja | Docker + Docker Compose |

## Funkcjonalnosci

### Dla pracownikow
- Przegladanie i wyszukiwanie ofert pracy (filtrowanie po kantonie, kategorii, wynagrodzeniu, trybie pracy)
- Rejestracja i profil pracownika
- Upload CV (PDF/DOCX) z automatyczna ekstrakcja AI
- Sprawdz CV - darmowa analiza AI z ocena i sugestiami
- Aplikowanie na oferty (standardowe i szybkie 1-click)
- Zapisywanie ofert, historia przegladania
- Alerty o nowych ofertach (email: natychmiastowy/dzienny/tygodniowy)
- Powiadomienia o statusie aplikacji

### Dla pracodawcow
- Panel zarzadzania ogoszeniami (CRUD, kopiowanie, zamykanie)
- AI parser ofert - wklej tekst z innego portalu, AI wyciagnie dane
- Dashboard z analityka (wykresy aplikacji, top oferty, konwersja)
- Przeglad kandydatow i zarzadzanie statusami aplikacji
- Eksport kandydatow do CSV
- Profil firmy z logiem
- System limitow publikacji (darmowy/basic/premium)

### Dla administratora
- Moderacja ofert pracy (zatwierdzanie/odrzucanie)
- Zarzadzanie uzytkownikami (aktywacja/dezaktywacja)
- Zarzadzanie firmami i ich limitami
- Baza CV z wyszukiwaniem i eksportem XLSX
- Moderacja recenzji pracodawcow
- Zarzadzanie kategoriami i ustawieniami systemowymi
- Dashboard ze statystykami i trendami
- Eksport danych (CSV)
- Panel sterowania scraperami ofert

### System AI (procesy w tle)
- **Ekstrakcja CV** - co 2 min przetwarza nowe CV: wyciaga umiejetnosci, doswiadczenie, jezyki, lokalizacje
- **Tlumaczenie ofert** - co 2 min tlumaczenie DE/FR/IT -> PL dla zescrapowanych ofert
- **Ekstrakcja ofert** - co 3 min wyciaga metadane z opisow: skills, seniority, pensum, zakwaterowanie, benefity
- **Scraping ofert** - automatyczne pobieranie z Jobs.pl, FachPraca, RolJob, Adecco

## Struktura projektu

```
PolacySzwajcaria/
├── backend/                  # FastAPI REST API
│   ├── app/
│   │   ├── main.py          # Entry point, middleware, lifespan
│   │   ├── config.py        # Konfiguracja (env vars)
│   │   ├── database.py      # SQLAlchemy async engine
│   │   ├── dependencies.py  # Auth dependencies (JWT)
│   │   ├── core/            # Security, reCAPTCHA, rate limit, sanitize
│   │   ├── models/          # 20 modeli SQLAlchemy
│   │   ├── routers/         # 10 routerow API
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── services/        # Logika biznesowa, AI, email, scraping
│   │   └── tasks/           # APScheduler - zadania w tle
│   ├── alembic/             # Migracje bazy (17 wersji)
│   ├── tests/               # 17 plikow testowych, 370+ testow
│   └── requirements.txt
├── frontend/                 # Next.js 14 App Router
│   ├── src/
│   │   ├── app/             # Strony i routing
│   │   │   ├── oferty/      # Lista ofert + szczegoly (SSR/SEO)
│   │   │   ├── firmy/       # Profile firm (SSR/SEO)
│   │   │   ├── sprawdz-cv/  # Analiza CV
│   │   │   ├── panel/       # Panele (pracownik/pracodawca/admin)
│   │   │   ├── login/       # Logowanie
│   │   │   └── register/    # Rejestracja
│   │   ├── components/      # Komponenty UI
│   │   ├── services/        # Warstwa API (Axios)
│   │   ├── store/           # Zustand (auth state)
│   │   ├── types/           # TypeScript interfaces
│   │   └── lib/             # Helpery, formatowanie
│   └── Dockerfile           # Multi-stage build (Node 20)
├── nginx/                    # Reverse proxy
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml        # Development
├── docker-compose.dev.yml    # Dev (inne porty)
├── docker-compose.prod.yml   # Production
└── .env.example
```

## API - Endpointy

| Router | Prefix | Endpointy | Opis |
|--------|--------|-----------|------|
| auth | `/api/v1/auth` | 7 | Rejestracja, logowanie, JWT refresh, weryfikacja email, reset hasla |
| jobs | `/api/v1/jobs` | 8 | Lista ofert, filtry, szczegoly, podobne oferty, kategorie |
| worker | `/api/v1/worker` | 14 | Profil, CV upload/analiza, aplikacje, zapisane oferty |
| employer | `/api/v1/employer` | 20+ | Profil firmy, CRUD ogloszen, kandydaci, dashboard, AI parser |
| admin | `/api/v1/admin` | 25+ | Moderacja, uzytkownicy, firmy, CV baza, statystyki, scraper |
| alerts | `/api/v1/alerts` | 6 | Alerty o nowych ofertach |
| reviews | `/api/v1/reviews` | 4 | Recenzje pracodawcow |
| cv-review | `/api/v1/cv-review` | 5 | Analiza CV przez AI |
| notifications | `/api/v1/notifications` | 3 | Powiadomienia uzytkownikow |
| companies | `/api/v1/companies` | 2 | Lista firm, profil firmy |

Dokumentacja API: `/api/docs` (Swagger) | `/api/redoc` (ReDoc)

## Uruchomienie lokalne

### Wymagania
- Python 3.12+
- Node.js 20+
- PostgreSQL 16 (lub SQLite do dev)
- Redis 7
- Docker + Docker Compose (opcjonalnie)

### Opcja 1: Docker (zalecane)

```bash
# Development (z hot reload)
docker-compose up

# Dostep:
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/api/docs
# PostgreSQL: localhost:5432
```

### Opcja 2: Reczne uruchomienie

```bash
# Backend
cd backend
pip install -r requirements.txt
cp .env.example .env          # Uzupelnic dane
uvicorn app.main:app --reload --port 8001

# Frontend (nowy terminal)
cd frontend
npm install
npm run dev                   # http://localhost:3002
```

Przy starcie backend automatycznie:
- Tworzy tabele w bazie
- Seeduje kategorie, ustawienia systemowe i konto admina
- Uruchamia scheduler (ekstrakcja CV/ofert, tlumaczenia, alerty)

### Konto admina (seed)

Ustawiane przez zmienne srodowiskowe:
```
FIRST_ADMIN_EMAIL=admin@example.com
FIRST_ADMIN_PASSWORD=admin123
```

## Deploy produkcyjny

### Architektura

```
Internet
   │
   ▼
┌─────────┐
│  Nginx  │ :80/:443  (reverse proxy, SSL, gzip, cache)
└────┬────┘
     │
     ├──────────────────┐
     ▼                  ▼
┌──────────┐     ┌───────────┐
│ Frontend │     │  Backend  │
│ Next.js  │     │  FastAPI  │
│  :3000   │     │  :8000    │
└──────────┘     └─────┬─────┘
                       │
              ┌────────┼────────┐
              ▼        ▼        ▼
         ┌────────┐ ┌───────┐ ┌────────┐
         │Postgres│ │ Redis │ │ OpenAI │
         │ :5432  │ │ :6379 │ │  API   │
         └────────┘ └───────┘ └────────┘
```

### Uruchomienie produkcji

```bash
# 1. Skonfigurowac zmienne srodowiskowe
cp .env.example .env
# Uzupelnic: DB_PASSWORD, SITE_URL, RECAPTCHA keys

cp backend/.env.example backend/.env
# Uzupelnic: DATABASE_URL (postgres), JWT_SECRET, OPENAI_API_KEY,
#            RESEND_API_KEY, EMAIL_ENABLED=true, RECAPTCHA_ENABLED=true

# 2. Uruchomic
docker-compose -f docker-compose.prod.yml up -d

# 3. Sprawdzic status
docker-compose -f docker-compose.prod.yml ps
```

### Roznice dev vs prod

| Aspekt | Development | Production |
|--------|-------------|------------|
| Backend | 1 worker + --reload | 2 workery uvicorn |
| Frontend | npm run dev (HMR) | standalone build (node server.js) |
| Baza | SQLite (plik) | PostgreSQL 16 |
| Proxy | next.config.js rewrites | Nginx reverse proxy |
| SSL | brak | Let's Encrypt (certbot) |
| Email | wylaczony | Resend API |
| reCAPTCHA | wylaczony | Google reCAPTCHA v3 |
| Restart | brak | unless-stopped |
| Health checks | 5s interval | 30s interval |

### SSL (Let's Encrypt)

Konfiguracja Nginx jest przygotowana pod certbot. Aby wlaczyc SSL:

1. Odkomentowac sekcje SSL w `nginx/nginx.conf`
2. Uruchomic certbot:
```bash
docker run --rm -v certbot-conf:/etc/letsencrypt -v certbot-www:/var/www/certbot \
  certbot/certbot certonly --webroot -w /var/www/certbot -d polacyszwajcaria.ch
```
3. Restart nginx

### Nginx routing

| Sciezka | Cel | Cache |
|---------|-----|-------|
| `/api/*` | backend:8000 | brak |
| `/uploads/*` | backend:8000 | 7 dni |
| `/*` | frontend:3000 | brak |

### Healthchecki

Kazdy serwis ma healthcheck:
- **PostgreSQL**: `pg_isready`
- **Redis**: `redis-cli ping`
- **Backend**: `GET /api/health` → `{"status": "ok"}`
- **Frontend**: `wget http://localhost:3000`
- **Nginx**: `wget http://localhost:80`

## Zmienne srodowiskowe

### Backend (.env)

| Zmienna | Domyslna | Opis |
|---------|----------|------|
| `DATABASE_URL` | sqlite+aiosqlite:///./polacyszwajcaria.db | URL bazy danych |
| `REDIS_URL` | redis://localhost:6379 | URL Redis |
| `JWT_SECRET` | - | Klucz JWT (wymagany w prod) |
| `OPENAI_API_KEY` | - | Klucz OpenAI (ekstrakcja AI) |
| `RESEND_API_KEY` | - | Klucz Resend (email) |
| `EMAIL_ENABLED` | false | Wlaczenie wysylki email |
| `RECAPTCHA_SECRET_KEY` | - | Klucz reCAPTCHA v3 |
| `RECAPTCHA_ENABLED` | false | Wlaczenie reCAPTCHA |
| `FIRST_ADMIN_EMAIL` | admin@example.com | Email konta admina |
| `FIRST_ADMIN_PASSWORD` | admin123 | Haslo konta admina |
| `FRONTEND_URL` | http://localhost:3000 | URL frontendu (do linkow w email) |

### Frontend

| Zmienna | Domyslna | Opis |
|---------|----------|------|
| `NEXT_PUBLIC_SITE_URL` | - | Publiczny URL strony |
| `NEXT_PUBLIC_RECAPTCHA_SITE_KEY` | - | Klucz publiczny reCAPTCHA |
| `BACKEND_INTERNAL_URL` | http://127.0.0.1:8000 | URL backendu (server components) |

## Testy

```bash
cd backend

# Wszystkie testy
python -m pytest tests/ -v

# Konkretny plik
python -m pytest tests/test_auth.py -v

# Konkretny test
python -m pytest tests/test_auth.py::TestLogin::test_login_success -v
```

Srodowisko testowe automatycznie:
- Uzywa SQLite in-memory
- Wylacza reCAPTCHA i email
- Seeduje dane testowe

**Pokrycie**: 17 plikow testowych, 370+ testow obejmujacych auth, CRUD, filtry, AI ekstrakcje, bugi i regresje.

## Migracje bazy

```bash
cd backend

# Nowa migracja
alembic revision --autogenerate -m "opis zmian"

# Zastosuj migracje
alembic upgrade head

# Cofnij ostatnia
alembic downgrade -1
```

## Zadania w tle (Scheduler)

| Zadanie | Czestotliwosc | Opis |
|---------|---------------|------|
| Ekstrakcja CV | co 2 min | Przetwarza nowe CV w CVDatabase |
| Tlumaczenie ofert | co 2 min | Tlumaczy zescrapowane oferty DE/FR/IT → PL |
| Ekstrakcja ofert | co 3 min | Wyciaga metadane z opisow ofert |
| Alerty o ofertach | co 1h | Wysyla email z nowymi dopasowanymi ofertami |
| Reset limitow | codziennie 00:05 | Resetuje limity publikacji pracodawcow |
| Wygaszanie ofert | codziennie 01:00 | Zmienia status na "expired" |
| Sync Jobs.pl | codziennie 06:00 | Pobiera oferty z Jobs.pl |

## Licencja

Projekt prywatny. Wszelkie prawa zastrzezone.
