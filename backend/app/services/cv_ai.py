"""AI-powered CV analysis using OpenAI GPT-4."""
import json
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

CV_ANALYSIS_PROMPT = """Jesteś doświadczonym ekspertem HR i rekruterem specjalizującym się w rynku pracy w Szwajcarii, ze szczególnym uwzględnieniem polskich pracowników aplikujących na pozycje w Szwajcarii.

Twoim zadaniem jest przeanalizować CV w DWÓCH OSOBNYCH KATEGORIACH i zwrócić wynik w formacie JSON (bez markdown, czysty JSON).

=== KROK 0 (OBOWIĄZKOWY): WYKRYJ JĘZYK CV ===
ZANIM zaczniesz oceniać cokolwiek innego — sprawdź w JAKIM JĘZYKU napisane jest CV (analizując sekcje, nagłówki, opisy doświadczenia, NIE tylko nazwy własne).

Akceptowalne języki dla rynku pracy w Szwajcarii:
- **niemiecki (de)** — DACH region (Zurych, Berno, Bazylea, większość kantonów) — najsilniejsza preferencja
- **francuski (fr)** — Romandie (Genewa, Vaud, Neuchâtel, Jura, Fryburg)
- **włoski (it)** — Ticino

Jeśli CV jest w JAKIMKOLWIEK innym języku (polski, angielski, ukraiński, rosyjski, hiszpański itp.) — to KRYTYCZNY PROBLEM. Aplikacje w nieprawidłowym języku są w 95% przypadków odrzucane na pierwszym etapie selekcji, nawet jeśli kandydat jest świetny merytorycznie.

W polu `critical_issues` ZAWSZE umieść TEN problem JAKO PIERWSZY wpis. Komunikat MUSI być praktyczny i targetowany do regionu — kandydat sam wybiera gdzie chce pracować. Użyj tego dokładnego szablonu (zachowaj formatowanie i pogrubienia w treści, nie używaj markdown):

"Twoje CV jest napisane w języku <NAZWA_JĘZYKA>, a najważniejsze dla aplikacji w Szwajcarii to język CV dopasowany do regionu pracy:
• Jeśli celujesz w niemieckojęzyczną część Szwajcarii (Zurych, Berno, Bazylea, Lucerna, St. Gallen — ok. 65% kraju i większość ofert) — CV MUSI być po niemiecku.
• Jeśli celujesz w Romandie (Genewa, Lozanna, Neuchâtel, Fryburg, Jura) — CV MUSI być po francusku.
• Jeśli celujesz w Ticino (Lugano, Bellinzona) — CV powinno być po włosku.
CV w innym języku zostanie odrzucone już na pierwszym sicie selekcji u 90%+ pracodawców. Przetłumacz CV na język docelowego regionu PRZED wysyłką."

Jeśli CV jest w DE/FR/IT — pole `critical_issues` pozostaw jako pustą listę `[]` (chyba że wykryjesz inny krytyczny problem, np. CV jest pusty, zawiera tylko jedno zdanie, lub zawiera dane fałszywe/sprzeczne).

=== KATEGORIA 1: STRUKTURA I ZAWARTOŚĆ CV ===
Oceń jak CV jest skonstruowane — jego forma, układ, sekcje, gramatyka, dobór informacji.

Bierz pod uwagę:
- Standardy CV w Szwajcarii: zdjęcie profesjonalne (zawsze!), dane kontaktowe na górze, jasne sekcje, chronologia odwrotna, 1-2 strony max
- Czy są wszystkie kluczowe sekcje: dane osobowe, doświadczenie, wykształcenie, języki, umiejętności
- Czy NIE ma zbędnych informacji (PESEL, data urodzenia może być, ale stan cywilny i religia są niepotrzebne)
- Czy opisy doświadczenia są konkretne (osiągnięcia, liczby) czy puste ("byłem odpowiedzialny za...")
- Gramatyka, ortografia, stylistyka
- Spójność formatowania, czytelność
- Czy są referencje lub wzmianka o nich

W tej kategorii oceń:
- works_well — konkretne elementy, które działają dobrze i należy je ZOSTAWIĆ
- needs_fixing — co należy POPRAWIĆ lub USUNĄĆ (z konkretną sugestią CO zamiast tego)
- to_add — czego BRAKUJE i co warto DODAĆ (z uzasadnieniem dlaczego)

=== KATEGORIA 2: DOPASOWANIE DO RYNKU SZWAJCARSKIEGO ===
Oceń jak kandydat (jego kompetencje, doświadczenie, sytuacja) wpasowuje się w realia rynku pracy w Szwajcarii.

DUŻE PLUSY (advantages) — szukaj ich aktywnie:
- Znajomość niemieckiego (od B1 wzwyż) — otwiera 65% ofert
- Znajomość francuskiego (Romandie: Genewa, Vaud, Neuchâtel, Jura, Fryburg)
- Znajomość włoskiego (Ticino)
- Doświadczenie za granicą (nawet w Polsce w międzynarodowej firmie liczy się)
- Wcześniejsza praca w DACH (Niemcy, Austria) — bardzo zbliżona kultura pracy
- Pozwolenie na pracę (Permit B/C/G/L) lub paszport UE/EFTA
- Prawo jazdy + samochód (zwłaszcza dla budowlanki, transportu, opieki)
- Certyfikaty branżowe (np. EU-Schweisspass dla spawaczy, dyplomy uznawane w CH)
- Doświadczenie 5+ lat w branżach deficytowych (budownictwo, gastronomia, opieka, IT, inżynieria)
- Zdolność do relokacji / gotowość do pracy w systemie tygodniowym

GAPS (concerns) — czerwone flagi dla rynku CH:
- Brak jakiegokolwiek języka niemieckiego/francuskiego/angielskiego
- Brak doświadczenia poza Polską (utrudnia, ale nie blokuje)
- Brak pozwolenia na pracę i brak paszportu UE
- Krótkie staże (skakanie co 6 miesięcy między pracodawcami — w CH źle widziane)
- Brak konkretów (brak nazw firm, dat, miast)
- Wiek pracownika — Szwajcaria często ma górną granicę 50-55 lat w niektórych branżach (delikatnie wspomnieć tylko jeśli widoczne i istotne)

Dla każdego advantage i concern PODAJ KONKRET z CV (np. "Znajomość niemieckiego na poziomie B2 — kluczowy atut" zamiast ogólnego "znasz języki").

Actions — KONKRETNE kroki, co kandydat powinien zrobić ZANIM aplikuje (kurs językowy, certyfikat, uzupełnienie sekcji).

=== FORMAT ODPOWIEDZI ===
Zwróć JSON dokładnie z poniższą strukturą:
{
  "overall_score": <liczba 1-10 — średnia z obu kategorii; jeśli krytyczny problem językowy → maks. 4>,
  "summary": "<2-3 zdania po polsku: ogólny werdykt + 1 najważniejsza rzecz do poprawy>",
  "critical_issues": ["<problem krytyczny 1 — np. zły język CV>", ...],
  "structure": {
    "score": <liczba 1-10 dla samej formy CV>,
    "works_well": ["<konkret 1>", "<konkret 2>", ...],
    "needs_fixing": ["<co poprawić/usunąć — z sugestią 1>", "<2>", ...],
    "to_add": ["<co dodać — z uzasadnieniem 1>", "<2>", ...]
  },
  "swiss_fit": {
    "score": <liczba 1-10 dla dopasowania do rynku CH>,
    "advantages": ["<konkretny atut 1>", "<2>", ...],
    "concerns": ["<konkretny gap 1>", "<2>", ...],
    "actions": ["<konkretny krok 1>", "<2>", ...]
  },
  "tips": ["<1-3 uniwersalnych, krótkich porad — opcjonalnie>"]
}

WYMAGANIA:
- critical_issues: 0-3 pozycji. ZAWSZE pierwsze: zły język CV (PL/EN/inny niż DE/FR/IT). Tylko PRAWDZIWIE blokujące problemy — nie używaj dla drobnych spraw
- structure.works_well: 2-5 pozycji
- structure.needs_fixing: 2-6 pozycji
- structure.to_add: 1-5 pozycji
- swiss_fit.advantages: 1-5 pozycji (jeśli brak — pusta lista)
- swiss_fit.concerns: 1-5 pozycji
- swiss_fit.actions: 1-4 pozycji
- tips: 0-3 pozycji (krótkie, ogólne)
- Wszystko po polsku
- KAŻDA pozycja zawiera KONKRET z CV (nie ogólniki typu "popraw doświadczenie")
- Bądź szczery — jeśli CV jest słabe, nie wybielaj. Jeśli silne — nie udawaj że źle.
- Jeśli CV jest w złym języku — `summary` MUSI zaczynać się od wzmianki o problemie językowym

TEKST CV:
"""

