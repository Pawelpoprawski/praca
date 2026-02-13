"""Extract text and structured info from CV files (PDF and DOCX)."""
import re
import logging

logger = logging.getLogger(__name__)

# Language keywords to detect in CVs (Polish/German/English/French names)
LANGUAGE_KEYWORDS = {
    "polski": "pl", "polish": "pl", "polnisch": "pl", "polonais": "pl",
    "niemiecki": "de", "german": "de", "deutsch": "de", "allemand": "de",
    "angielski": "en", "english": "en", "englisch": "en", "anglais": "en",
    "francuski": "fr", "french": "fr", "französisch": "fr", "français": "fr",
    "włoski": "it", "italian": "it", "italienisch": "it", "italien": "it",
    "hiszpański": "es", "spanish": "es", "spanisch": "es", "espagnol": "es",
    "portugalski": "pt", "portuguese": "pt", "portugiesisch": "pt", "portugais": "pt",
    "rosyjski": "ru", "russian": "ru", "russisch": "ru", "russe": "ru",
    "ukraiński": "uk", "ukrainian": "uk", "ukrainisch": "uk", "ukrainien": "uk",
    "czeski": "cs", "czech": "cs", "tschechisch": "cs", "tchèque": "cs",
    "holenderski": "nl", "dutch": "nl", "niederländisch": "nl", "néerlandais": "nl",
}

LEVEL_PATTERN = re.compile(
    r"(A1|A2|B1|B2|C1|C2|native|ojczysty|muttersprachler|natif|biegły|zaawansowany|średniozaawansowany|podstawowy|fluent|advanced|intermediate|beginner)",
    re.IGNORECASE,
)


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text from a PDF file using PyPDF2."""
    try:
        from PyPDF2 import PdfReader
        reader = PdfReader(file_path)
        pages_text = []
        for page in reader.pages:
            text = page.extract_text()
            if text:
                pages_text.append(text)
        return "\n".join(pages_text)
    except Exception as e:
        logger.error(f"PDF extraction failed for {file_path}: {e}")
        return ""


def extract_text_from_docx(file_path: str) -> str:
    """Extract text from a DOCX file using python-docx."""
    try:
        from docx import Document
        doc = Document(file_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        logger.error(f"DOCX extraction failed for {file_path}: {e}")
        return ""


def extract_text(file_path: str, mime_type: str) -> str:
    """Extract text from a file based on its mime type."""
    if mime_type == "application/pdf":
        return extract_text_from_pdf(file_path)
    elif mime_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        return extract_text_from_docx(file_path)
    return ""


def _extract_email(text: str) -> str | None:
    """Extract email address from text."""
    match = re.search(r"[\w.+-]+@[\w.-]+\.\w+", text)
    return match.group(0) if match else None


def _extract_phone(text: str) -> str | None:
    """Extract phone number from text."""
    match = re.search(r"(\+?\d[\d\s\-()]{7,}\d)", text)
    if match:
        phone = match.group(0).strip()
        # Clean up - remove excessive whitespace
        phone = re.sub(r"\s+", " ", phone)
        return phone
    return None


def _extract_name(text: str) -> str | None:
    """Extract name - heuristic: first non-empty line that looks like a name."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:5]:  # Check first 5 lines
        # Skip lines that look like headers/sections
        if any(kw in line.lower() for kw in [
            "cv", "curriculum", "resume", "lebenslauf",
            "tel", "email", "phone", "adres", "@",
        ]):
            continue
        # Name should be 2-5 words, all starting with uppercase
        words = line.split()
        if 2 <= len(words) <= 5 and all(w[0].isupper() for w in words if w):
            return line
    return None


def _extract_languages(text: str) -> list[dict]:
    """Extract language skills from text."""
    languages = []
    seen = set()
    text_lower = text.lower()

    for keyword, lang_code in LANGUAGE_KEYWORDS.items():
        if keyword in text_lower and lang_code not in seen:
            seen.add(lang_code)
            # Try to find level near the keyword
            idx = text_lower.index(keyword)
            context = text[max(0, idx - 20):idx + len(keyword) + 40]
            level_match = LEVEL_PATTERN.search(context)
            level = level_match.group(0) if level_match else None

            # Normalize level
            if level:
                level_upper = level.upper()
                if level_upper in ("A1", "A2", "B1", "B2", "C1", "C2"):
                    level = level_upper
                elif level.lower() in ("native", "ojczysty", "muttersprachler", "natif", "biegły"):
                    level = "C2"
                elif level.lower() in ("zaawansowany", "fluent", "advanced"):
                    level = "C1"
                elif level.lower() in ("średniozaawansowany", "intermediate"):
                    level = "B2"
                elif level.lower() in ("podstawowy", "beginner"):
                    level = "A2"

            languages.append({"lang": lang_code, "level": level or "unknown"})

    return languages


