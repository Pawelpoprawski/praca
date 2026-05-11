"""Seed test employers and job offers for demo purposes."""
import logging
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from app.database import async_session
from app.core.security import hash_password
from app.models.user import User
from app.models.employer_profile import EmployerProfile
from app.models.worker_profile import WorkerProfile
from app.models.job_offer import JobOffer
from app.models.posting_quota import PostingQuota
from app.models.category import Category
from app.models.cv_file import CVFile

logger = logging.getLogger(__name__)

EMPLOYERS = [
    {
        "email": "hr@swissbau.ch",
        "company_name": "SwissBau AG",
        "company_slug": "swissbau-ag",
        "description": "SwissBau AG to wiodąca firma budowlana w kantonie Zurych, specjalizująca się w budownictwie mieszkaniowym i komercyjnym. Zatrudniamy ponad 200 pracowników i realizujemy projekty na terenie całej Szwajcarii niemieckojęzycznej.",
        "industry": "Budownictwo",
        "canton": "zurich",
        "city": "Zurych",
        "company_size": "201-500",
    },
    {
        "email": "jobs@alpengastro.ch",
        "company_name": "Alpen Gastro GmbH",
        "company_slug": "alpen-gastro",
        "description": "Sieć restauracji i hoteli w Alpach Berneńskich. Szukamy zmotywowanych pracowników do naszych lokali w Interlaken, Grindelwald i Wengen. Oferujemy zakwaterowanie i wyżywienie.",
        "industry": "Gastronomia",
        "canton": "bern",
        "city": "Interlaken",
        "company_size": "51-200",
    },
    {
        "email": "rekrutacja@cleanpro.ch",
        "company_name": "CleanPro Schweiz",
        "company_slug": "cleanpro-schweiz",
        "description": "Profesjonalne usługi sprzątania dla firm i klientów indywidualnych w Bazylei i okolicach. Działamy od 2010 roku, obsługujemy ponad 500 klientów.",
        "industry": "Usługi",
        "canton": "basel-stadt",
        "city": "Bazylea",
        "company_size": "11-50",
    },
    {
        "email": "praca@transhelvet.ch",
        "company_name": "TransHelvet SA",
        "company_slug": "transhelvet",
        "description": "Firma transportowa z siedzibą w Genewie. Specjalizujemy się w transporcie międzynarodowym i logistyce. Posiadamy flotę 80 pojazdów i szukamy doświadczonych kierowców.",
        "industry": "Transport",
        "canton": "geneve",
        "city": "Genewa",
        "company_size": "51-200",
    },
    {
        "email": "hr@techswiss.ch",
        "company_name": "TechSwiss Solutions",
        "company_slug": "techswiss-solutions",
        "description": "Firma IT z siedzibą w Zurychu, specjalizująca się w rozwiązaniach chmurowych i rozwoju oprogramowania. Międzynarodowy zespół, praca w technologiach: Python, React, AWS, Kubernetes.",
        "industry": "IT",
        "canton": "zurich",
        "city": "Zurych",
        "company_size": "51-200",
    },
    {
        "email": "jobs@carehome-luzern.ch",
        "company_name": "CareHome Luzern",
        "company_slug": "carehome-luzern",
        "description": "Dom opieki dla seniorów w Lucernie. Zatrudniamy opiekunów, pielęgniarki i personel pomocniczy. Oferujemy stabilne zatrudnienie i możliwość rozwoju zawodowego.",
        "industry": "Opieka zdrowotna",
        "canton": "luzern",
        "city": "Lucerna",
        "company_size": "51-200",
    },
]