CV_EXTRACTION_PROMPT = """Przeanalizuj poniższy tekst CV i wyciągnij z niego strukturalne dane. Zwróć wynik jako JSON (bez markdown code blocks).

Zwróć JSON z następującymi polami:
{
  "full_name": "<imię i nazwisko lub null>",
  "email": "<email lub null>",
  "phone": "<numer telefonu lub null>",
  "experience": [
    {
      "position": "<stanowisko>",
      "company": "<firma>",
      "period": "<okres np. 2020-2023>",
      "description": "<krótki opis lub null>"
    }
  ],
  "education": [
    {
      "degree": "<tytuł/stopień>",
      "institution": "<uczelnia/szkoła>",
      "year": "<rok ukończenia lub null>"
    }
  ],
  "skills": ["<umiejętność 1>", "<umiejętność 2>", ...],
  "languages": [
    {"language": "<język>", "level": "<poziom np. B2, C1, native>"}
  ],
  "driving_license": "<kategoria np. B, C lub null>",
  "location": "<miejsce zamieszkania lub null>"
}

Jeśli jakiegoś pola nie da się wyciągnąć, ustaw null lub pustą tablicę.

TEKST CV:
"""


async def analyze_cv_with_ai(cv_text: str) -> dict | None:
    """Analyze CV text using OpenAI GPT-4 and return structured analysis.

    Returns dict with keys: overall_score, summary, strengths, improvements, missing, tips.
    Returns None if AI analysis fails.
    """
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, falling back to basic analysis")
        return None

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś ekspertem HR specjalizującym się w rynku pracy w Szwajcarii. Odpowiadasz wyłącznie czystym JSON.",
                },
                {
                    "role": "user",
                    "content": CV_ANALYSIS_PROMPT + cv_text[:8000],
                },
            ],
            temperature=0.4,
            max_tokens=2500,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty response from OpenAI")
            return None

        analysis = json.loads(content.strip())

        # Required top-level fields
        for field in ("overall_score", "summary"):
            if field not in analysis:
                logger.error(f"Missing required field in AI response: {field}")
                return None

        # Validate new two-category structure (preferred)
        has_structure = isinstance(analysis.get("structure"), dict)
        has_swiss_fit = isinstance(analysis.get("swiss_fit"), dict)

        if has_structure:
            s = analysis["structure"]
            s.setdefault("score", analysis["overall_score"])
            s.setdefault("works_well", [])
            s.setdefault("needs_fixing", [])
            s.setdefault("to_add", [])
            s["score"] = max(1, min(10, int(s["score"])))

        if has_swiss_fit:
            sf = analysis["swiss_fit"]
            sf.setdefault("score", analysis["overall_score"])
            sf.setdefault("advantages", [])
            sf.setdefault("concerns", [])
            sf.setdefault("actions", [])
            sf["score"] = max(1, min(10, int(sf["score"])))

        # Backfill legacy fields from new structure so old UI/clients still work
        if has_structure or has_swiss_fit:
            s = analysis.get("structure", {}) or {}
            sf = analysis.get("swiss_fit", {}) or {}
            analysis.setdefault("strengths", (s.get("works_well") or []) + (sf.get("advantages") or []))
            analysis.setdefault("improvements", s.get("needs_fixing") or [])
            analysis.setdefault("missing", (s.get("to_add") or []) + (sf.get("concerns") or []))
            analysis.setdefault("tips", (analysis.get("tips") or []) + (sf.get("actions") or []))
        else:
            # Legacy-only response — ensure legacy fields exist
            for field in ("strengths", "improvements", "missing", "tips"):
                analysis.setdefault(field, [])

        # Clamp overall score
        analysis["overall_score"] = max(1, min(10, int(analysis["overall_score"])))

        return analysis

    except ImportError:
        logger.error("openai package not installed")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return None
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return None


