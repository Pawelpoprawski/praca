"""Job translation service — DE/FR/IT -> Polish.

Step 1 of the two-step pipeline for scraped jobs:
1. Translation (this service): translate foreign-language title/description to Polish, activate job
2. Extraction (job_extraction_service): extract metadata from Polish text

Manual employer jobs skip translation entirely (already Polish + already active).
"""
import json
import logging
import re
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from app.config import get_settings
from app.database import async_session
from app.models.job_offer import JobOffer
from app.services.activity_logger import log_activity

logger = logging.getLogger(__name__)

TRANSLATION_VERSION = 1
MAX_TRANSLATION_ATTEMPTS = 3

JOB_TRANSLATION_PROMPT = """Przetlumacz oferte pracy na polski i sformatuj jako HTML.

Tytul: {title}
Firma: {company}
Opis: {description}

Zwroc JSON:
{{
  "translated_title": "<oczyszczony tytul po polsku — TYLKO nazwa stanowiska>",
  "translated_description": "<HTML z dokladnie 3 sekcjami w tej kolejnosci>",
  "contact_email": "<email aplikacyjny WYCIAGNIETY ze zrodlowego opisu, lub null jezeli brak>"
}}

═══════════════════════════════════════════════════════════
WYCIAGNIECIE EMAILA APLIKACYJNEGO (KRYTYCZNE)
═══════════════════════════════════════════════════════════

ZANIM usuniesz dane kontaktowe z opisu — najpierw WYCIAGNIJ pierwszy adres email
do aplikacji i zapisz go w polu "contact_email".

Email aplikacyjny to adres pod ktory kandydat ma WYSLAC swoje CV. Wskazniki:
- "Aplikuj wysylajac maila na: X@Y.Z"
- "Wyslij CV na adres: X@Y.Z"
- "Osoby zainteresowane prosimy o aplikacje na: X@Y.Z"
- "Kontakt: X@Y.Z"
- "info@firma.ch", "recruitment@firma.com", "biuro@firma.pl", "hr@firma..."

Jezeli oryginal ma WIELE emaili — wybierz GLOWNY (zwykle pierwszy lub najbardziej
"officjalny": recruitment@, hr@, info@, kontakt@).

Jezeli BRAK emaila aplikacyjnego — zwroc "contact_email": null (kandydat zostanie
przekierowany na oryginalna strone z linkiem).

PO wyciagnieciu maila — usun go z translated_description tak jak inne kontakty
(zgodnie z zasadami w sekcji DANE KONTAKTOWE ponizej).

═══════════════════════════════════════════════════════════
TYTUL — TYLKO NAZWA STANOWISKA. NIC INNEGO.
═══════════════════════════════════════════════════════════

ZASADA #1: Zwracasz WYLACZNIE nazwe zawodu / stanowiska. Maksymalnie 2-7 slow.
ZASADA #2: Jezeli widzisz w tytule cokolwiek co NIE jest nazwa zawodu — USUN to.

KATEGORIE rzeczy do wycielczenia z tytulu (kazda BEZ WYJATKOW):

1. LOKALIZACJE — wszystkie miasta, kantony, kraje:
   "Szwajcaria", "Cala Szwajcaria", "do Szwajcarii", "SZWAJCARIA"
   Zurich, Zürich, Zurych, Bern, Berno, Basel, Bazylea, Luzern, Lucerna,
   Zug, Geneve, Genewa, Wallis, Schwyz, Thurgau, Aarau, Sursee, Wadenswil,
   Reichenburg, Andermatt, Lachen, Solothurn, Fribourg, Neuchatel, Valais,
   Vaud, Ticino, Graubunden, Uri, Obwalden, Nidwalden, Glarus, Appenzell,
   Schaffhausen, Jura, St-Gallen, "Inne lokalizacje", "okolice X"

2. PENSJE — wszelkie liczby z waluta:
   "34-38 CHF", "37,00 CHF", "/godz", "/h", "/Godzina", "brutto", "netto",
   "+18 Euro Netto Dzien Diety", "od 2200 CHF", "do 25 000 zl", "msc netto",
   "4200-4900 CHF NETTO" — wszystko zwiazane z wynagrodzeniem precz

3. TRYB i CZAS:
   "Praca od Zaraz", "OD ZARAZ", "START OD ZARAZ", "ZARAZ" sam,
   "Stale zatrudnienie", "Stala praca", "Pelny etat", "Czesc etatu",
   "100%", "80%" itp.

4. UMOWA:
   "Szwajcarska Umowa", "Szwajcarska Umowa o Prace", "Umowa o prace",
   "Kontrakt", "B2B"

5. KORZYSCI:
   "Zakwaterowanie", "Darmowe mieszkanie", "Darmowe posilki",
   "Darmowe zakwaterowanie", "Wysokie zarobki", "Dieta dzienna"

6. WYMAGANIA jezykowe i transportowe:
   "dobry niemiecki", "wymagany niemiecki", "j.niem", "j.ang",
   "i auto", "z prawem jazdy", "wlasne narzedzia",
   "z certyfikatem", "z doswiadczeniem w PERI/DOKA"

7. KODY/PLEC:
   "(m/w/d)", "(w/m/d)", "(m/k)", "(k/m)", "/-ka", "EFZ", "EBA"

8. PREFIX ILOSCI:
   "2x Malarz" -> "Malarz (2 stanowiska)" (przenies do nawiasu)
   "3x Stolarz" -> "Stolarz (3 stanowiska)"

9. WSZELKIE SEPARATORY KONCOWE:
   trailing " - ", " – ", " | ", " / ", przecinki, plusy

PRZETLUMACZ niemieckie nazwy zawodow na polski, oryginal w nawiasie:
- Bauspengler -> "Blacharz budowlany (Bauspengler)"
- Dachdecker -> "Dekarz (Dachdecker)"
- Polymechaniker -> "Polimechanik (Polymechaniker)"
- Zimmermann -> "Ciesla (Zimmermann)"
- Schreiner / Mobelschreiner -> "Stolarz (Schreiner)"
- Maler -> "Malarz (Maler)"
- Fassadenbauer -> "Monter fasad (Fassadenbauer)"
- Strassenbauer -> "Pracownik drogowy (Strassenbauer)"
- Heizungsmonteur -> "Monter ogrzewania (Heizungsmonteur)"
- Mechatroniker -> "Mechatronik (Mechatroniker)"
- Metallbauer -> "Slusarz konstrukcji (Metallbauer)"
- Deckenmonteur -> "Monter sufitow (Deckenmonteur)"
- Walzenfuhrer -> "Operator walca (Walzenfuhrer)"
- Kranfuhrer -> "Operator dzwigu (Kranfuhrer)"
- Autolackierer -> "Lakiernik samochodowy (Autolackierer)"
- Baumaschinenmechaniker -> "Mechanik maszyn budowlanych (Baumaschinenmechaniker)"

PREFIX ILOSCI: jezeli tytul zaczyna sie od "2x", "3x" itp. — zamien na sufix:
  "2x Malarz" -> "Malarz (2 stanowiska)"
  "3x Stolarz budowlany" -> "Stolarz budowlany (3 stanowiska)"

PRZYKLADY tytulu (BAD -> GOOD):
  BAD:  "Glazurnik – Luzern Inne Lokalizacje - 37,00 CHF / Brutto / Godzina + 18,00 Euro / Netto / Dzień / Diety – Szwajcarska Umowa o Pracę – Zakwaterowanie – Praca od Zaraz"
  GOOD: "Glazurnik"

  BAD:  "Mechanik / Mechaniczka pojazdów ciężarowych - stałe zatrudnienie / darmowe mieszkanie"
  GOOD: "Mechanik pojazdów ciężarowych"

  BAD:  "Cieśla szalunkowy z doświadczeniem w PERI / DOKA, dobry niemiecki i auto, Wallis - Wädenswil - Zurych - Lucerna"
  GOOD: "Cieśla szalunkowy (PERI/DOKA)"

  BAD:  "Mechatronik / Mechanik - Zürich - Szwajcarska Umowa o Pracę - Praca od Zaraz"
  GOOD: "Mechatronik / Mechanik"

  BAD:  "2x Malarz"
  GOOD: "Malarz (2 stanowiska)"

  BAD:  "Monter rusztowań – Szwajcaria | 4200–4900 CHF NETTO | Wysokie zarobki | OD ZARAZ"
  GOOD: "Monter rusztowań"

  BAD:  "Operator CNC / CNC Abkartner / 33-38 CHF / OD ZARAZ Szwajcaria"
  GOOD: "Operator CNC (Abkartner)"

  BAD:  "Rzeźnik SZWAJCARIA do 25 000 zł msc netto"
  GOOD: "Rzeźnik"

  BAD:  "Mechatronik / mechatroniczka pojazdów samochodowych Szwajcaria"
  GOOD: "Mechatronik pojazdów samochodowych"

  BAD:  "Mechanik w parku rozrywki od 2200 Chf netto, DARMOWE zakwaterowanie, darmowe posiłki"
  GOOD: "Mechanik"

  BAD:  "Spawacz /-ka aluminium do Szwajcarii 36-39 CHF brutto/h j.niem lub ang-bez certyfikatów"
  GOOD: "Spawacz aluminium"

DOBRY tytul: 2-7 slow, max 70 znakow, TYLKO nazwa stanowiska.

KONTROLA SAMODZIELNA: zanim zwrocisz translated_title — przeczytaj go i sprawdz:
- Czy zawiera jakas liczbe? Jezeli tak (oprocz "(2 stanowiska)") — USUN.
- Czy zawiera nazwe miasta lub kraju? Jezeli tak — USUN.
- Czy zawiera "CHF", "Euro", "EUR", "PLN", "zl"? Jezeli tak — USUN.
- Czy zawiera "ZARAZ", "OD", "umowa", "etat", "darmowe"? Jezeli tak — USUN.
- Czy konczy sie separatorem (- | / ,)? Jezeli tak — USUN go.

═══════════════════════════════════════════════════════════
OPIS — struktura HTML, anti-duplikacja.
═══════════════════════════════════════════════════════════

STRUKTURA HTML (sztywna, nie odbiegaj):
<h3>Opis stanowiska</h3>
<ul><li>...</li><li>...</li></ul>

<h3>Wymagania</h3>
<ul><li>...</li><li>...</li></ul>

<h3>Oferujemy</h3>
<ul><li>...</li><li>...</li></ul>

ZASADY HTML — KRYTYCZNE:
- ZARAZ po <h3> wstaw <ul>. NIGDY nie wstawiaj <p>...:</p> miedzy <h3> a <ul>.
- ZAKAZANE wzorce (NIE generuj ich nigdy):
  BAD: <h3>Wymagania</h3><p>Wymagania:</p><ul>...
  BAD: <h3>Opis stanowiska</h3><p>Zakres obowiazkow:</p><ul>...
  BAD: <h3>Opis stanowiska</h3><p>OBOWIAZKI:</p><ul>...
  BAD: <h3>Opis stanowiska</h3><p>Twoje zadania:</p><ul>...
  BAD: <h3>Oferujemy</h3><p>Nasza oferta:</p><ul>...
  BAD: <h3>Oferujemy</h3><p>Co oferujemy:</p><ul>...
- DOBRZE:
  GOOD: <h3>Wymagania</h3><ul><li>Komunikatywny niemiecki</li>...
- Jezeli oryginal ma label typu "Aufgaben:" / "Anforderungen:" / "Wir bieten:"
  / "Zakres obowiazkow:" / "Wymagania:" / "Nasza oferta:" / "Twoje zadania:"
  / "OBOWIAZKI:" — POMIN go, uzyj WYLACZNIE <h3>.

Dozwolone tagi: h3, ul, ol, li, p, strong, em, br. Nic innego.
<p> uzywaj TYLKO dla luznego tekstu poza sekcjami (kontakt, dodatkowe info).
Punkty z duzej litery, zdania konczone kropka.

TRESC OPISU — zostaw wszystko co byc powinno:
- ZACHOWUJ informacje o pensji, miejscu pracy, umowie, zakwaterowaniu,
  dietach, godzinach pracy itp. — uzytkownik chce miec te dane w opisie.
- ZACHOWUJ wymagania jezykowe dotyczace dokumentow:
  "CV w jezyku niemieckim", "list motywacyjny po niemiecku",
  "swiadectwo przetlumaczone na niemiecki", "klauzula RODO po niemiecku" — TO ZOSTAWIAJ.
- Tlumacz z DE/FR/IT na polski (lub przepisz juz polski w lepszym stylu)
- Z TRESCI usun tylko znaki ozdobne: =>  -> ➜ ► ★ ✓ ●
- Zachowaj nazwy wlasne firm i certyfikatow w oryginale
- Jezeli sekcja nie ma tresci w oryginale — POMIN cala sekcje (bez pustego <h3>)

═══════════════════════════════════════════════════════════
KRYTYCZNE — DANE KONTAKTOWE: USUN WSZYSTKIE BEZ WYJATKU
═══════════════════════════════════════════════════════════

ZADEN typ kontaktu nie moze zostac w wynikowym opisie. Aplikacja na portalu
odbywa sie wylacznie przez przycisk "Aplikuj" — wszelkie zewnetrzne kanaly
kontaktu z pracodawca sa dla nas zakazane i MUSZA byc usuniete z tresci.

ZAKAZANE typy kontaktu (USUN cale zdanie / cala linijke <li> z nimi):

1. EMAIL — KAZDY adres mailowy:
   - info@firma.ch, biuro@firma.pl, recruitment@icareer24.com,
     hr@example.com, kontakt@..., aplikacje@..., job@..., mail@...
   - Cokolwiek pasuje do wzorca XXXX@YYYY.ZZ — usun cale zdanie z tym mailem.

2. NUMER TELEFONU — KAZDY numer:
   - +41 61 415 19 57, +48 571 381 734, 600 100 200, 022 123 45 67
   - Telefony szwajcarskie (+41), polskie (+48), niemieckie (+49) i inne
   - Numery 6-15 cyfr w jakimkolwiek formacie (z kreskami, spacjami, kropkami)
   - Usun cale zdanie z numerem.

3. WHATSAPP / SMS / TELEGRAM / VIBER:
   - "WhatsApp: +41...", "SMS na nr...", "Napisz na WhatsApp",
   - "Telegram: @user", "Viber:", linki wa.me/, t.me/

4. INSTRUKCJE APLIKACJI ZEWNETRZNEJ — zdania typu:
   - "Aplikuj wysylajac maila", "Aplikuj na adres",
   - "Wyslij CV na adres mailowy", "Wyslij CV na nasz mail",
   - "Skontaktuj sie pod numerem", "Zglos sie telefonicznie",
   - "Osoby zainteresowane prosimy o wysylanie swoich aplikacji na adres...",
   - "Aplikuj przez formularz na naszej stronie",
   - "Wejdz na strone X i wypelnij formularz",
   - "W razie szczegolowych pytan prosimy o kontakt: ..."

5. LINKI DO POBRANIA i URL ZEWNETRZNE:
   - "do pobrania tutaj", "kliknij tutaj", "pobierz formularz na stronie",
   - https://... do innych portali, "wiecej informacji na stronie X"

6. ZACHETY DO KONTAKTU TELEFONICZNEGO:
   - "Zadzwon", "Skontaktuj sie z nami pod numerem",
   - "Mozesz nas zlapac pod numerem..."

CO ZACHOWUJESZ (NIE traktuj jako kontakt):
- Wymagania jezykowe ("CV w jezyku niemieckim", "po niemiecku")
- Klauzula RODO bez konkretnego kontaktu

PRZYKLADY (BAD -> GOOD):

  BAD:  "<li>Osoby zainteresowane prosimy o wysylanie swoich aplikacji na adres
         mailowy: recruitment@icareer24.com. W treści lub tytule maila proszę
         podać stanowisko, jakiego aplikacja dotyczy.</li>
         <li>W razie szczegółowych pytań prosimy o kontakt: +48 571 381 734.</li>"
  GOOD: (cale dwie linijki USUNIETE — nic nie zostawiaj)

  BAD:  "<p>Prześlij CV w języku niemieckim wraz z klauzulą RODO. Aplikuj
         wysyłając maila z dokumentami na info@rol-jobhliwa.ch.
         Tel: +41 61 415 19 57. WhatsApp: +41 79 123 45 67.</p>"
  GOOD: "<p>Prześlij CV w języku niemieckim wraz z klauzulą RODO.</p>"

  BAD:  "<p>Wiecej informacji na stronie www.firma.ch lub pisz na info@firma.ch</p>"
  GOOD: (caly paragraph USUNIETY)

KONTROLA SAMODZIELNA opisu — zanim zwrocisz translated_description, sprawdz:
- Czy widzisz znak "@" gdziekolwiek? Jezeli tak — USUN cala linijke/zdanie z nim.
- Czy widzisz "+41", "+48", "+49" lub jakikolwiek ciag 7+ cyfr? Jezeli tak — USUN.
- Czy widzisz "WhatsApp", "SMS", "Telegram", "Viber"? Jezeli tak — USUN linijke.
- Czy widzisz "https://", "www."? Jezeli tak (oprocz nazw firm) — USUN.
- Czy widzisz "Aplikuj wysylajac", "Wyslij CV na", "Skontaktuj sie pod"? USUN.
"""