# category_slug -> list of job offers
JOBS = [
    {
        "title": "Murarz / Tynkarz",
        "description": "Poszukujemy doświadczonego murarza lub tynkarza do pracy na budowach w okolicach Zurychu.\n\nZakres obowiązków:\n- Murowanie ścian z cegły i bloczków\n- Tynkowanie ścian wewnętrznych i zewnętrznych\n- Prace wykończeniowe\n- Współpraca z innymi ekipami na budowie\n\nWymagania:\n- Minimum 3 lata doświadczenia w zawodzie\n- Znajomość niemieckiego na poziomie min. A2\n- Prawo jazdy kat. B\n- Pozwolenie na pracę w Szwajcarii (B lub C)\n\nOferujemy:\n- Wynagrodzenie 5500-6500 CHF/mies.\n- Dodatek za nadgodziny\n- Ubezpieczenie zdrowotne",
        "canton": "zurich",
        "city": "Zurych",
        "contract_type": "full_time",
        "salary_min": 5500,
        "salary_max": 6500,
        "salary_type": "monthly",
        "experience_min": 3,
        "is_remote": "no",
        "languages_required": [{"lang": "de", "level": "A2"}],
        "employer_idx": 0,
        "category_slug": "budownictwo",
    },
    {
        "title": "Elektryk budowlany",
        "description": "Firma SwissBau AG zatrudni elektryka budowlanego do pracy przy nowych inwestycjach.\n\nObowiązki:\n- Instalacje elektryczne w budynkach mieszkalnych i komercyjnych\n- Montaż rozdzielnic i skrzynek elektrycznych\n- Prowadzenie przewodów zgodnie z normami CH\n- Pomiary i odbiory instalacji\n\nWymagania:\n- Dyplom elektryka lub pokrewny\n- 2+ lata doświadczenia\n- Znajomość norm SEV\n- Język niemiecki min. B1\n\nOferujemy:\n- 6000-7500 CHF/mies. zależnie od doświadczenia\n- Szkolenia i certyfikaty opłacane przez firmę\n- 13. pensja",
        "canton": "zurich",
        "city": "Winterthur",
        "contract_type": "full_time",
        "salary_min": 6000,
        "salary_max": 7500,
        "salary_type": "monthly",
        "experience_min": 2,
        "is_remote": "no",
        "languages_required": [{"lang": "de", "level": "B1"}],
        "employer_idx": 0,
        "category_slug": "budownictwo",
    },
    {
        "title": "Kucharz / Kucharka",
        "description": "Hotel w Interlaken poszukuje kucharza/kucharki do pracy w restauracji hotelowej.\n\nObowiązki:\n- Przygotowanie posiłków (kuchnia europejska i szwajcarska)\n- Planowanie menu wspólnie z szefem kuchni\n- Zarządzanie zapasami\n- Dbanie o standardy higieny HACCP\n\nWymagania:\n- Doświadczenie min. 2 lata w gastronomii\n- Znajomość HACCP\n- Język niemiecki lub francuski min. A2\n\nOferujemy:\n- 4800-5800 CHF/mies.\n- Zakwaterowanie (pokój jednoosobowy)\n- Wyżywienie w trakcie pracy\n- Piękna lokalizacja w Alpach",
        "canton": "bern",
        "city": "Interlaken",
        "contract_type": "full_time",
        "salary_min": 4800,
        "salary_max": 5800,
        "salary_type": "monthly",
        "experience_min": 2,
        "is_remote": "no",
        "languages_required": [{"lang": "de", "level": "A2"}],
        "employer_idx": 1,
        "category_slug": "gastronomia",
    },
    {
        "title": "Kelner / Kelnerka (sezon zimowy)",
        "description": "Restauracja w Grindelwald szuka kelnerów na sezon zimowy 2026/2027.\n\nOkres pracy: grudzień 2026 - kwiecień 2027\n\nObowiązki:\n- Obsługa gości (restauracja, bar)\n- Przyjmowanie zamówień\n- Serwowanie potraw i napojów\n- Utrzymanie czystości w sali\n\nWymagania:\n- Doświadczenie w gastronomii mile widziane\n- Komunikatywny niemiecki (min. A2)\n- Pozytywne nastawienie i dyspozycyjność\n\nOferujemy:\n- 4200-4800 CHF/mies. + napiwki\n- Zakwaterowanie i wyżywienie\n- Karnet narciarski gratis!",
        "canton": "bern",
        "city": "Grindelwald",
        "contract_type": "temporary",
        "salary_min": 4200,
        "salary_max": 4800,
        "salary_type": "monthly",
        "experience_min": 0,
        "is_remote": "no",
        "languages_required": [{"lang": "de", "level": "A2"}],
        "employer_idx": 1,
        "category_slug": "gastronomia",
    },
    {
        "title": "Pracownik sprzątający (biura)",
        "description": "CleanPro Schweiz zatrudni pracowników do sprzątania biur w centrum Bazylei.\n\nGodziny pracy: pon-pt, 17:00-21:00 (20h/tydzień)\n\nObowiązki:\n- Sprzątanie biur i przestrzeni wspólnych\n- Odkurzanie, mycie podłóg\n- Czyszczenie sanitariatów\n- Opróżnianie koszy\n\nWymagania:\n- Rzetelność i dokładność\n- Język niemiecki nie jest wymagany (instrukcje w języku polskim)\n- Pozwolenie na pracę w CH\n\nOferujemy:\n- 25-28 CHF/godz.\n- Elastyczny grafik\n- Umowa na czas nieokreślony po okresie próbnym",
        "canton": "basel-stadt",
        "city": "Bazylea",
        "contract_type": "part_time",
        "salary_min": 25,
        "salary_max": 28,
        "salary_type": "hourly",
        "experience_min": 0,
        "is_remote": "no",
        "languages_required": [],
        "employer_idx": 2,
        "category_slug": "sprzatanie",
    },
    {
        "title": "Kierowca C+E (transport międzynarodowy)",
        "description": "TransHelvet SA poszukuje kierowców z kategorią C+E do transportu międzynarodowego.\n\nTrasy: Szwajcaria - Polska - Niemcy - Francja\n\nObowiązki:\n- Prowadzenie ciągnika siodłowego z naczepą\n- Załadunek i rozładunek towarów\n- Prowadzenie dokumentacji przewozowej\n- Dbałość o powierzony pojazd\n\nWymagania:\n- Prawo jazdy kat. C+E\n- Karta kierowcy (tachograf cyfrowy)\n- Certyfikat ADR mile widziany\n- Doświadczenie min. 2 lata w transporcie międzynarodowym\n- Język niemiecki lub francuski min. A1\n\nOferujemy:\n- 5500-7000 CHF/mies.\n- Nowoczesne pojazdy (Volvo, Scania)\n- Premie za bezszkodową jazdę\n- Regularne powroty do domu",
        "canton": "geneve",
        "city": "Genewa",
        "contract_type": "full_time",
        "salary_min": 5500,
        "salary_max": 7000,
        "salary_type": "monthly",
        "experience_min": 2,
        "is_remote": "no",
        "languages_required": [{"lang": "fr", "level": "A1"}],
        "employer_idx": 3,
        "category_slug": "transport",
    },
    {
        "title": "Full-Stack Developer (Python/React)",
        "description": "TechSwiss Solutions szuka doświadczonego Full-Stack Developera.\n\nTechnologie:\n- Backend: Python, FastAPI, PostgreSQL, Redis\n- Frontend: React, TypeScript, Next.js\n- Cloud: AWS (ECS, Lambda, S3, RDS)\n- DevOps: Docker, Kubernetes, Terraform\n\nObowiązki:\n- Rozwój i utrzymanie aplikacji webowych\n- Udział w code review i planowaniu sprintów\n- Współpraca z zespołem UX/UI\n- Pisanie testów jednostkowych i integracyjnych\n\nWymagania:\n- 3+ lata doświadczenia w Python + React/TypeScript\n- Znajomość SQL i NoSQL databases\n- Doświadczenie z REST API\n- Angielski min. B2 (język pracy)\n\nOferujemy:\n- 9000-12000 CHF/mies.\n- Praca hybrydowa (2 dni w biurze, 3 z domu)\n- 25 dni urlopu\n- Budżet szkoleniowy 3000 CHF/rok\n- Nowoczesne biuro w centrum Zurychu",
        "canton": "zurich",
        "city": "Zurych",
        "contract_type": "full_time",
        "salary_min": 9000,
        "salary_max": 12000,
        "salary_type": "monthly",
        "experience_min": 3,
        "is_remote": "hybrid",
        "languages_required": [{"lang": "en", "level": "B2"}],
        "employer_idx": 4,
        "category_slug": "it",
        "is_featured": True,
    },
    {
        "title": "DevOps Engineer",
        "description": "Dołącz do naszego zespołu DevOps w TechSwiss Solutions!\n\nObowiązki:\n- Zarządzanie infrastrukturą AWS (ECS, RDS, ElastiCache)\n- CI/CD pipelines (GitHub Actions, ArgoCD)\n- Monitoring i alerting (Prometheus, Grafana)\n- Infrastructure as Code (Terraform, CloudFormation)\n- Bezpieczeństwo i compliance\n\nWymagania:\n- 3+ lata doświadczenia w DevOps/SRE\n- Dobra znajomość AWS lub GCP\n- Docker, Kubernetes\n- Linux administration\n- Scripting (Bash, Python)\n- Angielski B2+\n\nOferujemy:\n- 10000-13000 CHF/mies.\n- Praca zdalna (full remote możliwy)\n- Stock options\n- Konferencje i certyfikaty (AWS, K8s)",
        "canton": "zurich",
        "city": "Zurych",
        "contract_type": "full_time",
        "salary_min": 10000,
        "salary_max": 13000,
        "salary_type": "monthly",
        "experience_min": 3,
        "is_remote": "yes",
        "languages_required": [{"lang": "en", "level": "B2"}],
        "employer_idx": 4,
        "category_slug": "it",
    },
    {
        "title": "Opiekun/ka osób starszych",
        "description": "Dom opieki CareHome Luzern poszukuje opiekunów osób starszych.\n\nObowiązki:\n- Codzienna opieka nad pensjonariuszami\n- Pomoc w higienie osobistej\n- Podawanie posiłków i leków\n- Organizacja czasu wolnego\n- Współpraca z personelem medycznym\n\nWymagania:\n- Doświadczenie w opiece nad osobami starszymi\n- Empatia i cierpliwość\n- Język niemiecki min. A2 (B1 preferowany)\n- Pozwolenie na pracę w CH\n\nOferujemy:\n- 4500-5500 CHF/mies.\n- Harmonogram zmianowy (6:00-14:00 lub 14:00-22:00)\n- 13. pensja\n- Kursy języka niemieckiego opłacone przez pracodawcę\n- Pomoc w znalezieniu mieszkania",
        "canton": "luzern",
        "city": "Lucerna",
        "contract_type": "full_time",
        "salary_min": 4500,
        "salary_max": 5500,
        "salary_type": "monthly",
        "experience_min": 1,
        "is_remote": "no",
        "languages_required": [{"lang": "de", "level": "A2"}],
        "employer_idx": 5,
        "category_slug": "opieka",
    },
    {
        "title": "Magazynier / Pracownik magazynowy",
        "description": "TransHelvet SA zatrudni pracownika magazynowego do centrum logistycznego w Genewie.\n\nObowiązki:\n- Przyjmowanie i wydawanie towarów\n- Obsługa wózka widłowego\n- Kompletacja zamówień\n- Kontrola stanów magazynowych\n- Utrzymanie porządku w magazynie\n\nWymagania:\n- Uprawnienia na wózek widłowy (mile widziane)\n- Sprawność fizyczna\n- Rzetelność i punktualność\n- Język francuski min. A1\n\nOferujemy:\n- 4500-5200 CHF/mies.\n- Praca pon-pt 7:00-16:00\n- Bezpłatne szkolenie na wózek widłowy\n- Sponsoring pozwolenia na pracę (dla odpowiednich kandydatów)",
        "canton": "geneve",
        "city": "Genewa",
        "contract_type": "full_time",
        "salary_min": 4500,
        "salary_max": 5200,
        "salary_type": "monthly",
        "experience_min": 0,
        "is_remote": "no",
        "languages_required": [{"lang": "fr", "level": "A1"}],
        "employer_idx": 3,
        "category_slug": "transport",
    },
    {
        "title": "Malarz budowlany",
        "description": "Poszukujemy malarza budowlanego do pracy przy remontach i nowych budowach w okolicach Zurychu.\n\nObowiązki:\n- Malowanie ścian i sufitów\n- Tapetowanie\n- Szpachlowanie i przygotowanie powierzchni\n- Prace wykończeniowe\n\nWymagania:\n- Min. 2 lata doświadczenia\n- Znajomość technik malarskich\n- Prawo jazdy kat. B mile widziane\n- Niemiecki A2\n\nOferujemy:\n- 5000-6000 CHF/mies.\n- Narzędzia i materiały zapewnione\n- Stabilne zatrudnienie",
        "canton": "zurich",
        "city": "Zurych",
        "contract_type": "full_time",
        "salary_min": 5000,
        "salary_max": 6000,
        "salary_type": "monthly",
        "experience_min": 2,
        "is_remote": "no",
        "languages_required": [{"lang": "de", "level": "A2"}],
        "employer_idx": 0,
        "category_slug": "budownictwo",
    },
    {
        "title": "Pomoc kuchenna",
        "description": "Hotel w Wengen (Alpy Berneńskie) szuka pomocy kuchennej.\n\nObowiązki:\n- Pomoc w przygotowaniu posiłków\n- Obieranie, krojenie warzyw\n- Utrzymanie czystości w kuchni\n- Mycie naczyń\n\nWymagania:\n- Chęć do pracy i nauki\n- Bez doświadczenia - przyuczymy!\n- Higiena osobista\n\nOferujemy:\n- 3800-4200 CHF/mies.\n- Zakwaterowanie + wyżywienie\n- Nauka zawodu kucharza\n- Praca w pięknej scenerii alpejskiej",
        "canton": "bern",
        "city": "Wengen",
        "contract_type": "full_time",
        "salary_min": 3800,
        "salary_max": 4200,
        "salary_type": "monthly",
        "experience_min": 0,
        "is_remote": "no",
        "languages_required": [],
        "employer_idx": 1,
        "category_slug": "gastronomia",
    },
]

