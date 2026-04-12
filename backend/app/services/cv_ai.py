"""AI-powered CV analysis using OpenAI GPT-4."""
import json
import logging

from app.config import get_settings

logger = logging.getLogger(__name__)

CV_ANALYSIS_PROMPT = """Jesteś ekspertem HR specjalizującym się w rynku pracy w Szwajcarii, ze szczególnym uwzględnieniem polskich pracowników.

Przeanalizuj poniższe CV i zwróć wynik w formacie JSON (bez markdown code blocks, czysty JSON).

Ocena powinna być szczegółowa i konkretna. Bierz pod uwagę specyfikę rynku szwajcarskiego:
- Ważność znajomości języków (niemiecki, francuski, włoski, angielski)
- Znaczenie pozwoleń na pracę (Permit B, C, G, L)
- Standardy CV w Szwajcarii (zdjęcie, dane osobowe, referencje)
- Specyficzne wymagania branżowe

Zwróć JSON z następującymi polami:
{
  "overall_score": <liczba 1-10>,
  "summary": "<ogólna ocena CV w 2-3 zdaniach po polsku>",
  "strengths": ["<mocna strona 1>", "<mocna strona 2>", ...],
  "improvements": ["<co poprawić 1 - z konkretną sugestią>", "<co poprawić 2>", ...],
  "missing": ["<czego brakuje 1>", "<czego brakuje 2>", ...],
  "tips": ["<porada na rynek szwajcarski 1>", "<porada 2>", ...]
}

Wymagania:
- overall_score: obiektywna ocena od 1 (bardzo słabe) do 10 (doskonałe)
- strengths: minimum 2 pozycje, maksimum 6
- improvements: minimum 2 pozycje, maksimum 6, każda z konkretną sugestią
- missing: minimum 1 pozycja, maksimum 5
- tips: minimum 2 porady, maksimum 5, specyficzne dla rynku szwajcarskiego
- Wszystkie teksty po polsku

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
                    "content": "Jesteś ekspertem HR. Odpowiadasz wyłącznie czystym JSON bez żadnego formatowania markdown.",
                },
                {
                    "role": "user",
                    "content": CV_ANALYSIS_PROMPT + cv_text[:8000],
                },
            ],
            temperature=0.3,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        if not content:
            logger.error("Empty response from OpenAI")
            return None

        # Strip possible markdown code block wrapping
        content = content.strip()
        if content.startswith("```"):
            # Remove ```json and ``` wrappers
            lines = content.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            content = "\n".join(lines)

        analysis = json.loads(content)

        # Validate required fields
        required = ["overall_score", "summary", "strengths", "improvements", "missing", "tips"]
        for field in required:
            if field not in analysis:
                logger.error(f"Missing field in AI response: {field}")
                return None

        # Clamp score
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