# ── AI call ───────────────────────────────────────────────────────────


async def _call_translation_ai(title: str, company: str, description: str, job_id: str | None = None) -> dict | None:
    """Call OpenAI with translation prompt. Returns parsed dict or None."""
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, skipping job translation")
        return None

    prompt = JOB_TRANSLATION_PROMPT.format(
        title=title,
        company=company,
        description=description[:5000],
    )

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-5.4-nano",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Jestes profesjonalnym tlumaczem specjalizujacym sie "
                        "w tlumaczeniu ofert pracy z niemieckiego, francuskiego "
                        "i wloskiego na polski. Odpowiadasz wylacznie czystym JSON."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_completion_tokens=2000,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty AI response for job translation")
            return None

        # Track tokens
        try:
            from app.services.ai_usage import track_usage
            if response.usage:
                track_usage(
                    service="translation",
                    model=response.model or "gpt-4o-mini",
                    prompt_tokens=response.usage.prompt_tokens,
                    completion_tokens=response.usage.completion_tokens,
                    job_id=job_id,
                )
        except Exception as e:
            logger.error(f"track_usage failed: {e}")

        return json.loads(content)

    except ImportError:
        logger.error("openai package not installed")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI translation response: {e}")
        return None
    except Exception as e:
        logger.error(f"AI job translation error: {e}")
        return None