WORKERS = [
    {
        "email": "jan.kowalski@gmail.com",
        "first_name": "Jan",
        "last_name": "Kowalski",
        "phone": "+41 79 123 45 67",
        "canton": "zurich",
        "work_permit": "permit_b",
        "experience_years": 5,
        "bio": "Doświadczony murarz z 5-letnim stażem pracy w Szwajcarii. Szukam stabilnego zatrudnienia w budownictwie.",
        "industry": "Budownictwo",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "B1"}],
        "skills": ["murowanie", "tynkowanie", "prace wykończeniowe"],
        "cv_extracted": {
            "name": "Jan Kowalski",
            "email": "jan.kowalski@gmail.com",
            "phone": "+41 79 123 45 67",
            "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "B1"}, {"lang": "en", "level": "A2"}],
        },
    },
    {
        "email": "anna.nowak@gmail.com",
        "first_name": "Anna",
        "last_name": "Nowak",
        "phone": "+41 76 234 56 78",
        "canton": "bern",
        "work_permit": "permit_b",
        "experience_years": 3,
        "bio": "Dyplomowana pielęgniarka z doświadczeniem w opiece nad osobami starszymi. Pracowałam 2 lata w domu opieki w Lucernie.",
        "industry": "Opieka zdrowotna",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "B2"}, {"lang": "en", "level": "B1"}],
        "skills": ["opieka nad seniorami", "pierwsza pomoc", "pielęgniarstwo"],
        "cv_extracted": {
            "name": "Anna Nowak",
            "email": "anna.nowak@gmail.com",
            "phone": "+41 76 234 56 78",
            "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "B2"}, {"lang": "en", "level": "B1"}],
        },
    },
    {
        "email": "piotr.wisniewski@wp.pl",
        "first_name": "Piotr",
        "last_name": "Wiśniewski",
        "phone": "+41 78 345 67 89",
        "canton": "geneve",
        "work_permit": "permit_c",
        "experience_years": 8,
        "bio": "Kierowca C+E z wieloletnim doświadczeniem w transporcie międzynarodowym. Aktualnie szukam tras Szwajcaria-Polska.",
        "industry": "Transport",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "fr", "level": "B1"}, {"lang": "de", "level": "A2"}],
        "skills": ["prawo jazdy C+E", "ADR", "tachograf cyfrowy", "logistyka"],
        "cv_extracted": {
            "name": "Piotr Wiśniewski",
            "email": "piotr.wisniewski@wp.pl",
            "phone": "+41 78 345 67 89",
            "languages": [{"lang": "pl", "level": "C2"}, {"lang": "fr", "level": "B1"}, {"lang": "de", "level": "A2"}],
        },
    },
    {
        "email": "katarzyna.zielinska@gmail.com",
        "first_name": "Katarzyna",
        "last_name": "Zielińska",
        "phone": "+41 79 456 78 90",
        "canton": "zurich",
        "work_permit": "permit_b",
        "experience_years": 4,
        "bio": "Full-Stack Developer z 4-letnim doświadczeniem w Python i React. Szukam pracy w sektorze IT w Zurychu.",
        "industry": "IT",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "en", "level": "C1"}, {"lang": "de", "level": "B1"}],
        "skills": ["Python", "React", "TypeScript", "PostgreSQL", "Docker"],
        "cv_extracted": {
            "name": "Katarzyna Zielińska",
            "email": "katarzyna.zielinska@gmail.com",
            "phone": "+41 79 456 78 90",
            "languages": [{"lang": "pl", "level": "C2"}, {"lang": "en", "level": "C1"}, {"lang": "de", "level": "B1"}],
        },
    },
    {
        "email": "marek.wojciechowski@onet.pl",
        "first_name": "Marek",
        "last_name": "Wojciechowski",
        "phone": "+41 77 567 89 01",
        "canton": "basel-stadt",
        "work_permit": "permit_g",
        "experience_years": 10,
        "bio": "Doświadczony elektryk budowlany ze znajomością norm SEV. Pracuję jako Grenzgänger z Niemiec.",
        "industry": "Budownictwo",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "C1"}],
        "skills": ["instalacje elektryczne", "normy SEV", "pomiary", "rozdzielnice"],
        "cv_extracted": {
            "name": "Marek Wojciechowski",
            "email": "marek.wojciechowski@onet.pl",
            "phone": "+41 77 567 89 01",
            "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "C1"}, {"lang": "en", "level": "A2"}],
        },
    },
    {
        "email": "ewa.kaminska@gmail.com",
        "first_name": "Ewa",
        "last_name": "Kamińska",
        "phone": "+41 76 678 90 12",
        "canton": "bern",
        "work_permit": "permit_b",
        "experience_years": 2,
        "bio": "Kucharka z doświadczeniem w kuchni europejskiej i polskiej. Szukam pracy w gastronomii w regionie berneńskim.",
        "industry": "Gastronomia",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "A2"}],
        "skills": ["kuchnia europejska", "HACCP", "planowanie menu", "kuchnia polska"],
        "cv_extracted": {
            "name": "Ewa Kamińska",
            "email": "ewa.kaminska@gmail.com",
            "phone": "+41 76 678 90 12",
            "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "A2"}],
        },
    },
    {
        "email": "tomasz.lewandowski@gmail.com",
        "first_name": "Tomasz",
        "last_name": "Lewandowski",
        "phone": "+41 78 789 01 23",
        "canton": "zurich",
        "work_permit": "permit_b",
        "experience_years": 6,
        "bio": "Malarz budowlany specjalizujący się w pracach wykończeniowych. Doświadczenie przy projektach komercyjnych i mieszkalnych.",
        "industry": "Budownictwo",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "B1"}, {"lang": "en", "level": "A2"}],
        "skills": ["malowanie", "tapetowanie", "szpachlowanie", "lakierowanie"],
        "cv_extracted": {
            "name": "Tomasz Lewandowski",
            "email": "tomasz.lewandowski@gmail.com",
            "phone": "+41 78 789 01 23",
            "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "B1"}],
        },
    },
    {
        "email": "magdalena.dabrowska@yahoo.com",
        "first_name": "Magdalena",
        "last_name": "Dąbrowska",
        "phone": "+41 79 890 12 34",
        "canton": "luzern",
        "work_permit": "permit_b",
        "experience_years": 1,
        "bio": "Opiekunka osób starszych, ukończyłam kurs opiekuna medycznego w Polsce. Empatyczna i cierpliwa.",
        "industry": "Opieka zdrowotna",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "A2"}],
        "skills": ["opieka nad seniorami", "higiena osobista", "podawanie leków"],
        "cv_extracted": {
            "name": "Magdalena Dąbrowska",
            "email": "magdalena.dabrowska@yahoo.com",
            "phone": "+41 79 890 12 34",
            "languages": [{"lang": "pl", "level": "C2"}, {"lang": "de", "level": "A2"}],
        },
    },
    {
        "email": "adam.szymanski@gmail.com",
        "first_name": "Adam",
        "last_name": "Szymański",
        "phone": "+41 77 901 23 45",
        "canton": "geneve",
        "work_permit": "permit_b",
        "experience_years": 0,
        "bio": "Świeżo po studiach, szukam pierwszej pracy w Szwajcarii. Chętny do nauki i ciężkiej pracy.",
        "industry": "Gastronomia",
        "languages": [{"lang": "pl", "level": "C2"}, {"lang": "fr", "level": "A1"}],
        "skills": ["obsługa klienta", "praca zespołowa"],
        "cv_extracted": None,  # No extracted data (simulates failed extraction)
    },
]


