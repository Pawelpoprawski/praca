# PolacySzwajcaria - Kompletny Plan Produktu

> Portal pracy dla Polaków w Szwajcarii
> Wersja: 1.0 | Data: 2026-02-12

---

## Spis treści

1. [Wizja produktu](#1-wizja-produktu)
2. [Decyzja architektoniczna: FastAPI vs Django](#2-decyzja-architektoniczna)
3. [Role i uprawnienia](#3-role-i-uprawnienia)
4. [Struktura bazy danych](#4-struktura-bazy-danych)
5. [API - endpointy backendowe](#5-api---endpointy-backendowe)
6. [System limitów ogłoszeń](#6-system-limitów-ogłoszeń)
7. [Struktura frontendu](#7-struktura-frontendu)
8. [UX i struktura stron](#8-ux-i-struktura-stron)
9. [Wyszukiwarka](#9-wyszukiwarka)
10. [Bezpieczeństwo i RODO](#10-bezpieczeństwo-i-rodo)
11. [Architektura techniczna](#11-architektura-techniczna)
12. [Roadmapa](#12-roadmapa)
13. [Przyszła monetyzacja](#13-przyszła-monetyzacja)
14. [Design system](#14-design-system)

---

## 1. Wizja produktu

### Problem
Polacy w Szwajcarii nie mają dedykowanego, polskojęzycznego portalu pracy. Korzystają z rozproszonych grup na Facebooku, ogólnych portali (jobs.ch, indeed.ch) w językach obcych, lub poleceń ustnych. Brakuje profesjonalnego narzędzia, które łączy polskich pracowników z pracodawcami szukającymi polskojęzycznych pracowników w Szwajcarii.

### Rozwiązanie
Profesjonalny portal pracy w 100% po polsku, skupiony na rynku szwajcarskim. Interfejs inspirowany pracuj.pl/indeed, ale dostosowany do specyfiki szwajcarskiego rynku pracy (kantony, pozwolenia na pracę, wielojęzyczność).

### Unikalna wartość (USP)
- Jedyny polskojęzyczny portal pracy dedykowany Szwajcarii
- Filtry specyficzne dla CH: kanton, typ pozwolenia na pracę, wymagany język
- Zrozumienie specyfiki polskiego pracownika w CH (pozwolenia B/C/G/L, cross-border)
- Prostota i profesjonalizm

### Grupa docelowa
- **Pracownicy**: ~100 000 Polaków mieszkających w Szwajcarii + Polacy z pogranicza (Grenzgänger)
- **Pracodawcy**: Firmy w CH szukające polskojęzycznych pracowników, polskie firmy działające w CH, agencje pracy

---

## 2. Decyzja architektoniczna

### Rekomendacja: FastAPI

| Kryterium | FastAPI | Django |
|---|---|---|
| API-first design | Natywne, idealne dla React SPA | Wymaga DRF jako dodatku |
| Wydajność | Async, ~3x szybszy | Synchroniczny, wolniejszy |
| Typowanie | Pydantic - walidacja + typy | Serializery DRF - więcej boilerplate |
| Dokumentacja API | Auto Swagger/ReDoc | Wymaga konfiguracji |
| Panel admina | Brak wbudowanego (budujemy w React) | Wbudowany (ale i tak chcemy React) |
| ORM | SQLAlchemy 2.0 (async) | Django ORM (dojrzały, ale sync) |
| Background tasks | Celery / APScheduler / natywne | Celery |
| Krzywa uczenia | Łatwy do opanowania | Więcej konwencji do nauki |
| Skalowalność | Lepsza (async I/O) | Dobra, ale sync |
| Ekosystem | Mniejszy, ale rosnący | Ogromny, dojrzały |

### Dlaczego FastAPI wygrywa:

1. **API-first**: Cały frontend to React SPA - potrzebujemy czystego API, nie renderowania szablonów. FastAPI jest do tego stworzony.
2. **Wydajność async**: Upload CV, wysyłanie emaili, background tasks - async jest kluczowy.
3. **Pydantic**: Modele danych z automatyczną walidacją to ogromna oszczędność czasu. Idealne dla formularzy rejestracji, ogłoszeń.
4. **Auto-dokumentacja**: Swagger UI out-of-the-box - bezcenne przy współpracy frontend/backend.
5. **Panel admina**: I tak budujemy go w React (potrzebujemy custom UI), więc wbudowany admin Django nie jest przewagą.
6. **SQLAlchemy 2.0**: Async ORM z full type-hinting, równie dojrzały jak Django ORM.

### Stack technologiczny:

```
Backend:
  - Python 3.12+
  - FastAPI 0.110+
  - SQLAlchemy 2.0 (async, z Alembic do migracji)
  - PostgreSQL 16
  - Redis (cache, sesje, rate limiting)
  - Celery + Redis (background tasks)
  - Pydantic v2 (walidacja)
  - python-jose (JWT)
  - boto3 (S3 upload w przyszłości)
  - python-multipart (upload plików)

Frontend:
  - React 18 / Next.js 14
  - TypeScript
  - Tailwind CSS + shadcn/ui
  - React Query (TanStack Query) - data fetching
  - React Hook Form + Zod - formularze
  - Zustand - state management (lekki, prostszy niż Redux)
  - Axios - HTTP client

Infrastruktura:
  - Docker + Docker Compose (dev)
  - Nginx (reverse proxy, static files)
  - GitHub Actions (CI/CD)
  - AWS S3 / MinIO (pliki CV) - przyszłość
```

---

## 3. Role i uprawnienia

### 3.1 Gość (niezalogowany)

**Widoki:**
- Strona główna (hero + wyszukiwarka + ostatnie oferty)
- Lista ofert z filtrami
- Szczegóły oferty (pełne, z przyciskiem "Aplikuj" przekierowującym do logowania)
- Strona firmy (profil publiczny)
- Rejestracja / Logowanie

**Ograniczenia:**
- Nie może aplikować
- Nie może dodawać ogłoszeń
- Nie widzi danych kontaktowych pracodawcy
- Nie ma panelu

**Endpointy:**
- `GET /api/jobs` - lista ofert
- `GET /api/jobs/{id}` - szczegóły oferty
- `GET /api/jobs/categories` - kategorie
- `GET /api/companies/{id}` - profil firmy
- `POST /api/auth/register` - rejestracja
- `POST /api/auth/login` - logowanie

---

### 3.2 Pracownik (worker)

**Widoki:**
- Wszystko co gość +
- Panel pracownika (dashboard)
  - Moje aplikacje (lista z statusami)
  - Mój profil (edycja danych)
  - Moje CV (upload/zamiana/usunięcie)
  - Ustawienia konta
- Formularz aplikowania na ofertę (bezpośrednio ze strony oferty)

**Flow użytkownika:**
1. Rejestracja -> Weryfikacja email -> Uzupełnienie profilu -> Upload CV
2. Przeglądanie ofert -> Filtrowanie -> Klik "Aplikuj" -> Potwierdzenie -> Status w panelu

**Dane profilu:**
- Imię, nazwisko
- Email, telefon
- Kanton zamieszkania
- Typ pozwolenia na pracę (B/C/G/L/brak)
- Języki (PL + poziomy DE/FR/IT/EN)
- Lata doświadczenia
- Branża/specjalizacja
- Krótkie bio
- CV (PDF, max 5MB)
- Oczekiwane wynagrodzenie (opcjonalne)
- Dostępność od (data)

**Ograniczenia:**
- Może mieć 1 aktywne CV (zamiana, nie kumulacja)
- Może aplikować na ofertę tylko raz
- Nie widzi aplikacji innych kandydatów

**Endpointy:**
- `GET /api/worker/profile` - mój profil
- `PUT /api/worker/profile` - aktualizacja profilu
- `POST /api/worker/cv` - upload CV
- `DELETE /api/worker/cv` - usunięcie CV
- `GET /api/worker/cv` - pobranie swojego CV
- `POST /api/jobs/{id}/apply` - aplikowanie
- `GET /api/worker/applications` - moje aplikacje
- `GET /api/worker/applications/{id}` - szczegóły aplikacji
- `PUT /api/worker/settings` - ustawienia konta
- `DELETE /api/worker/account` - usunięcie konta (RODO)

---

### 3.3 Pracodawca (employer)

**Widoki:**
- Wszystko co gość +
- Panel pracodawcy (dashboard)
  - Statystyki (ilość aktywnych ofert, aplikacji, wyświetleń)
  - Moje ogłoszenia (lista z statusami)
  - Dodaj ogłoszenie (formularz)
  - Edytuj ogłoszenie
  - Lista kandydatów na ofertę
  - Profil firmy (edycja)
  - Informacja o limicie ogłoszeń (X/Y wykorzystanych)
  - Ustawienia konta

**Flow dodawania ogłoszenia:**
1. Klik "Dodaj ogłoszenie" -> Sprawdzenie limitu -> Formularz -> Podgląd -> Wyślij do moderacji
2. Admin zatwierdza -> Ogłoszenie aktywne -> Powiadomienie email
3. Admin odrzuca -> Powiadomienie z powodem -> Możliwość edycji i ponownego wysłania

**Dane ogłoszenia:**
- Tytuł stanowiska
- Opis (rich text, z sanitizacją HTML)
- Kategoria/branża
- Kanton
- Miasto
- Typ umowy (pełny etat, część etatu, zlecenie, tymczasowa, praktyka)
- Wynagrodzenie min/max (CHF, opcjonalne, "do uzgodnienia")
- Wymagany język (DE/FR/IT/EN + poziom)
- Wymagane pozwolenie na pracę (lub "sponsorujemy")
- Wymagane doświadczenie (lata)
- Praca zdalna (tak/nie/hybrydowo)
- Data wygaśnięcia (domyślnie +30 dni, max 60 dni)
- Dane kontaktowe (email firmy / formularz przez portal)

**Dane profilu firmy:**
- Nazwa firmy
- Logo (upload, max 2MB, jpg/png)
- Opis firmy
- Branża
- Strona WWW
- Adres (kanton, miasto)
- Numer UID (opcjonalny, do weryfikacji)
- Wielkość firmy (1-10, 11-50, 51-200, 200+)

**Ograniczenia:**
- Limit ogłoszeń miesięcznie (konfigurowalny przez admina)
- Ogłoszenia wymagają zatwierdzenia admina
- Nie widzi danych osobowych pracowników, których nie aplikowało
- Ogłoszenie wygasa automatycznie po X dniach

**Endpointy:**
- `GET /api/employer/profile` - profil firmy
- `PUT /api/employer/profile` - aktualizacja profilu
- `POST /api/employer/profile/logo` - upload logo
- `GET /api/employer/dashboard` - statystyki
- `GET /api/employer/jobs` - moje ogłoszenia
- `POST /api/employer/jobs` - dodaj ogłoszenie
- `PUT /api/employer/jobs/{id}` - edytuj ogłoszenie
- `DELETE /api/employer/jobs/{id}` - usuń ogłoszenie
- `GET /api/employer/jobs/{id}/applications` - kandydaci na ofertę
- `PUT /api/employer/applications/{id}/status` - zmień status aplikacji
- `GET /api/employer/quota` - informacja o limicie
- `PUT /api/employer/settings` - ustawienia konta

---

### 3.4 Administrator

**Widoki:**
- Panel admina (osobny layout)
  - Dashboard ze statystykami (nowe rejestracje, oferty, aplikacje, aktywni użytkownicy)
  - Moderacja ogłoszeń (lista pending, approve/reject z komentarzem)
  - Zarządzanie użytkownikami (lista, filtrowanie, ban/unban, zmiana roli)
  - Zarządzanie kategoriami (CRUD, sortowanie, ikony)
  - Ustawienia systemowe (limity, konfiguracja)
  - Logi systemowe

**Ograniczenia:**
- Dostęp tylko dla roli `admin`
- Akcje logowane w audit log
- Nie może usunąć swojego konta admina

**Endpointy:**
- `GET /api/admin/dashboard` - statystyki
- `GET /api/admin/jobs/pending` - ogłoszenia do moderacji
- `PUT /api/admin/jobs/{id}/approve` - zatwierdź
- `PUT /api/admin/jobs/{id}/reject` - odrzuć (z powodem)
- `GET /api/admin/users` - lista użytkowników
- `GET /api/admin/users/{id}` - szczegóły użytkownika
- `PUT /api/admin/users/{id}/status` - ban/unban
- `PUT /api/admin/users/{id}/role` - zmiana roli
- `GET /api/admin/categories` - kategorie
- `POST /api/admin/categories` - dodaj kategorię
- `PUT /api/admin/categories/{id}` - edytuj
- `DELETE /api/admin/categories/{id}` - usuń (soft delete)
- `PUT /api/admin/categories/reorder` - zmień kolejność
- `GET /api/admin/settings` - ustawienia systemowe
- `PUT /api/admin/settings` - zmień ustawienia
- `PUT /api/admin/employers/{id}/quota` - nadpisz limit dla pracodawcy
- `GET /api/admin/audit-log` - logi

---

## 4. Struktura bazy danych

### Diagram relacji (ERD)

```
Users 1──── 1 WorkerProfiles
Users 1──── 1 EmployerProfiles
Users 1──── * CVFiles
EmployerProfiles 1──── * JobOffers
EmployerProfiles 1──── 1 PostingQuotas
JobOffers *──── 1 Categories
JobOffers 1──── * Applications
Applications *──── 1 Users (worker)
Applications *──── 0..1 CVFiles
JobOffers *──── * JobOfferLanguages
SystemSettings (standalone)
AuditLog (standalone)
```

### Tabele

#### `users`
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           VARCHAR(255) UNIQUE NOT NULL,
    password_hash   VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL CHECK (role IN ('worker', 'employer', 'admin')),
    first_name      VARCHAR(100),
    last_name       VARCHAR(100),
    phone           VARCHAR(20),
    is_active       BOOLEAN DEFAULT true,
    is_verified     BOOLEAN DEFAULT false,
    verification_token VARCHAR(255),
    reset_token     VARCHAR(255),
    reset_token_expires TIMESTAMPTZ,
    last_login      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
```

**Uwagi:**
- UUID zamiast autoincrement - bezpieczniejsze w URL, nie ujawnia ilości użytkowników
- `role` jako enum-like CHECK - prostsze niż osobna tabela ról w MVP
- `is_verified` - wymuszamy weryfikację email przed pełnym dostępem

---

#### `worker_profiles`
```sql
CREATE TABLE worker_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    canton          VARCHAR(50),
    work_permit     VARCHAR(20) CHECK (work_permit IN (
                        'permit_b', 'permit_c', 'permit_g', 'permit_l',
                        'eu_efta', 'swiss_citizen', 'none', 'other'
                    )),
    experience_years INTEGER DEFAULT 0,
    bio             TEXT,
    languages       JSONB DEFAULT '[]',
    -- Format: [{"lang": "de", "level": "B2"}, {"lang": "fr", "level": "A1"}]
    skills          JSONB DEFAULT '[]',
    -- Format: ["spawanie", "hydraulika", "SAP"]
    desired_salary_min  INTEGER,  -- CHF miesięcznie
    desired_salary_max  INTEGER,
    available_from  DATE,
    industry        VARCHAR(100),
    active_cv_id    UUID REFERENCES cv_files(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_worker_profiles_canton ON worker_profiles(canton);
CREATE INDEX idx_worker_profiles_work_permit ON worker_profiles(work_permit);
```

**Uwagi:**
- `languages` jako JSONB - elastyczne, bez dodatkowej tabeli many-to-many
- `active_cv_id` - wskazuje na aktualnie aktywne CV
- `canton` - kanton zamieszkania (do matchingu)

---

#### `employer_profiles`
```sql
CREATE TABLE employer_profiles (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID UNIQUE NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    company_name    VARCHAR(255) NOT NULL,
    company_slug    VARCHAR(255) UNIQUE NOT NULL,
    description     TEXT,
    logo_url        VARCHAR(500),
    website         VARCHAR(500),
    industry        VARCHAR(100),
    canton          VARCHAR(50),
    city            VARCHAR(100),
    address         VARCHAR(255),
    uid_number      VARCHAR(20),  -- Swiss UID (CHE-xxx.xxx.xxx)
    company_size    VARCHAR(20) CHECK (company_size IN (
                        '1-10', '11-50', '51-200', '201-500', '500+'
                    )),
    is_verified     BOOLEAN DEFAULT false,  -- Admin może zweryfikować firmę
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_employer_profiles_slug ON employer_profiles(company_slug);
CREATE INDEX idx_employer_profiles_canton ON employer_profiles(canton);
```

**Uwagi:**
- `company_slug` - do czytelnych URL: /firmy/swiss-clean-gmbh
- `uid_number` - unikalny identyfikator firmy w CH, opcjonalny ale przydatny do weryfikacji
- `is_verified` - weryfikacja przez admina (badge na profilu)

---

#### `categories`
```sql
CREATE TABLE categories (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            VARCHAR(100) NOT NULL,
    slug            VARCHAR(100) UNIQUE NOT NULL,
    parent_id       UUID REFERENCES categories(id) ON DELETE SET NULL,
    icon            VARCHAR(50),  -- np. nazwa ikony z Lucide
    sort_order      INTEGER DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_categories_parent ON categories(parent_id);
CREATE INDEX idx_categories_slug ON categories(slug);
```

**Przykładowe kategorie:**
- Budownictwo i remonty
- Gastronomia i hotelarstwo
- Opieka i pielęgniarstwo
- Transport i logistyka
- IT i technologia
- Sprzątanie i utrzymanie
- Produkcja i przemysł
- Handel i sprzedaż
- Finanse i księgowość
- Administracja i biuro
- Rolnictwo i ogrodnictwo
- Inne

---

#### `job_offers`
```sql
CREATE TABLE job_offers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employer_id     UUID NOT NULL REFERENCES employer_profiles(id) ON DELETE CASCADE,
    category_id     UUID REFERENCES categories(id) ON DELETE SET NULL,
    title           VARCHAR(255) NOT NULL,
    description     TEXT NOT NULL,
    canton          VARCHAR(50) NOT NULL,
    city            VARCHAR(100),
    contract_type   VARCHAR(30) NOT NULL CHECK (contract_type IN (
                        'full_time', 'part_time', 'temporary', 'contract',
                        'internship', 'freelance'
                    )),
    salary_min      INTEGER,   -- CHF miesięcznie (lub rocznie - pole salary_type)
    salary_max      INTEGER,
    salary_type     VARCHAR(20) DEFAULT 'monthly' CHECK (salary_type IN (
                        'monthly', 'yearly', 'hourly', 'negotiable'
                    )),
    salary_currency VARCHAR(3) DEFAULT 'CHF',
    experience_min  INTEGER DEFAULT 0,  -- lata
    work_permit_required VARCHAR(20),  -- null = dowolne
    work_permit_sponsored BOOLEAN DEFAULT false,
    is_remote       VARCHAR(20) DEFAULT 'no' CHECK (is_remote IN (
                        'no', 'yes', 'hybrid'
                    )),
    languages_required JSONB DEFAULT '[]',
    -- Format: [{"lang": "de", "level": "B1"}, {"lang": "en", "level": "A2"}]
    contact_email   VARCHAR(255),
    apply_via       VARCHAR(20) DEFAULT 'portal' CHECK (apply_via IN (
                        'portal', 'email', 'external_url'
                    )),
    external_url    VARCHAR(500),
    status          VARCHAR(20) DEFAULT 'pending' CHECK (status IN (
                        'draft', 'pending', 'active', 'rejected', 'expired', 'closed'
                    )),
    rejection_reason TEXT,
    views_count     INTEGER DEFAULT 0,
    is_featured     BOOLEAN DEFAULT false,  -- dla przyszłej monetyzacji
    feature_priority INTEGER DEFAULT 0,     -- wyższy = wyżej w wynikach
    published_at    TIMESTAMPTZ,
    expires_at      TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Indeksy krytyczne dla wyszukiwarki
CREATE INDEX idx_job_offers_status ON job_offers(status);
CREATE INDEX idx_job_offers_canton ON job_offers(canton);
CREATE INDEX idx_job_offers_category ON job_offers(category_id);
CREATE INDEX idx_job_offers_contract ON job_offers(contract_type);
CREATE INDEX idx_job_offers_employer ON job_offers(employer_id);
CREATE INDEX idx_job_offers_expires ON job_offers(expires_at);
CREATE INDEX idx_job_offers_featured ON job_offers(is_featured, feature_priority DESC);
CREATE INDEX idx_job_offers_published ON job_offers(published_at DESC);

-- Indeks pełnotekstowy (PostgreSQL)
CREATE INDEX idx_job_offers_search ON job_offers
    USING GIN (to_tsvector('polish', title || ' ' || description));
```

**Uwagi:**
- `status` flow: `draft` -> `pending` -> `active`/`rejected` -> `expired`/`closed`
- `is_featured` + `feature_priority` - gotowe pod przyszłe płatne wyróżnianie
- `apply_via` - elastyczność: przez portal, email lub link zewnętrzny
- Pełnotekstowy indeks GIN z konfiguracją `polish` - natywne wyszukiwanie po polsku
- `views_count` - inkrementowany asynchronicznie (nie blokuje zapytań)

---

#### `applications`
```sql
CREATE TABLE applications (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_offer_id    UUID NOT NULL REFERENCES job_offers(id) ON DELETE CASCADE,
    worker_id       UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    cv_file_id      UUID REFERENCES cv_files(id) ON DELETE SET NULL,
    cover_letter    TEXT,
    status          VARCHAR(20) DEFAULT 'sent' CHECK (status IN (
                        'sent', 'viewed', 'shortlisted', 'rejected', 'accepted'
                    )),
    employer_notes  TEXT,  -- notatki widoczne tylko dla pracodawcy
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(job_offer_id, worker_id)  -- jeden raz na ofertę
);

CREATE INDEX idx_applications_job ON applications(job_offer_id);
CREATE INDEX idx_applications_worker ON applications(worker_id);
CREATE INDEX idx_applications_status ON applications(status);
```

**Uwagi:**
- UNIQUE constraint - pracownik nie może aplikować dwa razy na tę samą ofertę
- `cv_file_id` - snapshot CV z momentu aplikacji (nie zmienia się gdy worker zaktualizuje CV)
- `employer_notes` - prywatne notatki pracodawcy o kandydacie

---

#### `cv_files`
```sql
CREATE TABLE cv_files (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    original_filename VARCHAR(255) NOT NULL,
    stored_filename VARCHAR(255) NOT NULL,  -- UUID-based, unikalna
    file_path       VARCHAR(500) NOT NULL,
    file_size       INTEGER NOT NULL,  -- bytes
    mime_type       VARCHAR(50) NOT NULL,
    is_active       BOOLEAN DEFAULT true,  -- aktualnie używane CV
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_cv_files_user ON cv_files(user_id);
```

**Uwagi:**
- `stored_filename` - bezpieczna nazwa (UUID), nie oryginalna nazwa pliku
- Stare CV nie są usuwane natychmiast - mogą być przypisane do aplikacji
- `is_active` - oznacza aktualne CV użytkownika

---

#### `posting_quotas` (system limitów)
```sql
CREATE TABLE posting_quotas (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    employer_id     UUID UNIQUE NOT NULL REFERENCES employer_profiles(id) ON DELETE CASCADE,
    monthly_limit   INTEGER,     -- null = używaj globalnego domyślnego
    used_count      INTEGER DEFAULT 0,
    period_start    DATE NOT NULL,
    period_end      DATE NOT NULL,
    plan_type       VARCHAR(30) DEFAULT 'free' CHECK (plan_type IN (
                        'free', 'basic', 'premium', 'enterprise', 'unlimited'
                    )),
    custom_limit    INTEGER,     -- nadpisanie przez admina
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_posting_quotas_employer ON posting_quotas(employer_id);
CREATE INDEX idx_posting_quotas_period ON posting_quotas(period_end);
```

---

#### `system_settings`
```sql
CREATE TABLE system_settings (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key             VARCHAR(100) UNIQUE NOT NULL,
    value           TEXT NOT NULL,
    value_type      VARCHAR(20) DEFAULT 'string' CHECK (value_type IN (
                        'string', 'integer', 'boolean', 'json'
                    )),
    description     TEXT,
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_by      UUID REFERENCES users(id)
);
```

**Domyślne ustawienia:**
| Key | Value | Typ | Opis |
|-----|-------|-----|------|
| `default_monthly_posting_limit` | `5` | integer | Domyślny limit ogłoszeń/miesiąc |
| `job_expiry_days` | `30` | integer | Domyślny czas wygaśnięcia oferty |
| `max_job_expiry_days` | `60` | integer | Maksymalny czas wygaśnięcia |
| `max_cv_size_mb` | `5` | integer | Max rozmiar CV |
| `require_moderation` | `true` | boolean | Czy ogłoszenia wymagają moderacji |
| `registration_enabled` | `true` | boolean | Czy rejestracja jest otwarta |
| `maintenance_mode` | `false` | boolean | Tryb konserwacji |

---

#### `audit_log`
```sql
CREATE TABLE audit_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    action          VARCHAR(100) NOT NULL,
    entity_type     VARCHAR(50),   -- 'job_offer', 'user', 'setting'
    entity_id       UUID,
    details         JSONB,
    ip_address      INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_audit_log_user ON audit_log(user_id);
CREATE INDEX idx_audit_log_action ON audit_log(action);
CREATE INDEX idx_audit_log_created ON audit_log(created_at DESC);
```

---

## 5. API - Endpointy backendowe

### Konwencje
- Prefix: `/api/v1/`
- Autoryzacja: Bearer JWT token w nagłówku `Authorization`
- Paginacja: `?page=1&per_page=20`
- Sortowanie: `?sort_by=created_at&sort_order=desc`
- Format odpowiedzi: JSON z wrapperem `{"data": ..., "meta": {"total": N, "page": 1, "per_page": 20}}`

### 5.1 Autoryzacja (`/api/v1/auth/`)

| Metoda | Endpoint | Opis | Auth |
|--------|----------|------|------|
| POST | `/register` | Rejestracja (worker lub employer) | Nie |
| POST | `/login` | Logowanie, zwraca access + refresh token | Nie |
| POST | `/refresh` | Odświeżenie access tokena | Refresh token |
| POST | `/logout` | Unieważnienie refresh tokena | Tak |
| POST | `/forgot-password` | Wysłanie emaila z linkiem reset | Nie |
| POST | `/reset-password` | Reset hasła z tokenem | Nie |
| GET | `/verify-email/{token}` | Weryfikacja email | Nie |
| GET | `/me` | Dane zalogowanego użytkownika | Tak |

**Szczegóły JWT:**
- Access token: ważny 15 minut, podpisany HS256
- Refresh token: ważny 7 dni, przechowywany w httpOnly cookie + DB
- Payload: `{sub: user_id, role: "worker"|"employer"|"admin", exp: timestamp}`
- Blacklista tokenów w Redis (dla logout)

### 5.2 Oferty pracy - publiczne (`/api/v1/jobs/`)

| Metoda | Endpoint | Opis | Auth |
|--------|----------|------|------|
| GET | `/` | Lista ofert (aktywnych) z filtrami | Nie |
| GET | `/{id}` | Szczegóły oferty | Nie |
| GET | `/categories` | Lista kategorii | Nie |
| GET | `/cantons` | Lista kantonów | Nie |
| GET | `/stats` | Statystyki publiczne (ile ofert, ile firm) | Nie |

**Query params dla `GET /jobs`:**
```
?q=spawacz                    # szukaj w tytule i opisie
&canton=zurich,bern           # filtr kanton (multi)
&category=budownictwo         # filtr kategoria
&contract_type=full_time      # filtr typ umowy
&salary_min=4000              # minimalne wynagrodzenie
&salary_max=8000              # maksymalne wynagrodzenie
&language=de                  # wymagany język
&is_remote=hybrid             # praca zdalna
&work_permit_sponsored=true   # sponsorowanie pozwolenia
&sort_by=published_at         # sortowanie
&sort_order=desc              # kierunek
&page=1&per_page=20           # paginacja
```

### 5.3 Pracownik (`/api/v1/worker/`)

| Metoda | Endpoint | Opis | Auth |
|--------|----------|------|------|
| GET | `/profile` | Mój profil | Worker |
| PUT | `/profile` | Aktualizacja profilu | Worker |
| POST | `/cv` | Upload CV (PDF) | Worker |
| GET | `/cv` | Pobranie mojego CV | Worker |
| DELETE | `/cv` | Usunięcie CV | Worker |
| POST | `/jobs/{id}/apply` | Aplikuj na ofertę | Worker |
| GET | `/applications` | Moje aplikacje | Worker |
| GET | `/applications/{id}` | Szczegóły aplikacji | Worker |
| DELETE | `/account` | Usunięcie konta (RODO) | Worker |

### 5.4 Pracodawca (`/api/v1/employer/`)

| Metoda | Endpoint | Opis | Auth |
|--------|----------|------|------|
| GET | `/profile` | Profil firmy | Employer |
| PUT | `/profile` | Aktualizacja profilu | Employer |
| POST | `/profile/logo` | Upload logo | Employer |
| GET | `/dashboard` | Statystyki | Employer |
| GET | `/jobs` | Moje ogłoszenia | Employer |
| POST | `/jobs` | Dodaj ogłoszenie | Employer |
| PUT | `/jobs/{id}` | Edytuj ogłoszenie | Employer |
| DELETE | `/jobs/{id}` | Usuń ogłoszenie | Employer |
| PATCH | `/jobs/{id}/close` | Zamknij ogłoszenie | Employer |
| GET | `/jobs/{id}/applications` | Kandydaci | Employer |
| PUT | `/applications/{id}/status` | Zmień status aplikacji | Employer |
| GET | `/applications/{id}/cv` | Pobierz CV kandydata | Employer |
| GET | `/quota` | Informacja o limicie | Employer |

### 5.5 Firmy - publiczne (`/api/v1/companies/`)

| Metoda | Endpoint | Opis | Auth |
|--------|----------|------|------|
| GET | `/{slug}` | Publiczny profil firmy | Nie |
| GET | `/{slug}/jobs` | Aktywne oferty firmy | Nie |

### 5.6 Admin (`/api/v1/admin/`)

| Metoda | Endpoint | Opis | Auth |
|--------|----------|------|------|
| GET | `/dashboard` | Statystyki ogólne | Admin |
| GET | `/jobs` | Wszystkie ogłoszenia (filtrowanie po statusie) | Admin |
| PUT | `/jobs/{id}/approve` | Zatwierdź ogłoszenie | Admin |
| PUT | `/jobs/{id}/reject` | Odrzuć ogłoszenie | Admin |
| GET | `/users` | Lista użytkowników | Admin |
| GET | `/users/{id}` | Szczegóły użytkownika | Admin |
| PUT | `/users/{id}/status` | Aktywuj / zbanuj | Admin |
| PUT | `/users/{id}/role` | Zmień rolę | Admin |
| GET | `/categories` | Kategorie | Admin |
| POST | `/categories` | Dodaj kategorię | Admin |
| PUT | `/categories/{id}` | Edytuj kategorię | Admin |
| DELETE | `/categories/{id}` | Usuń kategorię | Admin |
| PUT | `/categories/reorder` | Zmień kolejność | Admin |
| GET | `/settings` | Ustawienia systemowe | Admin |
| PUT | `/settings` | Zmień ustawienia | Admin |
| PUT | `/employers/{id}/quota` | Nadpisz limit pracodawcy | Admin |
| GET | `/audit-log` | Logi audytu | Admin |

---

## 6. System limitów ogłoszeń

### 6.1 Zasada działania

```
┌─────────────────────────────────────────────────────────────┐
│                    FLOW DODAWANIA OGŁOSZENIA                │
│                                                             │
│  Pracodawca klika "Dodaj"                                   │
│       │                                                     │
│       ▼                                                     │
│  Sprawdź posting_quotas dla employer_id                     │
│       │                                                     │
│       ├── Brak rekordu? → Utwórz z globalnym limitem        │
│       │                                                     │
│       ▼                                                     │
│  Oblicz efektywny limit:                                    │
│    1. custom_limit (nadpisanie admina) → najwyższy priorytet│
│    2. monthly_limit (z planu) → drugi priorytet             │
│    3. system_settings.default_monthly_posting_limit → domyślny│
│       │                                                     │
│       ▼                                                     │
│  used_count < efektywny_limit?                              │
│       │                                                     │
│       ├── TAK → Pozwól dodać, used_count += 1               │
│       │                                                     │
│       └── NIE → Pokaż komunikat o wyczerpaniu limitu        │
│              → Pokaż datę resetu                            │
│              → (przyszłość) Zaproponuj upgrade planu        │
└─────────────────────────────────────────────────────────────┘
```

### 6.2 Hierarchia limitów (priorytet)

1. **custom_limit** (admin nadpisał ręcznie) - np. dał 20 dla VIP klienta
2. **monthly_limit** z `posting_quotas` (wynikający z planu) - np. basic = 10
3. **default_monthly_posting_limit** z `system_settings` - globalny domyślny, np. 5

Kod pseudologiczny:
```
def get_effective_limit(employer_id):
    quota = db.get(PostingQuota, employer_id)
    if quota and quota.custom_limit is not None:
        return quota.custom_limit
    if quota and quota.monthly_limit is not None:
        return quota.monthly_limit
    return db.get(SystemSetting, 'default_monthly_posting_limit').value
```

### 6.3 Reset miesięczny

**Mechanizm:** Celery Beat (scheduler) + task

```
# Uruchamiany codziennie o 00:05 UTC
@celery.task
def reset_expired_quotas():
    today = date.today()
    expired = PostingQuota.filter(period_end <= today)
    for quota in expired:
        quota.used_count = 0
        quota.period_start = today
        quota.period_end = today + timedelta(days=30)
        quota.save()
```

**Alternatywa bez Celery (prostsze MVP):** APScheduler wbudowany w FastAPI

```python
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

@scheduler.scheduled_job('cron', hour=0, minute=5)
async def reset_quotas():
    async with get_db() as db:
        await db.execute(
            update(PostingQuota)
            .where(PostingQuota.period_end <= date.today())
            .values(used_count=0, period_start=date.today(),
                    period_end=date.today() + timedelta(days=30))
        )
```

**Rekomendacja dla MVP:** APScheduler (prostsze, nie wymaga Redis dla schedulera). Migracja na Celery Beat w Fazie 2.

### 6.4 Endpoint informacyjny dla pracodawcy

`GET /api/v1/employer/quota` zwraca:
```json
{
    "plan_type": "free",
    "monthly_limit": 5,
    "used_count": 3,
    "remaining": 2,
    "period_start": "2026-02-01",
    "period_end": "2026-03-02",
    "days_until_reset": 18,
    "has_custom_limit": false
}
```

### 6.5 Przygotowanie pod płatne plany

Tabela `posting_quotas` już zawiera pole `plan_type`. W przyszłości:

```
┌──────────────┬────────┬──────────────┬──────────────┐
│ Plan         │ Limit  │ Wyróżnienie  │ Cena CHF/mies│
├──────────────┼────────┼──────────────┼──────────────┤
│ Free         │ 5      │ Nie          │ 0            │
│ Basic        │ 15     │ 1/mies       │ 49           │
│ Premium      │ 50     │ 5/mies       │ 149          │
│ Enterprise   │ ∞      │ ∞            │ 399          │
└──────────────┴────────┴──────────────┴──────────────┘
```

Do wdrożenia w przyszłości: tabela `subscription_plans` + integracja Stripe.

---

## 7. Struktura frontendu

### 7.1 Technologia

- **Next.js 14** (App Router) - SSR dla SEO, routing, optymalizacja
- **TypeScript** - bezpieczeństwo typów
- **Tailwind CSS** - utility-first, szybki development
- **shadcn/ui** - komponenty (Button, Input, Dialog, Select, Card, Table, Badge, etc.)
- **TanStack Query (React Query)** - data fetching, cache, invalidation
- **React Hook Form + Zod** - formularze z walidacją
- **Zustand** - globalny state (auth, UI)
- **Axios** - HTTP client z interceptorami (JWT refresh)
- **Lucide Icons** - ikony

### 7.2 Struktura projektu

```
frontend/
├── public/
│   ├── favicon.ico
│   ├── logo.svg
│   └── images/
│       ├── hero-bg.jpg
│       └── og-image.jpg
├── src/
│   ├── app/                          # Next.js App Router
│   │   ├── layout.tsx                # Root layout (Header, Footer)
│   │   ├── page.tsx                  # Strona główna
│   │   ├── loading.tsx               # Global loading
│   │   ├── not-found.tsx             # 404
│   │   ├── (auth)/                   # Grupa: auth (bez headera)
│   │   │   ├── login/page.tsx
│   │   │   ├── register/page.tsx
│   │   │   ├── register/worker/page.tsx
│   │   │   ├── register/employer/page.tsx
│   │   │   ├── forgot-password/page.tsx
│   │   │   └── reset-password/page.tsx
│   │   ├── oferty/                   # Publiczne oferty
│   │   │   ├── page.tsx              # Lista ofert
│   │   │   └── [id]/page.tsx         # Szczegóły oferty
│   │   ├── firmy/                    # Publiczne profile firm
│   │   │   └── [slug]/page.tsx       # Profil firmy
│   │   ├── panel/                    # Panele (auth required)
│   │   │   ├── layout.tsx            # Layout z sidebar
│   │   │   ├── pracownik/           # Panel pracownika
│   │   │   │   ├── page.tsx          # Dashboard
│   │   │   │   ├── profil/page.tsx   # Edycja profilu
│   │   │   │   ├── cv/page.tsx       # Upload CV
│   │   │   │   ├── aplikacje/page.tsx # Moje aplikacje
│   │   │   │   └── ustawienia/page.tsx
│   │   │   ├── pracodawca/          # Panel pracodawcy
│   │   │   │   ├── page.tsx          # Dashboard
│   │   │   │   ├── profil/page.tsx   # Profil firmy
│   │   │   │   ├── ogloszenia/page.tsx        # Moje ogłoszenia
│   │   │   │   ├── ogloszenia/nowe/page.tsx    # Dodaj ogłoszenie
│   │   │   │   ├── ogloszenia/[id]/page.tsx    # Edytuj ogłoszenie
│   │   │   │   ├── ogloszenia/[id]/kandydaci/page.tsx  # Lista kandydatów
│   │   │   │   └── ustawienia/page.tsx
│   │   │   └── admin/               # Panel admina
│   │   │       ├── page.tsx          # Dashboard
│   │   │       ├── moderacja/page.tsx # Moderacja ogłoszeń
│   │   │       ├── uzytkownicy/page.tsx
│   │   │       ├── kategorie/page.tsx
│   │   │       ├── ustawienia/page.tsx
│   │   │       └── logi/page.tsx
│   │   └── api/                      # Next.js API routes (proxy/BFF)
│   ├── components/
│   │   ├── ui/                       # shadcn/ui components
│   │   ├── layout/
│   │   │   ├── Header.tsx
│   │   │   ├── Footer.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MobileNav.tsx
│   │   │   └── UserMenu.tsx
│   │   ├── home/
│   │   │   ├── HeroSection.tsx
│   │   │   ├── SearchBar.tsx
│   │   │   ├── FeaturedJobs.tsx
│   │   │   ├── CategoryGrid.tsx
│   │   │   └── StatsSection.tsx
│   │   ├── jobs/
│   │   │   ├── JobCard.tsx
│   │   │   ├── JobList.tsx
│   │   │   ├── JobFilters.tsx
│   │   │   ├── JobFiltersMobile.tsx
│   │   │   ├── JobDetail.tsx
│   │   │   ├── JobApplyForm.tsx
│   │   │   ├── JobBadge.tsx
│   │   │   └── SalaryDisplay.tsx
│   │   ├── auth/
│   │   │   ├── LoginForm.tsx
│   │   │   ├── RegisterWorkerForm.tsx
│   │   │   ├── RegisterEmployerForm.tsx
│   │   │   └── AuthGuard.tsx
│   │   ├── worker/
│   │   │   ├── ProfileForm.tsx
│   │   │   ├── CVUpload.tsx
│   │   │   ├── ApplicationList.tsx
│   │   │   └── ApplicationCard.tsx
│   │   ├── employer/
│   │   │   ├── CompanyForm.tsx
│   │   │   ├── JobForm.tsx
│   │   │   ├── JobTable.tsx
│   │   │   ├── CandidateList.tsx
│   │   │   ├── CandidateCard.tsx
│   │   │   ├── QuotaIndicator.tsx
│   │   │   └── LogoUpload.tsx
│   │   ├── admin/
│   │   │   ├── StatsCards.tsx
│   │   │   ├── ModerationQueue.tsx
│   │   │   ├── UserTable.tsx
│   │   │   ├── CategoryManager.tsx
│   │   │   └── SettingsForm.tsx
│   │   └── common/
│   │       ├── Pagination.tsx
│   │       ├── EmptyState.tsx
│   │       ├── LoadingSpinner.tsx
│   │       ├── ConfirmDialog.tsx
│   │       ├── FileUpload.tsx
│   │       ├── RichTextEditor.tsx
│   │       ├── CantonSelect.tsx
│   │       ├── LanguageSelect.tsx
│   │       └── StatusBadge.tsx
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useJobs.ts
│   │   ├── useApplications.ts
│   │   ├── useEmployer.ts
│   │   ├── useAdmin.ts
│   │   ├── useDebounce.ts
│   │   └── useMediaQuery.ts
│   ├── services/
│   │   ├── api.ts                    # Axios instance + interceptors
│   │   ├── authService.ts
│   │   ├── jobService.ts
│   │   ├── workerService.ts
│   │   ├── employerService.ts
│   │   └── adminService.ts
│   ├── store/
│   │   ├── authStore.ts              # Zustand - auth state
│   │   └── uiStore.ts               # Zustand - UI state (sidebar, modals)
│   ├── types/
│   │   ├── auth.ts
│   │   ├── job.ts
│   │   ├── user.ts
│   │   ├── application.ts
│   │   └── api.ts                    # Generic API response types
│   ├── lib/
│   │   ├── utils.ts                  # cn() helper, formatters
│   │   ├── constants.ts              # Kantony, języki, typy umów
│   │   └── validations.ts           # Zod schemas
│   └── styles/
│       └── globals.css               # Tailwind + custom styles
├── tailwind.config.ts
├── tsconfig.json
├── next.config.js
└── package.json
```

### 7.3 Struktura backendu

```
backend/
├── alembic/                          # Migracje DB
│   ├── versions/
│   └── env.py
├── app/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app, middleware, startup
│   ├── config.py                     # Pydantic Settings (env vars)
│   ├── database.py                   # SQLAlchemy async engine + session
│   ├── dependencies.py               # Dependency injection (get_db, get_current_user)
│   ├── models/                       # SQLAlchemy models
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── worker_profile.py
│   │   ├── employer_profile.py
│   │   ├── job_offer.py
│   │   ├── application.py
│   │   ├── cv_file.py
│   │   ├── category.py
│   │   ├── posting_quota.py
│   │   ├── system_setting.py
│   │   └── audit_log.py
│   ├── schemas/                      # Pydantic schemas (request/response)
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── user.py
│   │   ├── job.py
│   │   ├── application.py
│   │   ├── employer.py
│   │   ├── worker.py
│   │   ├── admin.py
│   │   └── common.py                # PaginatedResponse, etc.
│   ├── routers/                      # API routers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   ├── jobs.py                   # Publiczne endpointy ofert
│   │   ├── worker.py
│   │   ├── employer.py
│   │   ├── companies.py              # Publiczne profile firm
│   │   └── admin.py
│   ├── services/                     # Business logic
│   │   ├── __init__.py
│   │   ├── auth_service.py
│   │   ├── job_service.py
│   │   ├── application_service.py
│   │   ├── quota_service.py
│   │   ├── file_service.py
│   │   ├── email_service.py
│   │   └── admin_service.py
│   ├── core/                         # Core utilities
│   │   ├── security.py               # JWT, hashing
│   │   ├── permissions.py            # Role-based guards
│   │   ├── exceptions.py             # Custom exceptions
│   │   └── sanitize.py               # HTML sanitization
│   ├── tasks/                        # Background tasks
│   │   ├── __init__.py
│   │   ├── scheduler.py              # APScheduler config
│   │   ├── quota_reset.py
│   │   └── job_expiry.py
│   └── utils/
│       ├── pagination.py
│       └── validators.py
├── uploads/                          # Local file storage (dev)
│   ├── cv/
│   └── logos/
├── tests/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_jobs.py
│   ├── test_worker.py
│   ├── test_employer.py
│   └── test_admin.py
├── alembic.ini
├── requirements.txt
├── .env
├── .env.example
├── Dockerfile
└── docker-compose.yml
```

---

## 8. UX i struktura stron

### 8.1 Strona główna

```
┌──────────────────────────────────────────────────────────────┐
│  [Logo PolacySzwajcaria]              [Oferty] [Zaloguj się] │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│              HERO SECTION (tło: Alpy / Szwajcaria)           │
│                                                              │
│         Znajdź wymarzoną pracę w Szwajcarii                  │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐  │
│  │ 🔍 Stanowisko, firma...  │ 📍 Kanton ▼ │ [Szukaj]    │  │
│  └────────────────────────────────────────────────────────┘  │
│                                                              │
│      Popularne: spawacz, kierowca, opiekun/ka, kelner/ka     │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  📊 450+ ofert pracy  │  🏢 120+ firm  │  👥 2000+ profili  │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  KATEGORIE (grid 3x4 na desktop, 2x kolumny mobile)         │
│                                                              │
│  [🔨 Budownictwo (45)]  [🍳 Gastronomia (32)]               │
│  [🏥 Opieka (28)]       [🚛 Transport (22)]                 │
│  [💻 IT (18)]           [🧹 Sprzątanie (35)]                │
│  ...                                                         │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  NAJNOWSZE OFERTY (6 kart)                                   │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Logo firmy   │  │ Logo firmy   │  │ Logo firmy   │       │
│  │ Tytuł        │  │ Tytuł        │  │ Tytuł        │       │
│  │ Firma        │  │ Firma        │  │ Firma        │       │
│  │ Zürich       │  │ Bern         │  │ Basel        │       │
│  │ 5500 CHF     │  │ Do uzgodn.   │  │ 4800 CHF     │       │
│  │ [Pełny etat] │  │ [Tymczasowa] │  │ [Część etatu]│       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│                                                              │
│                   [Zobacz wszystkie oferty →]                │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  DLA PRACODAWCÓW                                             │
│  Szukasz polskojęzycznych pracowników?                       │
│  [Dodaj ogłoszenie za darmo]   [Dowiedz się więcej]          │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  FOOTER                                                      │
│  PolacySzwajcaria © 2026 │ O nas │ Kontakt │ Regulamin      │
│  Polityka prywatności │ Dla pracodawców                       │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 8.2 Lista ofert (`/oferty`)

```
┌──────────────────────────────────────────────────────────────┐
│  [Header]                                                    │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Oferty pracy (342 wyników)                                  │
│                                                              │
│  ┌──────────────┬───────────────────────────────────────┐    │
│  │  FILTRY      │  WYNIKI                               │    │
│  │  (sidebar)   │                                       │    │
│  │              │  [Sortuj: Najnowsze ▼]                │    │
│  │  Kanton ▼    │                                       │    │
│  │  □ Zürich    │  ┌─────────────────────────────────┐  │    │
│  │  □ Bern      │  │ ★ WYRÓŻNIONE                    │  │    │
│  │  □ Basel     │  │ [Logo] Spawacz MIG/MAG          │  │    │
│  │  □ ...       │  │ SwissBau AG · Zürich            │  │    │
│  │              │  │ 6000-7000 CHF · Pełny etat      │  │    │
│  │  Branża ▼    │  │ Dodano 2 godz. temu             │  │    │
│  │  □ Budow.    │  └─────────────────────────────────┘  │    │
│  │  □ Gastr.    │                                       │    │
│  │  □ IT        │  ┌─────────────────────────────────┐  │    │
│  │              │  │ [Logo] Kierowca kat. C           │  │    │
│  │  Umowa ▼     │  │ TransLog GmbH · Bern            │  │    │
│  │  □ Pełny     │  │ 5500 CHF · Pełny etat           │  │    │
│  │  □ Część     │  │ Dodano wczoraj                   │  │    │
│  │  □ Tymcz.    │  └─────────────────────────────────┘  │    │
│  │              │                                       │    │
│  │  Wynagrodz.  │  ┌─────────────────────────────────┐  │    │
│  │  [4000]–     │  │ ...kolejne oferty...             │  │    │
│  │  [8000] CHF  │  └─────────────────────────────────┘  │    │
│  │              │                                       │    │
│  │  Język ▼     │  [1] [2] [3] ... [17]  Następna →    │    │
│  │  □ Niemiecki │                                       │    │
│  │  □ Francuski │                                       │    │
│  │  □ Angielski │                                       │    │
│  │              │                                       │    │
│  │  Zdalna ▼    │                                       │    │
│  │  □ Tak       │                                       │    │
│  │  □ Hybrid    │                                       │    │
│  │              │                                       │    │
│  │ [Wyczyść     │                                       │    │
│  │  filtry]     │                                       │    │
│  └──────────────┴───────────────────────────────────────┘    │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

**Mobile:** Filtry w wysuwającym się panelu (Sheet z shadcn/ui), przycisk "Filtry (3)" nad listą.

### 8.3 Szczegóły oferty (`/oferty/{id}`)

```
┌──────────────────────────────────────────────────────────────┐
│  ← Powrót do wyników                                        │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────────────────────────────┬─────────────┐  │
│  │  GŁÓWNA TREŚĆ                           │  SIDEBAR     │  │
│  │                                          │              │  │
│  │  [Logo] SwissBau AG                      │  ┌────────┐  │  │
│  │                                          │  │APLIKUJ │  │  │
│  │  Spawacz MIG/MAG                         │  └────────┘  │  │
│  │                                          │              │  │
│  │  📍 Zürich │ 💼 Pełny etat │ 🕐 2h temu │  Wynagrodzenie│  │
│  │                                          │  6000-7000   │  │
│  │  ──────────────────────────              │  CHF/mies.   │  │
│  │                                          │              │  │
│  │  Opis stanowiska                         │  Typ umowy   │  │
│  │  Lorem ipsum dolor sit amet...           │  Pełny etat  │  │
│  │                                          │              │  │
│  │  Wymagania                               │  Język       │  │
│  │  • 3 lata doświadczenia                  │  DE (B1)     │  │
│  │  • Certyfikat spawacza                   │              │  │
│  │  • Pozwolenie B lub C                    │  Pozwolenie  │  │
│  │                                          │  B lub C     │  │
│  │  Oferujemy                               │              │  │
│  │  • Zakwaterowanie                        │  Zdalna      │  │
│  │  • Dojazd zapewniony                     │  Nie         │  │
│  │  • Ubezpieczenie                         │              │  │
│  │                                          │  Wygasa      │  │
│  │                                          │  za 28 dni   │  │
│  │                                          │              │  │
│  │  ──────────────────────────              │  ──────────  │  │
│  │                                          │              │  │
│  │  O firmie                                │  Udostępnij  │  │
│  │  SwissBau AG to firma budowlana...       │  [📋] [📧]   │  │
│  │  [Zobacz profil firmy →]                 │              │  │
│  │                                          │              │  │
│  └──────────────────────────────────────────┴─────────────┘  │
│                                                              │
│  PODOBNE OFERTY (3 karty)                                    │
│  ┌──────┐  ┌──────┐  ┌──────┐                               │
│  └──────┘  └──────┘  └──────┘                               │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

### 8.4 Flow aplikowania

```
1. Gość widzi ofertę → klika "Aplikuj" → Redirect do logowania
   → Po logowaniu → Redirect z powrotem do oferty

2. Zalogowany pracownik → klika "Aplikuj" →
   Modal/formularz:
   ┌──────────────────────────────────────┐
   │  Aplikuj na: Spawacz MIG/MAG        │
   │                                      │
   │  CV: [moje_cv.pdf] ✓                │
   │  (lub: [Najpierw dodaj CV →])       │
   │                                      │
   │  List motywacyjny (opcjonalny):     │
   │  ┌──────────────────────────────┐   │
   │  │                              │   │
   │  │                              │   │
   │  └──────────────────────────────┘   │
   │                                      │
   │  [Anuluj]          [Wyślij aplikację]│
   └──────────────────────────────────────┘

3. Po wysłaniu → Komunikat sukcesu →
   "Twoja aplikacja została wysłana. Śledź status w panelu."
   → Link do "Moje aplikacje"

4. Jeśli już aplikował → Przycisk nieaktywny:
   "Już aplikowałeś na tę ofertę" + data
```

### 8.5 Panel pracownika

```
┌──────────────────────────────────────────────────────────────┐
│  [Header z menu użytkownika]                                 │
├───────────┬──────────────────────────────────────────────────┤
│ SIDEBAR   │  CONTENT                                         │
│           │                                                  │
│ Dashboard │  Witaj, Jan!                                     │
│ Profil    │                                                  │
│ Moje CV   │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ Aplikacje │  │ Wysłane  │ │ W trakcie│ │ Odrzucone│        │
│ Ustawienia│  │ 8        │ │ 3        │ │ 2        │        │
│           │  └──────────┘ └──────────┘ └──────────┘        │
│           │                                                  │
│           │  Ostatnie aplikacje:                             │
│           │  ┌──────────────────────────────────────────┐   │
│           │  │ Spawacz MIG/MAG · SwissBau AG            │   │
│           │  │ Status: Przeglądane 👀  │ 2 dni temu     │   │
│           │  └──────────────────────────────────────────┘   │
│           │  ┌──────────────────────────────────────────┐   │
│           │  │ Kierowca kat. C · TransLog GmbH          │   │
│           │  │ Status: Wysłane 📩  │ 5 dni temu         │   │
│           │  └──────────────────────────────────────────┘   │
│           │                                                  │
└───────────┴──────────────────────────────────────────────────┘
```

### 8.6 Panel pracodawcy

```
┌───────────┬──────────────────────────────────────────────────┐
│ SIDEBAR   │  Dashboard                                       │
│           │                                                  │
│ Dashboard │  ┌──────────┐ ┌──────────┐ ┌──────────┐        │
│ Ogłoszenia│  │ Aktywne  │ │ Nowe     │ │ Limit    │        │
│ + Dodaj   │  │ 3        │ │ kandydaci│ │ 3/5      │        │
│ Profil    │  │ oferty   │ │ 12       │ │ tego mies│        │
│ Ustawienia│  └──────────┘ └──────────┘ └──────────┘        │
│           │                                                  │
│           │  Twoje ogłoszenia:                               │
│           │  ┌──────────────────────────────────────────┐   │
│           │  │ Spawacz MIG/MAG                          │   │
│           │  │ ● Aktywne │ 👥 8 kandydatów │ 👁 245     │   │
│           │  │ Wygasa: 28.03.2026  [Edytuj] [Zamknij]   │   │
│           │  └──────────────────────────────────────────┘   │
│           │                                                  │
│           │  ⚠️ Limit: Wykorzystano 3 z 5 ogłoszeń.         │
│           │  Reset: 2 marca 2026.                           │
│           │                                                  │
└───────────┴──────────────────────────────────────────────────┘
```

---

## 9. Wyszukiwarka

### 9.1 Struktura filtrów

| Filtr | Typ UI | Wartości | Kolumna DB |
|-------|--------|----------|------------|
| Szukaj (q) | Input text | Dowolny tekst | full-text search (title + description) |
| Kanton | Multi-select checkbox | 26 kantonów CH | `canton` |
| Branża | Single select / multi-checkbox | Z tabeli `categories` | `category_id` |
| Typ umowy | Multi-checkbox | Pełny etat, Część etatu, Tymczasowa, Zlecenie, Praktyka, Freelance | `contract_type` |
| Wynagrodzenie | Range slider / 2x input | 0 - 20000 CHF | `salary_min`, `salary_max` |
| Język | Multi-checkbox | DE, FR, IT, EN | `languages_required` (JSONB) |
| Praca zdalna | Checkbox group | Tak, Nie, Hybrydowo | `is_remote` |
| Pozwolenie sponsorowane | Toggle | Tak/Nie | `work_permit_sponsored` |

### 9.2 Query design w backendzie

```python
# services/job_service.py

async def search_jobs(
    db: AsyncSession,
    q: str | None = None,
    cantons: list[str] | None = None,
    category_id: UUID | None = None,
    contract_types: list[str] | None = None,
    salary_min: int | None = None,
    salary_max: int | None = None,
    languages: list[str] | None = None,
    is_remote: str | None = None,
    work_permit_sponsored: bool | None = None,
    sort_by: str = "published_at",
    sort_order: str = "desc",
    page: int = 1,
    per_page: int = 20,
) -> PaginatedResult:

    query = select(JobOffer).where(
        JobOffer.status == 'active',
        JobOffer.expires_at > func.now()
    )

    # Full-text search (PostgreSQL ts_vector)
    if q:
        search_query = func.plainto_tsquery('polish', q)
        query = query.where(
            func.to_tsvector('polish',
                JobOffer.title + ' ' + JobOffer.description
            ).match(search_query)
        )

    # Kanton (multi-select: OR)
    if cantons:
        query = query.where(JobOffer.canton.in_(cantons))

    # Kategoria
    if category_id:
        query = query.where(JobOffer.category_id == category_id)

    # Typ umowy (multi: OR)
    if contract_types:
        query = query.where(JobOffer.contract_type.in_(contract_types))

    # Wynagrodzenie (range overlap)
    if salary_min is not None:
        query = query.where(
            or_(
                JobOffer.salary_max >= salary_min,
                JobOffer.salary_max.is_(None)
            )
        )
    if salary_max is not None:
        query = query.where(
            or_(
                JobOffer.salary_min <= salary_max,
                JobOffer.salary_min.is_(None)
            )
        )

    # Język (JSONB contains)
    if languages:
        for lang in languages:
            query = query.where(
                JobOffer.languages_required.contains(
                    cast([{"lang": lang}], JSONB)
                )
            )

    # Praca zdalna
    if is_remote:
        query = query.where(JobOffer.is_remote == is_remote)

    # Sponsorowanie pozwolenia
    if work_permit_sponsored is not None:
        query = query.where(
            JobOffer.work_permit_sponsored == work_permit_sponsored
        )

    # Sortowanie: wyróżnione oferty zawsze na górze
    order_clauses = [JobOffer.is_featured.desc(), JobOffer.feature_priority.desc()]

    if sort_by == "published_at":
        order_clauses.append(
            JobOffer.published_at.desc() if sort_order == "desc"
            else JobOffer.published_at.asc()
        )
    elif sort_by == "salary":
        order_clauses.append(
            JobOffer.salary_max.desc().nullslast()
        )

    query = query.order_by(*order_clauses)

    # Paginacja
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    results = await db.execute(
        query.offset((page - 1) * per_page).limit(per_page)
    )

    return PaginatedResult(
        data=results.scalars().all(),
        total=total,
        page=page,
        per_page=per_page
    )
```

### 9.3 Optymalizacja zapytań

1. **Indeksy** (już zdefiniowane w sekcji DB):
   - GIN index na `to_tsvector('polish', title || ' ' || description)` - full-text search
   - B-tree na `status`, `canton`, `category_id`, `contract_type`, `expires_at`
   - Composite index: `(status, expires_at, published_at DESC)` - najczęstszy query

2. **Cache** (Redis):
   - Cache kategorii (rzadko się zmienia): TTL 1h
   - Cache listy kantonów: TTL 24h
   - Cache count per category na stronie głównej: TTL 5min
   - NIE cachujemy wyników wyszukiwania (zbyt wiele kombinacji filtrów)

3. **Paginacja**:
   - Offset-based (prostsze, wystarczające dla MVP)
   - Przyszłość: cursor-based dla lepszej wydajności przy dużych zbiorach

4. **Lazy loading filtrów**:
   - Kantony i kategorie ładowane raz, cache'owane w React Query (staleTime: 1h)
   - Counts per filter aktualizowane asynchronicznie

5. **Debounce wyszukiwarki**:
   - Input text z debounce 300ms (nie odpytujemy API przy każdym keystroke)

6. **URL state**:
   - Filtry zapisywane w URL query params (`/oferty?canton=zurich&q=spawacz`)
   - Pozwala na bookmark/share wyników wyszukiwania
   - React: `useSearchParams()` jako source of truth dla filtrów

---

## 10. Bezpieczeństwo i RODO

### 10.1 Uwierzytelnianie i autoryzacja

| Mechanizm | Implementacja |
|-----------|---------------|
| Haszowanie haseł | bcrypt (cost factor 12) |
| JWT Access Token | HS256, 15 min TTL |
| JWT Refresh Token | httpOnly cookie + DB record, 7 dni TTL |
| Token blacklist | Redis SET z TTL (dla logout) |
| Role-based access | Middleware sprawdzający `role` z JWT payload |
| Rate limiting | slowapi (FastAPI) - 5 login/min, 100 req/min ogólne |
| CORS | Whitelista origins (frontend domain) |
| CSRF | SameSite=Strict na cookies, custom header |

### 10.2 Ochrona API

```python
# Middleware stack w FastAPI

app.add_middleware(CORSMiddleware, allow_origins=["https://polacyszwajcaria.ch"])
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["polacyszwajcaria.ch", "api.polacyszwajcaria.ch"])

# Rate limiting per endpoint
@app.post("/api/v1/auth/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):

@app.post("/api/v1/employer/jobs")
@limiter.limit("10/hour")
async def create_job(request: Request, ...):

# Globalny limit
@limiter.limit("100/minute")
```

### 10.3 Ochrona przed spamem

| Zagrożenie | Rozwiązanie |
|-----------|-------------|
| Spam rejestracji | Weryfikacja email + rate limit (3 rejestracje/IP/h) |
| Spam ogłoszeń | Moderacja admina + limit ogłoszeń + rate limit |
| Spam aplikacji | 1 aplikacja na ofertę + rate limit (20 aplikacji/dzień) |
| Boty | Honeypot field w formularzach (MVP), reCAPTCHA v3 (Faza 2) |
| XSS | Sanityzacja HTML (bleach), Content-Security-Policy header |
| SQL Injection | SQLAlchemy ORM (parametryzowane zapytania) |
| File upload | Walidacja MIME type, max size, skan antywirusowy (przyszłość) |

### 10.4 Bezpieczeństwo plików (CV, logo)

```
Upload flow:
1. Walidacja po stronie frontendu (typ, rozmiar)
2. Backend sprawdza:
   - MIME type (magic bytes, nie tylko rozszerzenie)
   - Rozmiar (max 5MB CV, max 2MB logo)
   - Dozwolone typy: PDF (CV), JPG/PNG (logo)
3. Plik zapisywany z UUID jako nazwa (nie oryginalna)
4. Oryginalna nazwa w DB (do wyświetlania)
5. Pliki serwowane przez endpoint z autoryzacją (nie publiczny folder)
6. CV dostępne tylko dla: właściciel + pracodawcy do których aplikował + admin
```

**Przechowywanie:**
- MVP: lokalna dyskowa (folder `uploads/` poza public)
- Produkcja: S3-compatible storage (AWS S3 / MinIO / Cloudflare R2)
- Pliki NIGDY nie są serwowane bezpośrednio przez Nginx - zawsze przez API z auth

### 10.5 RODO (GDPR/nDSG)

Szwajcaria ma własną ustawę o ochronie danych (nDSG - New Federal Act on Data Protection), zbliżoną do GDPR.

| Wymóg | Implementacja |
|-------|---------------|
| Zgoda na przetwarzanie | Checkbox przy rejestracji + zapis zgody z timestampem |
| Prawo do informacji | Endpoint `GET /api/v1/worker/data-export` - export wszystkich danych jako JSON |
| Prawo do usunięcia | Endpoint `DELETE /api/v1/worker/account` - usunięcie konta i danych |
| Minimalizacja danych | Zbieramy tylko niezbędne dane, pola opcjonalne oznaczone |
| Polityka prywatności | Dedykowana strona `/polityka-prywatnosci` |
| Regulamin | Strona `/regulamin` |
| Cookies | Informacja o cookies (technicznie konieczne = bez zgody) |
| Przechowywanie CV | Szyfrowane at rest (AES-256), dostęp tylko autoryzowany |
| Retencja danych | Auto-usunięcie nieaktywnych kont po 24 miesiącach (z ostrzeżeniem email) |
| Logi | IP anonimizowane po 90 dniach |
| Breach notification | Procedura powiadomienia w 72h (GDPR) / jak najszybciej (nDSG) |

**Usunięcie konta - flow:**
1. Użytkownik klika "Usuń konto" → Potwierdzenie emailem
2. Konto oznaczone jako `is_active=false`, dane zanonimizowane
3. CV fizycznie usunięte z dysku
4. Aplikacje: dane osobowe usunięte, sama aplikacja zachowana jako "Użytkownik usunięty"
5. Po 30 dniach: pełne usunięcie z bazy

### 10.6 Nagłówki bezpieczeństwa

```python
# Middleware
@app.middleware("http")
async def security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'self'; ..."
    return response
```

---

## 11. Architektura techniczna

### 11.1 Architektura ogólna

```
┌─────────────────────────────────────────────────────────────────┐
│                         KLIENCI                                 │
│  [Browser Desktop]  [Browser Mobile]  [PWA - przyszłość]        │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTPS
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      NGINX (Reverse Proxy)                      │
│  - SSL termination (Let's Encrypt)                              │
│  - Static files (Next.js build)                                 │
│  - Gzip compression                                             │
│  - Rate limiting (dodatkowa warstwa)                            │
│  - /api/* → FastAPI backend                                     │
│  - /* → Next.js frontend                                        │
└───────────┬────────────────────────────────┬────────────────────┘
            │                                │
            ▼                                ▼
┌───────────────────────┐    ┌──────────────────────────────────┐
│   NEXT.JS FRONTEND    │    │        FASTAPI BACKEND           │
│                       │    │                                  │
│   - SSR/SSG pages     │    │  ┌─────────┐  ┌──────────────┐  │
│   - React components  │    │  │ Routers │→ │ Services     │  │
│   - TanStack Query    │    │  │ (API)   │  │ (Logic)      │  │
│   - Zustand store     │    │  └─────────┘  └──────┬───────┘  │
│                       │    │                       │          │
│   Port: 3000          │    │  ┌────────────────────▼───────┐  │
│                       │    │  │    SQLAlchemy 2.0 (async)  │  │
│                       │    │  └────────────────────┬───────┘  │
│                       │    │                       │          │
│                       │    │  Port: 8000           │          │
└───────────────────────┘    └───────────────────────┼──────────┘
                                                     │
                    ┌────────────────────────────────┼──────────┐
                    │                                │          │
                    ▼                                ▼          ▼
          ┌──────────────┐              ┌──────────────┐  ┌─────────┐
          │    REDIS      │              │ POSTGRESQL   │  │ STORAGE │
          │               │              │              │  │         │
          │ - JWT blacklist│              │ - Users      │  │ uploads/│
          │ - Cache       │              │ - Jobs       │  │ cv/     │
          │ - Rate limits │              │ - etc.       │  │ logos/  │
          │ - Sessions    │              │              │  │         │
          │               │              │ Port: 5432   │  │ (S3 w  │
          │ Port: 6379    │              │              │  │ prod)   │
          └──────────────┘              └──────────────┘  └─────────┘
                    ▲
                    │
          ┌──────────────┐
          │  SCHEDULER   │
          │              │
          │ APScheduler  │
          │ (wbudowany   │
          │  w FastAPI)  │
          │              │
          │ Taski:       │
          │ - quota reset│
          │ - job expiry │
          │ - cleanup    │
          └──────────────┘
```

### 11.2 Środowisko deweloperskie

```yaml
# docker-compose.yml
services:
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_DB: polacyszwajcaria
      POSTGRES_USER: psz_user
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    environment:
      - DATABASE_URL=postgresql+asyncpg://psz_user:${DB_PASSWORD}@db:5432/polacyszwajcaria
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET=${JWT_SECRET}
      - UPLOAD_DIR=/app/uploads
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
      - uploads:/app/uploads
    depends_on:
      - db
      - redis

  frontend:
    build: ./frontend
    command: npm run dev
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
    ports:
      - "3000:3000"
    volumes:
      - ./frontend:/app
      - /app/node_modules

volumes:
  pgdata:
  uploads:
```

### 11.3 Konfiguracja (`.env`)

```env
# Database
DATABASE_URL=postgresql+asyncpg://psz_user:password@localhost:5432/polacyszwajcaria

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET=super-secret-key-change-in-production
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# Upload
UPLOAD_DIR=./uploads
MAX_CV_SIZE_MB=5
MAX_LOGO_SIZE_MB=2

# Email (SMTP)
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=noreply@polacyszwajcaria.ch
SMTP_PASSWORD=xxx
SMTP_FROM=PolacySzwajcaria <noreply@polacyszwajcaria.ch>

# Frontend
FRONTEND_URL=http://localhost:3000

# Admin
FIRST_ADMIN_EMAIL=admin@polacyszwajcaria.ch
FIRST_ADMIN_PASSWORD=change-me-on-first-login
```

### 11.4 Background tasks

| Task | Częstotliwość | Opis |
|------|--------------|------|
| `reset_expired_quotas` | Codziennie 00:05 | Reset limitów ogłoszeń po upłynięciu 30 dni |
| `expire_old_jobs` | Codziennie 01:00 | Zmiana statusu na `expired` dla ofert po `expires_at` |
| `cleanup_unverified_accounts` | Tygodniowo | Usunięcie niezweryfikowanych kont starszych niż 7 dni |
| `cleanup_orphan_files` | Tygodniowo | Usunięcie plików CV/logo bez powiązania w DB |
| `anonymize_old_logs` | Miesięcznie | Anonimizacja IP w audit_log starszych niż 90 dni |

### 11.5 Wysyłka emaili

| Event | Email | Odbiorca |
|-------|-------|----------|
| Rejestracja | Weryfikacja email | Użytkownik |
| Reset hasła | Link do resetu | Użytkownik |
| Nowa aplikacja | Powiadomienie | Pracodawca |
| Zmiana statusu aplikacji | Powiadomienie | Pracownik |
| Ogłoszenie zatwierdzone | Powiadomienie | Pracodawca |
| Ogłoszenie odrzucone | Powiadomienie + powód | Pracodawca |
| Ogłoszenie wygasa za 3 dni | Przypomnienie | Pracodawca |
| Limit wyczerpany | Informacja | Pracodawca |

**Implementacja MVP:** SMTP (np. Gmail SMTP lub SendGrid free tier)
**Produkcja:** Dedykowany serwis (SendGrid / AWS SES / Postmark)

---

## 12. Roadmapa

### Faza 1 - MVP (4-6 tygodni)

**Tydzień 1-2: Fundamenty**
- [ ] Setup projektu (Docker, FastAPI, Next.js, PostgreSQL)
- [ ] Modele bazy danych + migracje Alembic
- [ ] System autoryzacji (rejestracja, logowanie, JWT, refresh)
- [ ] Weryfikacja email
- [ ] Podstawowy layout (Header, Footer, responsywny)
- [ ] Strona logowania / rejestracji

**Tydzień 2-3: Pracownik**
- [ ] Profil pracownika (CRUD)
- [ ] Upload CV (PDF)
- [ ] Panel pracownika (dashboard)
- [ ] Aplikowanie na oferty
- [ ] Lista "Moje aplikacje" ze statusami

**Tydzień 3-4: Pracodawca**
- [ ] Profil firmy (CRUD + logo)
- [ ] Dodawanie ogłoszeń (formularz + walidacja)
- [ ] Lista moich ogłoszeń
- [ ] System limitów ogłoszeń
- [ ] Lista kandydatów na ofertę
- [ ] Zmiana statusu aplikacji

**Tydzień 4-5: Publiczne + wyszukiwarka**
- [ ] Strona główna (hero, kategorie, najnowsze oferty)
- [ ] Lista ofert z filtrami (kanton, branża, umowa, wynagrodzenie, język)
- [ ] Full-text search (PostgreSQL)
- [ ] Strona szczegółów oferty
- [ ] Publiczny profil firmy
- [ ] Paginacja, sortowanie

**Tydzień 5-6: Admin + deploy**
- [ ] Panel admina (moderacja ogłoszeń, zarządzanie użytkownikami)
- [ ] Ustawienia systemowe (limity)
- [ ] Zarządzanie kategoriami
- [ ] Background tasks (quota reset, job expiry)
- [ ] Testy (unit + integration, min 70% coverage)
- [ ] Deploy na VPS / cloud (Docker Compose + Nginx)
- [ ] Domena + SSL

**Deliverable:** Działający portal z pełnym flow: rejestracja → dodanie oferty → moderacja → publikacja → aplikowanie → zarządzanie kandydatami.

---

### Faza 2 - Ulepszenia (4-6 tygodni po MVP)

- [ ] Powiadomienia email (aplikacja, zmiana statusu, wygaśnięcie)
- [ ] Wyszukiwarka: auto-suggest, popularne frazy
- [ ] Zapisane wyszukiwania / alerty email ("powiadom mnie o nowych ofertach spawacza w Zürichu")
- [ ] Ulubione oferty (pracownik może zapisać na liście)
- [ ] Rich text editor do opisów ogłoszeń
- [ ] Widok mobilny - pełna optymalizacja
- [ ] reCAPTCHA v3 (anti-spam)
- [ ] Statystyki pracodawcy (wyświetlenia, konwersja aplikacji)
- [ ] Statystyki admina (wykresy, trendy)
- [ ] SEO: meta tagi, structured data (JobPosting schema.org), sitemap
- [ ] Migracja z APScheduler na Celery + Redis (skalowalność)
- [ ] S3 dla plików (migracja z lokalnego storage)
- [ ] Monitoring (Sentry, health checks)
- [ ] CI/CD pipeline (GitHub Actions: lint + test + deploy)

---

### Faza 3 - Skalowanie (2-3 miesiące)

- [ ] PWA (Progressive Web App) - instalacja na telefonie
- [ ] Push notifications (nowe oferty, zmiana statusu)
- [ ] Elasticsearch / Meilisearch (zastąpienie PostgreSQL full-text dla lepszych wyników)
- [ ] CDN (Cloudflare) dla static assets
- [ ] Horizontal scaling: load balancer + multiple API instances
- [ ] Database read replicas
- [ ] Profilowanie wydajności, cache strategy
- [ ] A/B testing framework
- [ ] Analytics (Plausible / Matomo - privacy-friendly, RODO)
- [ ] Wielojęzyczność UI (PL + DE + FR - opcjonalnie)
- [ ] API publiczne (dla partnerów - z API keys)

---

### Faza 4 - Monetyzacja (3-6 miesięcy po MVP)

- [ ] System subskrypcji (Stripe integration)
- [ ] Płatne plany: Basic / Premium / Enterprise
- [ ] Wyróżnione ogłoszenia (featured - wyżej w wynikach, badge)
- [ ] Promowane ogłoszenia (banner na stronie głównej)
- [ ] AI matching kandydatów (rekomendacje ofert dla pracowników)
- [ ] CV parsing (automatyczne wyciąganie danych z PDF)
- [ ] Profil firmowy premium (zdjęcia, video, opis kultury)
- [ ] Statystyki zaawansowane dla pracodawców (benchmark rynkowy)
- [ ] Raporty rynku pracy (content marketing + wartość dodana)
- [ ] Newsletter z ofertami (personalizowany)
- [ ] Integracja z LinkedIn / Xing (import profilu)

---

## 13. Przyszła monetyzacja

### 13.1 Architektura gotowa na monetyzację

System jest projektowany tak, by dodanie płatności wymagało minimum zmian:

```
TERAZ (MVP):
┌──────────────────┐
│ posting_quotas   │
│ plan_type: 'free'│ ← jedyny plan, limit z system_settings
│ monthly_limit: 5 │
└──────────────────┘

PRZYSZŁOŚĆ:
┌──────────────────┐     ┌──────────────────────────────┐
│ posting_quotas   │     │ subscription_plans (nowa)     │
│ plan_type: FK ──────→  │ id, name, monthly_limit,     │
│                  │     │ featured_count, price_chf,    │
│                  │     │ stripe_price_id, features     │
└──────────────────┘     └──────────────────────────────┘
                               │
┌──────────────────┐           │
│ subscriptions    │           │
│ (nowa tabela)    │           │
│ employer_id      │           │
│ plan_id ─────────────────────┘
│ stripe_subscription_id
│ status (active/cancelled/past_due)
│ current_period_start
│ current_period_end
│ created_at
└──────────────────┘

┌──────────────────┐
│ payments (nowa)  │
│ subscription_id  │
│ stripe_payment_id│
│ amount_chf       │
│ status           │
│ invoice_url      │
│ created_at       │
└──────────────────┘
```

### 13.2 Co jest już gotowe pod monetyzację w MVP

| Element | Jak jest przygotowany |
|---------|---------------------|
| Limity ogłoszeń | `plan_type` w `posting_quotas` - wystarczy dodać nowe plany |
| Wyróżnione oferty | `is_featured` + `feature_priority` w `job_offers` - sortowanie już uwzględnia |
| Indywidualne limity | `custom_limit` w `posting_quotas` - admin może nadpisać |
| Profil firmy | `is_verified` badge - premium firmy mogą dostawać auto-verify |
| Statystyki | `views_count` w `job_offers` - podstawa do premium analytics |

### 13.3 Modele monetyzacji

**Model 1: Freemium (rekomendowany)**
- Free: 5 ogłoszeń/mies, brak wyróżnień
- Basic (49 CHF/mies): 15 ogłoszeń, 1 wyróżnione
- Premium (149 CHF/mies): 50 ogłoszeń, 5 wyróżnionych, priorytetowa moderacja
- Enterprise (399 CHF/mies): unlimited, dedykowany opiekun, API access

**Model 2: Pay-per-post (alternatywny)**
- Pierwsze 3 ogłoszenia free
- Każde kolejne: 19 CHF / 30 dni
- Wyróżnienie: +29 CHF

**Model 3: Prowizja od sukcesu (zaawansowany)**
- Ogłoszenia darmowe
- Opłata za "kontakt" (odsłonięcie CV): 5 CHF/kandydata
- Opłata za zatrudnienie: 200-500 CHF (trudne do egzekwowania)

**Rekomendacja:** Startuj z modelem Freemium. Daje jasny value proposition, łatwy upsell.

### 13.4 AI Matching (przyszłość)

Architektura gotowa pod AI:
1. Dane profilu pracownika (skills, languages, experience, canton) → vector embedding
2. Dane oferty (requirements, description) → vector embedding
3. Cosine similarity → matching score
4. Rekomendacje: "Oferty dopasowane do Twojego profilu" w panelu pracownika
5. Dla pracodawców: "Kandydaci pasujący do tej oferty" (premium feature)

Technologia: pgvector (PostgreSQL extension) lub dedykowany serwis (np. FastAPI + sentence-transformers)

---

## 14. Design system

### 14.1 Paleta kolorów

```
Primary (czerwony - Szwajcaria):
  50:  #FEF2F2
  100: #FEE2E2
  200: #FECACA
  500: #EF4444   ← akcenty, CTA
  600: #DC2626   ← hover
  700: #B91C1C   ← active
  900: #7F1D1D

Neutral (szarość):
  50:  #F9FAFB   ← tło strony
  100: #F3F4F6   ← tło kart
  200: #E5E7EB   ← bordery
  400: #9CA3AF   ← placeholder text
  600: #4B5563   ← secondary text
  800: #1F2937   ← primary text
  900: #111827   ← headers

White: #FFFFFF
Success: #10B981 (zielony - aktywne, zatwierdzone)
Warning: #F59E0B (pomarańczowy - pending)
Error:   #EF4444 (czerwony - odrzucone, błędy)
Info:    #3B82F6 (niebieski - linki, info)
```

### 14.2 Typografia

```
Font: Inter (Google Fonts) - profesjonalny, czytelny, dobre PL znaki

Headings:
  H1: 36px / 2.25rem / font-bold    (strona główna hero)
  H2: 30px / 1.875rem / font-bold   (sekcje)
  H3: 24px / 1.5rem / font-semibold (podsekcje)
  H4: 20px / 1.25rem / font-semibold (karty)

Body:
  Base: 16px / 1rem / font-normal
  Small: 14px / 0.875rem / font-normal
  XS: 12px / 0.75rem / font-normal (meta, timestamps)

Line height: 1.5 (body), 1.2 (headings)
```

### 14.3 Komponenty UI (shadcn/ui)

| Komponent | Użycie |
|-----------|--------|
| Button | CTA (czerwony), secondary (biały + border), ghost |
| Input | Formularze, wyszukiwarka |
| Select | Filtry (kanton, branża, język) |
| Checkbox | Multi-filtry |
| Card | Oferty pracy, statystyki |
| Badge | Status (aktywne/pending/wygasłe), typ umowy |
| Dialog | Potwierdzenia, aplikowanie |
| Sheet | Filtry na mobile (wysuwany panel) |
| Table | Panel admina, lista kandydatów |
| Tabs | Panel pracownika/pracodawcy |
| Skeleton | Loading states |
| Toast | Powiadomienia (sukces, błąd) |
| Avatar | Logo firmy, inicjały użytkownika |
| Pagination | Lista ofert |

### 14.4 Responsywność (Mobile-First)

```
Breakpoints (Tailwind defaults):
  sm:  640px   (duży telefon)
  md:  768px   (tablet)
  lg:  1024px  (laptop)
  xl:  1280px  (desktop)
  2xl: 1536px  (duży monitor)

Mobile (default):
  - 1 kolumna
  - Hamburger menu
  - Filtry w Sheet (wysuwany panel)
  - Karty ofert: pełna szerokość, stack
  - Bottom navigation (opcjonalnie)

Tablet (md):
  - 2 kolumny kart ofert
  - Sidebar filtrów (collapsible)

Desktop (lg+):
  - 3 kolumny kart na stronie głównej
  - Sidebar filtrów widoczny stale
  - Pełny header z menu
```

### 14.5 Inspiracje wizualne

- **Pracuj.pl** - układ wyszukiwarki i filtrów, karty ofert
- **Indeed** - prostota, czystość, focus na treść
- **LinkedIn Jobs** - szczegóły oferty (sidebar z meta-danymi)
- **jobs.ch** - specyfika CH (kantony, języki)

Kluczowe zasady:
1. Biała przestrzeń - nie tłoczyć elementów
2. Czytelne CTA - czerwony przycisk "Aplikuj" zawsze widoczny
3. Status badges - kolorowe, czytelne na pierwszy rzut oka
4. Ikony pomocnicze - nie dekoracyjne, wspierające skanowanie
5. Konsekwentna siatka - 12-kolumnowa, spójne spacingi (Tailwind)

---

## Podsumowanie decyzji architektonicznych

| Decyzja | Wybór | Uzasadnienie |
|---------|-------|-------------|
| Backend framework | FastAPI | API-first, async, Pydantic, auto-docs |
| Frontend framework | Next.js 14 + React | SSR dla SEO, routing, performance |
| UI framework | Tailwind + shadcn/ui | Szybki development, spójny design |
| State management | Zustand + TanStack Query | Lekki, wystarczający |
| Baza danych | PostgreSQL 16 | Full-text search PL, JSONB, dojrzałość |
| ORM | SQLAlchemy 2.0 async | Dojrzały, async, type-safe |
| Cache | Redis | JWT blacklist, rate limiting, cache |
| Auth | JWT (access + refresh) | Stateless, skalowalne |
| File storage | Lokalne (MVP) → S3 (prod) | Prostota na start |
| Background tasks | APScheduler (MVP) → Celery (prod) | Bez dodatkowej infra na start |
| Deployment | Docker Compose | Łatwy setup, powtarzalność |
| CI/CD | GitHub Actions | Zintegrowane z repo |

---

*Dokument przygotowany jako kompletna specyfikacja techniczno-produktowa. Gotowy do przekazania zespołowi developerów do implementacji.*