# ── Post-process sanitizers (safety net for AI output) ──────────────


# Lista miast / kantonów / nazw lokacyjnych do usuwania z tytułu
_LOCATION_TOKENS = (
    # Niemieckie nazwy
    "zurich", "zürich", "bern", "basel", "luzern", "zug", "geneve", "genf",
    "wallis", "schwyz", "thurgau", "aarau", "sursee", "wädenswil", "wadenswil",
    "reichenburg", "andermatt", "lachen", "solothurn", "fribourg", "neuchatel",
    "valais", "vaud", "ticino", "graubunden", "uri", "obwalden", "nidwalden",
    "glarus", "appenzell", "schaffhausen", "jura", "st-gallen", "st gallen",
    "saint-gallen",
    # Polskie nazwy
    "zurych", "berno", "bazylea", "lucerna", "genewa",
)

# Master pattern: cała pensja + jednostki + dodatki (CHF...Brutto/Godzina + Euro/Netto/Dzień/Diety)
_RE_SALARY_CHUNK = re.compile(
    r"\s*[-–|/+,]?\s*"
    r"(?:\d{1,4}[,.\d]*\s*[-–]\s*)?\d{1,4}[,.\d]*\s*"
    r"(?:CHF|Euro|EUR|Eu)\b"
    r"(?:\s*(?:[/-]|\+)\s*\w+)*"  # /Brutto, /Godzina, -Netto itp
    r"(?:\s*\+\s*\d[,.\d]*\s*(?:CHF|Euro|EUR|Eu)\b(?:\s*(?:[/-]|\+)\s*\w+)*)?",  # + Euro/Netto/Dzień
    re.IGNORECASE,
)