async def seed_demo_data():
    """Seed demo employers, jobs, and a test worker."""
    async with async_session() as db:
        # Check if already seeded
        existing = await db.execute(
            select(User).where(User.email == EMPLOYERS[0]["email"])
        )
        if existing.scalar_one_or_none():
            logger.info("Demo data already seeded, skipping")
            return

        # Get categories
        cat_result = await db.execute(select(Category))
        categories = {c.slug: c.id for c in cat_result.scalars().all()}

        # Create employers
        employer_profiles = []
        now = datetime.now(timezone.utc)

        for emp_data in EMPLOYERS:
            user = User(
                email=emp_data["email"],
                password_hash=hash_password("demo123"),
                role="employer",
                first_name="HR",
                last_name=emp_data["company_name"].split()[0],
                is_active=True,
                is_verified=True,
            )
            db.add(user)
            await db.flush()

            profile = EmployerProfile(
                user_id=user.id,
                company_name=emp_data["company_name"],
                company_slug=emp_data["company_slug"],
                description=emp_data["description"],
                industry=emp_data["industry"],
                canton=emp_data["canton"],
                city=emp_data["city"],
                company_size=emp_data["company_size"],
                is_verified=True,
            )
            db.add(profile)
            await db.flush()

            # Quota
            quota = PostingQuota(
                employer_id=profile.id,
                plan_type="free",
                monthly_limit=5,
                used_count=0,
                period_start=now.date(),
                period_end=(now + timedelta(days=30)).date(),
            )
            db.add(quota)
            employer_profiles.append(profile)

        # Create jobs
        for i, job_data in enumerate(JOBS):
            employer_profile = employer_profiles[job_data["employer_idx"]]
            cat_slug = job_data["category_slug"]
            category_id = categories.get(cat_slug)

            published_offset = timedelta(hours=i * 8 + 2)  # stagger publish times

            job = JobOffer(
                employer_id=employer_profile.id,
                category_id=category_id,
                title=job_data["title"],
                description=job_data["description"],
                canton=job_data["canton"],
                city=job_data["city"],
                contract_type=job_data["contract_type"],
                salary_min=job_data["salary_min"],
                salary_max=job_data["salary_max"],
                salary_type=job_data["salary_type"],
                experience_min=job_data["experience_min"],
                is_remote=job_data["is_remote"],
                languages_required=job_data["languages_required"],
                is_featured=job_data.get("is_featured", False),
                feature_priority=5 if job_data.get("is_featured") else 0,
                apply_via="portal",
                status="active",
                published_at=now - published_offset,
                expires_at=None,
                views_count=(12 - i) * 7 + 3,  # decreasing views
            )
            db.add(job)

        # Create test workers
        for w_data in WORKERS:
            worker_user = User(
                email=w_data["email"],
                password_hash=hash_password("demo123"),
                role="worker",
                first_name=w_data["first_name"],
                last_name=w_data["last_name"],
                phone=w_data["phone"],
                is_active=True,
                is_verified=True,
            )
            db.add(worker_user)
            await db.flush()

            worker_profile = WorkerProfile(
                user_id=worker_user.id,
                canton=w_data["canton"],
                work_permit=w_data["work_permit"],
                experience_years=w_data["experience_years"],
                bio=w_data["bio"],
                industry=w_data["industry"],
                languages=w_data["languages"],
                skills=w_data["skills"],
            )
            db.add(worker_profile)
            await db.flush()

            # Create mock CV record with extracted data
            cv_ext = w_data.get("cv_extracted")
            cv_file = CVFile(
                user_id=worker_user.id,
                original_filename=f"CV_{w_data['first_name']}_{w_data['last_name']}.pdf",
                stored_filename=f"{uuid.uuid4()}.pdf",
                file_path=f"uploads/cv/mock_{worker_user.id}.pdf",
                file_size=150000 + hash(w_data["email"]) % 200000,
                mime_type="application/pdf",
                is_active=True,
                extraction_status="completed" if cv_ext else "failed",
                extracted_name=cv_ext["name"] if cv_ext else None,
                extracted_email=cv_ext["email"] if cv_ext else None,
                extracted_phone=cv_ext["phone"] if cv_ext else None,
                extracted_languages=cv_ext["languages"] if cv_ext else None,
                extracted_text=f"Mock CV text for {w_data['first_name']} {w_data['last_name']}" if cv_ext else None,
            )
            db.add(cv_file)
            await db.flush()

            worker_profile.active_cv_id = cv_file.id

        await db.commit()
        logger.info(f"Seeded {len(EMPLOYERS)} employers, {len(JOBS)} jobs, {len(WORKERS)} workers")