def extract_info_from_text(text: str) -> dict:
    """Extract structured information from CV text."""
    return {
        "name": _extract_name(text),
        "email": _extract_email(text),
        "phone": _extract_phone(text),
        "languages": _extract_languages(text),
    }


# --- CV Analysis (strengths / weaknesses / tips) ---

_EXPERIENCE_KEYWORDS = [
    "doświadczenie", "experience", "erfahrung", "staż", "praktyka",
    "praca", "stanowisko", "position", "employment", "berufserfahrung",
]

_EDUCATION_KEYWORDS = [
    "wykształcenie", "education", "ausbildung", "studia", "uniwersytet",
    "university", "hochschule", "dyplom", "licencjat", "magister",
    "inżynier", "doktor", "matura", "szkoła", "certyfikat", "certificate",
]

_SWISS_LANGUAGES = {"de", "fr", "it", "en"}

_WORK_PERMIT_KEYWORDS = [
    "pozwolenie na pracę", "work permit", "arbeitsbewilligung",
    "permit b", "permit c", "permit g", "permit l",
    "aufenthaltsbewilligung", "zezwolenie",
]


def analyze_cv_text(text: str, extracted_info: dict) -> dict:
    """Analyze CV text and return strengths, weaknesses, tips, and score.

    Returns dict with keys: strengths, weaknesses, tips, score (10-100).
    All strings are in Polish.
    """
    strengths: list[str] = []
    weaknesses: list[str] = []
    tips: list[str] = []
    score = 50
    text_lower = text.lower()
    text_len = len(text.strip())

    # 1. Contact info
    has_email = bool(extracted_info.get("email"))
    has_phone = bool(extracted_info.get("phone"))
    has_name = bool(extracted_info.get("name"))

    if has_email and has_phone:
        strengths.append("Dane kontaktowe (email + telefon) są podane")
        score += 5
    elif has_email or has_phone:
        tips.append("Dodaj brakujące dane kontaktowe (email lub telefon)")
        score += 2
    else:
        weaknesses.append("Brak danych kontaktowych (email, telefon)")
        score -= 10

    if has_name:
        score += 3
    else:
        weaknesses.append("Nie udało się odczytać imienia i nazwiska")
        score -= 5

    # 2. CV length
    if text_len > 3000:
        strengths.append("CV ma odpowiednią długość i zawiera szczegóły")
        score += 5
    elif text_len > 1000:
        tips.append("CV mogłoby zawierać więcej szczegółów dotyczących doświadczenia")
    else:
        weaknesses.append("CV jest bardzo krótkie — rozważ dodanie szczegółów")
        score -= 10

    # 3. Languages (Swiss-relevant: DE, FR, IT, EN)
    langs = extracted_info.get("languages") or []
    lang_codes = {l["lang"] for l in langs}
    swiss_langs = lang_codes & _SWISS_LANGUAGES

    if len(swiss_langs) >= 2:
        strengths.append(f"Znajomość {len(swiss_langs)} języków ważnych w Szwajcarii")
        score += 10
    elif len(swiss_langs) == 1:
        tips.append("Znajomość dodatkowego języka szwajcarskiego (DE/FR/IT/EN) zwiększy Twoje szanse")
        score += 3
    else:
        weaknesses.append("Brak informacji o znajomości języków Szwajcarii (DE/FR/IT/EN)")
        score -= 5

    if langs:
        score += 3
    else:
        weaknesses.append("CV nie zawiera sekcji z językami")
        score -= 5

    # 4. Experience keywords
    exp_count = sum(1 for kw in _EXPERIENCE_KEYWORDS if kw in text_lower)
    if exp_count >= 3:
        strengths.append("Doświadczenie zawodowe jest dobrze opisane")
        score += 8
    elif exp_count >= 1:
        tips.append("Rozwiń opis doświadczenia zawodowego — dodaj konkretne osiągnięcia")
        score += 2
    else:
        weaknesses.append("Brak widocznej sekcji z doświadczeniem zawodowym")
        score -= 8

    # 5. Education keywords
    edu_count = sum(1 for kw in _EDUCATION_KEYWORDS if kw in text_lower)
    if edu_count >= 2:
        strengths.append("Wykształcenie jest udokumentowane")
        score += 5
    elif edu_count >= 1:
        tips.append("Dodaj więcej szczegółów o wykształceniu (uczelnia, kierunek, daty)")
        score += 2
    else:
        weaknesses.append("Brak informacji o wykształceniu")
        score -= 5

    # 6. Work permit mention
    has_permit_mention = any(kw in text_lower for kw in _WORK_PERMIT_KEYWORDS)
    if has_permit_mention:
        strengths.append("CV zawiera informację o pozwoleniu na pracę")
        score += 5
    else:
        tips.append("Rozważ dodanie informacji o pozwoleniu na pracę w Szwajcarii")

    # Clamp score
    score = max(10, min(100, score))

    return {
        "strengths": strengths,
        "weaknesses": weaknesses,
        "tips": tips,
        "score": score,
    }