# Range bez waluty: "4200–4900" — ryzykowne, więc tylko gdy poprzedzony separatorem |/–
_RE_NUMBER_RANGE = re.compile(r"\s*[|–-]\s*\d{3,5}(?:\s*[-–]\s*\d{3,5})?\s*(?=[|–-]|$)", re.IGNORECASE)

# Pojedyncze osamotnione słowa-śmieci po stripie pensji
_RE_SOLO_TRASH = re.compile(
    r"\s*[-–|/+,]?\s*\b("
    r"brutto|netto|godz\w*|dnia|dzie[nń]\w*|diet\w*|"
    r"dzienn[aey]|dziennie|dziennej|"
    r"darmow[aey]|zaraz|lub"
    r")\b\.?\s*",
    re.IGNORECASE,
)

# "/h" alone (po pensji godzinowej)
_RE_SLASH_H = re.compile(r"\s*[/]\s*h\b\s*", re.IGNORECASE)

# Pozostałe wzorce
_TITLE_TRASH_PATTERNS = [
    # "od zaraz", "praca od zaraz", "start od zaraz"
    (r"\s*[-–|/]?\s*(praca\s+)?(start\s+)?od\s+zaraz\b\s*", " "),
    # Szwajcarska umowa o pracę
    (r"\s*[-–|/]?\s*szwajcarska\s+umowa(\s+o\s+prac[ęe])?\s*", " "),
    # Zakwaterowanie / darmowe X
    (r"\s*[-–|/]?\s*zakwaterowani[ae]\s*", " "),
    (r"\s*[-–|/]?\s*darmow[aey]\s+(mieszkani[ae]|posiłk[iy]|zakwaterowani[ae])\s*", " "),
    # Wysokie zarobki / Stałe zatrudnienie / Stała praca
    (r"\s*[-–|/]?\s*wysokie\s+zarobki\s*", " "),
    (r"\s*[-–|/]?\s*stał[ae]\s+(praca|zatrudnienie)\s*", " "),
    # Pełny etat / Część etatu
    (r"\s*[-–|/]?\s*(pełny\s+etat|cz[ęe]ść\s+etatu)\s*", " "),
    # Dieta dzienna / dieta dnia (bez liczby)
    (r"\s*[-–|/+]?\s*\+?\s*diet[ay]\s+(dziennn?[aey]|dnia)\s*", " "),
    # Dobry/wymagany niemiecki, i auto, z prawem jazdy
    (r"\s*[-–|/,]?\s*(dobry|wymagany|wymagana)\s+(niemiecki|niemcza)\s*", " "),
    (r"\s*[-–|/,]?\s*i\s+auto\b\s*", " "),
    (r"\s*[-–|/,]?\s*z\s+prawem\s+jazdy\b\s*", " "),
    # "j.niem" / "j. niemiecki" / "j.ang" — fragmenty wymagań językowych
    (r"\s*[-–|/,]?\s*j\.\s*\w+\b\s*", " "),
    (r"\s*[-–|/,]?\s*\bang(?:ielski)?\b\s*", " "),
    # "bez certyfikatów"
    (r"\s*[-–|/,]?\s*bez\s+certyfikat\w*\s*", " "),
    # "(m/w/d)" "(w/m/d)" "(m/k)" "(/-ka)" "/-ka"
    (r"\s*\((m/w/d|w/m/d|m/k|k/m|/-ka)\)\s*", " "),
    (r"\s*/-ka\s*", " "),
    # EFZ / EBA / "100%"
    (r"\s+\b(EFZ|EBA)\b\s*", " "),
    (r"\s*\b\d{2,3}\s*%\b\s*", " "),
    # "Cała Szwajcaria" / "Inne lokalizacje" / "Szwajcaria" same / "do Szwajcarii"
    (r"\s*[-–|/]?\s*ca[łl][aej]?\s+szwajcari[ai]\s*", " "),
    (r"\s*[-–|/]?\s*inn[aey]\s+lokalizacj[ae]\s*", " "),
    (r"\s*[-–|/]?\s*\bdo\s+szwajcarii\b\s*", " "),
    (r"\s*[-–|/]?\s*\bszwajcari[ai]\b\s*", " "),
]


