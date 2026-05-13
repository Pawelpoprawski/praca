"""Generator 50 zroznicowanych CV Polakow szukajacych pracy w Szwajcarii.

Uzywa gpt-5.4-mini, 10 batchy po 5 CV (mniejsze batche = pewniejszy zwrot tablicy).
"""
import asyncio
import json
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

BATCHES = [
    "5 CV gastronomia (kucharz, kelner, sommelier, cukiernik, barman) - 2 PL, 2 DE (Lebenslauf), 1 EN. Mix poziomow doswiadczenia.",
    "5 CV budownictwo (cieslarz, murarz, spawacz, elektryk, hydraulik) - 3 PL, 2 DE. Mix doswiadczenia 3-25 lat. Niektorzy z prawem jazdy C+E.",
    "5 CV opieka (opiekun seniora 24h Pflege, pielegniarka, fizjoterapeuta, babysitter, opiekun dzieci) - 3 PL, 2 DE.",
    "5 CV IT (frontend dev, backend dev, DevOps/SRE, QA, data engineer) - 2 PL, 1 DE, 2 EN. Mix junior/senior.",
    "5 CV transport + inzynieria (kierowca C+E, LKW Fahrer DE, autobus, mechanik, projektant konstrukcji) - 3 PL, 2 DE.",
    "5 CV hotelarstwo (recepcjonista, hotel manager, housekeeping, concierge, F&B manager) - 3 PL, 1 DE, 1 EN.",
    "5 CV zdrowie (lekarz, dentysta, technik dentystyczny, farmaceuta, ratownik medyczny) - 4 PL, 1 DE.",
    "5 CV sprzedaz/marketing/admin (sprzedawca, marketing manager, office manager, account manager, recruiter) - 3 PL, 1 EN, 1 DE.",
    "5 CV ROZNYCH BLEDOW: literowki, brak diakrytykow, stan cywilny/religia, PESEL, hobbies bombastyczne (15+ pozycji), CV bardzo krotkie (3 linijki).",
    "5 CV EDGE CASES: job-hopper (8 prac po 3 mc), senior 60+, osoba z luka 5-letnia, mama 3 dzieci po urlopie wychowawczym, wlasna firma (przedsiebiorca).",
]

SYSTEM_PROMPT = """Jestes generatorem realistycznych CV polskich kandydatow szukajacych pracy w Szwajcarii.

OBOWIAZKOWY FORMAT ODPOWIEDZI:
{"cvs": ["<CALY tekst CV 1>", "<CALY tekst CV 2>", "<CALY tekst CV 3>", "<CALY tekst CV 4>", "<CALY tekst CV 5>"]}

ZASADY:
- ZAWSZE zwracaj TABLICE 5 osobnych stringow w polu "cvs"
- Kazdy element tablicy to JEDNO calosciowe CV (zaczyna sie od imienia/nagloku, konczy informacjami dodatkowymi)
- NIE laczy wielu CV w jeden string!
- Roznoroduj nazwiska, branze, poziomy doswiadczenia, jezyki
- Polskie imiona (Kowalski, Nowak, Wojcik, Mazur, Kwiatkowski, Pietrzak, Adamczyk, Lewandowski itp.)
- Czesc po polsku, czesc po niemiecku (Lebenslauf), czesc po angielsku
- 10-25 linii kazde CV (zwiezle, nie nadmiernie dlugie)
- Realistyczne firmy (np. Skanska, Roche, Allegro, Marriott, Bauunternehmen Schmidt, BauTeam, Promedica24)
- Niektore CV maja miec: literowki, brak polskich diakrytykow (Doswiadczenie zamiast Doświadczenie), info "stan cywilny", "religia", PESEL itd. — ALE NIE WSZYSTKIE
- Mix prawo jazdy / certyfikaty branzowe / paszport UE
- Bez markdown, bez komentarzy poza JSON."""


async def generate_batch(batch_num: int, instruction: str) -> list[str]:
    from openai import AsyncOpenAI
    import httpx

    http_client = httpx.AsyncClient(verify=False, timeout=300)
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], http_client=http_client)

    print(f"[Batch {batch_num}/10] {instruction[:60]}...", flush=True)
    response = await client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Wygeneruj 5 CV: {instruction}\n\nPamietaj: tablica 5 osobnych stringow w polu 'cvs', NIE laczy w jeden string."},
        ],
        max_completion_tokens=10000,
        response_format={"type": "json_object"},
    )
    content = response.choices[0].message.content
    if not content:
        return []
    try:
        data = json.loads(content)
    except json.JSONDecodeError as e:
        print(f"  ! JSON error: {e}", flush=True)
        return []
    cvs = data.get("cvs", [])
    print(f"  -> otrzymano {len(cvs)} CV", flush=True)
    return [cv for cv in cvs if isinstance(cv, str) and len(cv) > 100]


async def main():
    out_dir = Path(__file__).parent
    all_cvs: list[str] = []
    for i, instruction in enumerate(BATCHES, start=1):
        cvs = await generate_batch(i, instruction)
        all_cvs.extend(cvs)
        if len(all_cvs) >= 50:
            break

    print(f"\nTotal generated: {len(all_cvs)} CVs", flush=True)
    for i, cv_text in enumerate(all_cvs[:50], start=1):
        path = out_dir / f"cv_{i:02d}.txt"
        path.write_text(cv_text.strip() + "\n", encoding="utf-8")
    print(f"Saved {min(len(all_cvs), 50)} CV files", flush=True)


if __name__ == "__main__":
    asyncio.run(main())
