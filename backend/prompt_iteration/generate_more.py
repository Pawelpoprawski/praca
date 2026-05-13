"""Dogeneruj 16 brakujacych CV pojedynczo (po 1 na request)."""
import asyncio
import os
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / ".env")

MISSING_PROFILES = [
    "opiekunka 24h Pflege, 8 lat w Niemczech, niemiecki B2, paszport UE, ZAPISANE PO POLSKU",
    "pielegniarka po SRK-Anerkennung dla CH, 12 lat doswiadczenia, niemiecki C1, CV po niemiecku (Lebenslauf)",
    "fizjoterapeuta po polskiej licencji, 6 lat, niemiecki A2, angielski B2, CV po polsku",
    "babysitter studentka pedagogiki, 1 rok doswiadczenia, niemiecki podstawowy, CV po polsku, krotkie 8 linii",
    "kierowca C+E Polak, 14 lat w transporcie miedzynarodowym, niemiecki A2, prawo jazdy C+E + ADR, CV po polsku",
    "LKW Fahrer Polak w Niemczech, 18 lat, niemiecki B1, CV po niemiecku, ma wlasny pojazd",
    "kierowca autobusu wiek 58, kat D, 25 lat doswiadczenia, tylko polski, CV po polsku, krotkie",
    "inzynier mechanik z dyplomem PW, 9 lat w Bosch Polska, niemiecki B2, angielski C1, certyfikat EUR ING, CV po polsku",
    "lekarz kardiolog ze specjalizacja PL, 6 lat doswiadczenia, niemiecki C1, w trakcie SRK-Anerkennung, CV po polsku",
    "dentysta z wlasna praktyka 10 lat, niemiecki B1, angielski B2, CV po polsku",
    "technik dentystyczny 14 lat w laboratoriach, tylko polski, CV minimalne",
    "farmaceuta 13 lat w aptece, niemiecki B1, CV po polsku, krotkie",
    "Marketing Manager B2B SaaS, 10 lat w UK (Londyn), angielski C2, polski native, niemiecki A2, CV po angielsku",
    "Office Manager 6 lat, polski + angielski B2, niemiecki A1, CV po polsku",
    "Account Manager IT, 5 lat w polskim software house, polski + angielski C1, CV po polsku",
    "Recruiter HR Tech, 8 lat, angielski C1, niemiecki B1, CV po polsku",
]


SYSTEM_PROMPT = """Jestes generatorem realistycznych CV polskich kandydatow szukajacych pracy w Szwajcarii.

Zwracaj WYLACZNIE pelny tekst JEDNEGO CV (10-25 linii). Bez markdown, bez JSON, bez komentarzy.
Tylko sam tekst CV od imienia do informacji koncowych.

Cechy:
- Polskie imie i nazwisko, realistyczne dane kontaktowe
- Zwarta struktura: imie, kontakt, profil/cel, doswiadczenie, wyksztalcenie, jezyki, inne
- Realistyczne firmy
- Polskie diakrytyki zachowane (chyba ze instrukcja mowi inaczej)"""


async def generate_one(role_desc: str) -> str:
    from openai import AsyncOpenAI
    import httpx

    http_client = httpx.AsyncClient(verify=False, timeout=120)
    client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"], http_client=http_client)

    response = await client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Wygeneruj JEDNO CV: {role_desc}"},
        ],
        max_completion_tokens=1500,
    )
    return (response.choices[0].message.content or "").strip()


async def main():
    out_dir = Path(__file__).parent
    existing = sorted(out_dir.glob("cv_*.txt"))
    start_num = len(existing) + 1
    print(f"Mamy {len(existing)} CV, dorzucam {len(MISSING_PROFILES)} (od cv_{start_num:02d})", flush=True)

    for i, role in enumerate(MISSING_PROFILES):
        num = start_num + i
        print(f"  [{num}] {role[:50]}...", flush=True)
        cv = await generate_one(role)
        if cv and len(cv) > 100:
            (out_dir / f"cv_{num:02d}.txt").write_text(cv + "\n", encoding="utf-8")


if __name__ == "__main__":
    asyncio.run(main())