def _clean_title(title: str) -> str:
    """Aggressive title cleanup — strip locations, salaries, modes, etc."""
    if not title:
        return title

    t = title

    # Pętla: aplikuj wszystkie reguły aż do braku zmian (max 3 iteracje dla bezpieczeństwa)
    for _ in range(3):
        before = t

        # 1. Pensja (CHF/Euro + jednostki + dodatki)
        t = _RE_SALARY_CHUNK.sub(" ", t)

        # 2. Pozostałe trash patterns
        for pat, repl in _TITLE_TRASH_PATTERNS:
            t = re.sub(pat, repl, t, flags=re.IGNORECASE)

        # 3. Lokalizacje
        for loc in _LOCATION_TOKENS:
            t = re.sub(rf"\s*[-–|/,]?\s*\b{re.escape(loc)}\b\s*", " ", t, flags=re.IGNORECASE)

        # 4. Osamotnione słowa-śmieci pozostałe po stripie pensji (Brutto, Godzina, Diety...)
        t = _RE_SOLO_TRASH.sub(" ", t)

        # 4b. "/h" po pensji godzinowej
        t = _RE_SLASH_H.sub(" ", t)

        # 5. Range liczbowy bez waluty (np. "| 4200–4900 |")
        t = _RE_NUMBER_RANGE.sub(" ", t)

        # 6. Cleanup wielokrotnych przecinków/separatorów: ", , ," -> ","
        t = re.sub(r"(\s*[,;]\s*){2,}", ", ", t)

        if t == before:
            break

    # Prefix ilości: "2x Malarz" -> "Malarz (2 stanowiska)"
    m = re.match(r"^\s*(\d+)\s*x\s+(.+)$", t, flags=re.IGNORECASE)
    if m:
        count = m.group(1)
        rest = m.group(2).strip()
        t = f"{rest} ({count} stanowiska)"

    # Trailing/leading separatory: "- foo - " -> "foo"
    t = re.sub(r"^\s*[-–|/,+]+\s*", "", t)
    t = re.sub(r"\s*[-–|/,+]+\s*$", "", t)

    # Trailing dangling "od" (zostaje po stripie pensji "od XX CHF")
    t = re.sub(r"\s+\bod\b\s*$", "", t, flags=re.IGNORECASE)

    # Zwijaj wielokrotne separatory w środku: " - | - " -> " - "
    t = re.sub(r"\s*[-–|]\s*[-–|]+\s*", " - ", t)
    # Zwijaj wielokrotne spacje
    t = re.sub(r"\s+", " ", t).strip()

    return t[:80]