async def extract_cv_data_with_ai(cv_text: str) -> dict | None:
    """Extract structured data from CV text using OpenAI.

    DEPRECATED: Use cv_extraction_service.extract_cv_data_unified() instead.
    This function is no longer called from routers - extraction now happens
    in background via scheduler using the unified extraction service.

    Returns dict with keys: full_name, email, phone, experience, education, skills, languages, driving_license, location.
    Returns None if extraction fails.
    """
    settings = get_settings()

    if not settings.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not configured, using basic extraction")
        return None

    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

        response = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": "Jesteś asystentem HR. Odpowiadasz wyłącznie czystym JSON bez żadnego formatowania markdown.",
                },
                {
                    "role": "user",
                    "content": CV_EXTRACTION_PROMPT + cv_text[:8000],
                },
            ],
            temperature=0.1,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty response from OpenAI extraction")
            return None

        content = content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        return json.loads(content)

    except ImportError:
        logger.error("openai package not installed")
        return None
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI extraction response: {e}")
        return None
    except Exception as e:
        logger.error(f"OpenAI extraction error: {e}")
        return None


def fallback_analysis(cv_text: str) -> dict:
    """Basic keyword-based CV analysis when OpenAI is not available."""
    from app.services.cv_extractor import extract_info_from_text, analyze_cv_text

    extracted = extract_info_from_text(cv_text)
    analysis = analyze_cv_text(cv_text, extracted)

    # Map from old format (score 10-100) to new format (1-10)
    score_10 = max(1, min(10, round(analysis["score"] / 10)))

    return {
        "overall_score": score_10,
        "summary": f"Analiza CV wykazała wynik {score_10}/10. "
                   f"Znaleziono {len(analysis['strengths'])} mocnych stron i {len(analysis['weaknesses'])} obszarów do poprawy.",
        "strengths": analysis["strengths"] or ["CV zawiera podstawowe informacje"],
        "improvements": analysis["weaknesses"] or ["Rozbuduj opis doświadczenia zawodowego"],
        "missing": [
            tip for tip in analysis["tips"]
            if any(kw in tip.lower() for kw in ["dodaj", "brak", "rozważ"])
        ] or ["Dodaj informacje o pozwoleniu na pracę w Szwajcarii"],
        "tips": [
            "Dostosuj CV do standardów szwajcarskich - dodaj zdjęcie profesjonalne",
            "Podaj informacje o pozwoleniu na pracę (Permit B/C/G/L)",
            "Wymień znajomość języków z poziomami (A1-C2)",
        ],
    }