def _clean_description(html: str) -> str:
    """Light cleanup — only fix duplicated <h3>X</h3><p>X:</p> patterns."""
    if not html:
        return html

    # Usuń duplikat: <h3>Wymagania</h3><p>Wymagania:</p>, <h3>Oferujemy</h3><p>Nasza oferta:</p>, etc.
    # Pasuje do <p>...:</p> bezposrednio po <h3>X</h3>, jeśli paragraf zawiera label-style tekst (krótki, kończy się : lub .)
    html = re.sub(
        r"(<h3>(?:Opis stanowiska|Wymagania|Oferujemy)</h3>)"
        r"\s*<p>[^<]{1,80}[:.]\s*</p>",
        r"\1",
        html,
        flags=re.IGNORECASE,
    )

    # Usuń puste <ul></ul>, <ol></ol>, <p></p>, <h3></h3>
    html = re.sub(r"<(ul|ol)>\s*</\1>", "", html)
    html = re.sub(r"<p>\s*</p>", "", html)
    html = re.sub(r"<h3>\s*</h3>", "", html)

    return html.strip()


# ── Validation ────────────────────────────────────────────────────────


_EMAIL_VALIDATE_RE = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z]{2,}$")


def _validate_translation(data: dict) -> dict:
    """Validate translation response fields and run post-process sanitizers."""
    translated_title = data.get("translated_title", "")
    if not isinstance(translated_title, str):
        translated_title = ""
    translated_title = translated_title.strip()[:255]

    translated_description = data.get("translated_description", "")
    if not isinstance(translated_description, str):
        translated_description = ""
    translated_description = translated_description.strip()
    translated_description = _clean_description(translated_description)

    # Walidacja contact_email — musi byc poprawnym formatem email
    contact_email = data.get("contact_email")
    if contact_email and isinstance(contact_email, str):
        contact_email = contact_email.strip().lower()[:255]
        if not _EMAIL_VALIDATE_RE.match(contact_email):
            contact_email = None
    else:
        contact_email = None

    return {
        "translated_title": translated_title,
        "translated_description": translated_description,
        "contact_email": contact_email,
    }


# ── Single job translation pipeline ──────────────────────────────────


async def translate_single_job(job_id: str, session_factory=None) -> bool:
    """Full translation pipeline for a single scraped job.

    Status flow: pending -> processing -> completed/failed
    On success: overwrites title/description with Polish, activates job,
    ensures extraction_status='pending' so extraction picks it up next.

    Returns True if translation succeeded, False otherwise.
    """
    _sf = session_factory or async_session
    async with _sf() as db:
        result = await db.execute(
            select(JobOffer).where(JobOffer.id == job_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            logger.error(f"JobOffer {job_id} not found for translation")
            return False

        if not job.description:
            logger.warning(f"JobOffer {job_id} has no description, marking translation failed")
            job.translation_status = "failed"
            await db.commit()
            return False

        # Check max attempts
        if job.translation_attempts >= MAX_TRANSLATION_ATTEMPTS:
            logger.warning(f"JobOffer {job_id} exceeded max translation attempts")
            job.translation_status = "failed"
            await db.commit()
            return False

        # Mark as processing
        job.translation_status = "processing"
        job.translation_attempts += 1
        await db.commit()

        # Strip HTML for AI input
        from app.core.sanitize import strip_all_html
        raw_text = strip_all_html(job.description)

        # Call AI
        ai_data = await _call_translation_ai(
            title=job.title,
            company="",
            description=raw_text,
            job_id=str(job.id),
        )

        if ai_data is None:
            job.translation_status = "pending" if job.translation_attempts < MAX_TRANSLATION_ATTEMPTS else "failed"
            await db.commit()
            await log_activity(
                "job_translation_failed",
                f"AI translation failed for: {job.title[:80]} (attempt {job.translation_attempts})",
                entity_type="job_offer",
                entity_id=job.id,
                session_factory=_sf,
            )
            return False

        # Validate
        validated = _validate_translation(ai_data)

        if not validated["translated_title"] and not validated["translated_description"]:
            job.translation_status = "pending" if job.translation_attempts < MAX_TRANSLATION_ATTEMPTS else "failed"
            await db.commit()
            return False

        # Apply translation
        from app.core.sanitize import sanitize_html

        if validated["translated_title"]:
            job.title = validated["translated_title"]
        if validated["translated_description"]:
            job.description = sanitize_html(validated["translated_description"])

        # Email aplikacyjny: jezeli AI znalazl, ustaw apply_via='email'.
        # W przeciwnym wypadku zostawiamy 'external_url' (ustawione przy scrape) z linkiem do oryginalu.
        if validated["contact_email"]:
            job.contact_email = validated["contact_email"]
            job.apply_via = "email"

        # Activate job (scraped jobs: brak expires_at — dopiero pracodawca recznie dodajacy ofcjalnie ustawia 30 dni)
        now = datetime.now(timezone.utc)
        job.status = "active"
        job.published_at = now
        job.expires_at = None

        # Mark translation complete, ensure extraction picks it up
        job.translation_status = "completed"
        job.extraction_status = "pending"

        await db.commit()

        await log_activity(
            "job_translation_completed",
            f"AI translation completed for: {job.title[:80]}",
            entity_type="job_offer",
            entity_id=job.id,
            session_factory=_sf,
        )
        logger.info(f"Job translation completed for {job_id}")
        return True


# ── Batch processor ──────────────────────────────────────────────────


async def process_pending_job_translations(session_factory=None) -> int:
    """Process pending job translations in batches.

    Called by scheduler every 2 minutes. Processes up to 10 at a time.
    Only picks up scraped jobs (source_name IS NOT NULL).
    Returns number of successfully processed jobs.
    """
    _sf = session_factory or async_session
    async with _sf() as db:
        result = await db.execute(
            select(JobOffer.id)
            .where(
                JobOffer.translation_status == "pending",
                JobOffer.source_name.isnot(None),
                JobOffer.description.isnot(None),
                JobOffer.translation_attempts < MAX_TRANSLATION_ATTEMPTS,
            )
            .order_by(JobOffer.created_at.asc())
            .limit(10)
        )
        pending_ids = [row[0] for row in result.all()]

    if not pending_ids:
        return 0

    logger.info(f"Processing {len(pending_ids)} pending job translation(s)")
    success_count = 0
    for job_id in pending_ids:
        if await translate_single_job(job_id, session_factory=_sf):
            success_count += 1

    logger.info(f"Job translation batch: {success_count}/{len(pending_ids)} succeeded")
    return success_count
