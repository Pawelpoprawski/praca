"""Wyczysc baze i sciagnij po N RANDOMOWYCH ofert z kazdego sourca.

Uzycie: python run_full_test.py [LIMIT]  (domyslnie 5)
"""
import asyncio
import random
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

LIMIT = int(sys.argv[1]) if len(sys.argv) > 1 else 5


async def main():
    from sqlalchemy import text
    from app.database import async_session
    from app.services.job_processor import process_jobs
    from app.services.sources.jobspl import fetch_jobspl
    from app.services.sources.fachpraca import fetch_fachpraca
    from app.services.sources.roljob import fetch_roljob
    from app.services.sources.adecco import fetch_adecco

    print("=== KASOWANIE OFERT ===")
    async with async_session() as db:
        r = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        existing = {row[0] for row in r.all()}
    for tbl in ["external_applications", "applications", "job_offer_views",
                "job_offer_saves", "saved_jobs", "job_views"]:
        if tbl in existing:
            async with async_session() as db:
                await db.execute(text(f"DELETE FROM {tbl}"))
                await db.commit()
    async with async_session() as db:
        await db.execute(text("DELETE FROM job_offers"))
        await db.commit()
        cnt = (await db.execute(text("SELECT COUNT(*) FROM job_offers"))).scalar()
        print(f"  oferty po wyczyszczeniu: {cnt}")

    print(f"\n=== SCRAPING ({LIMIT} RANDOM z kazdego) ===")
    random.seed()

    for name, fetch_fn in [
        ("JOBSPL", fetch_jobspl),
        ("FACHPRACA", fetch_fachpraca),
        ("ROLJOB", fetch_roljob),
        ("ADECCO", fetch_adecco),
    ]:
        print(f"\n--- {name} ---")
        try:
            all_jobs = await fetch_fn()
            print(f"  feed total: {len(all_jobs)}")
            if not all_jobs:
                print("  brak ofert w feedzie")
                continue
            sample = random.sample(all_jobs, min(LIMIT, len(all_jobs)))
            print(f"  losowane: {len(sample)}")
            async with async_session() as db:
                result = await process_jobs(sample, db, limit=None)
                print(f"  added={result.added}, errors={result.errors}")
        except Exception as e:
            print(f"  BLAD: {e}")

    async with async_session() as db:
        total = (await db.execute(text("SELECT COUNT(*) FROM job_offers"))).scalar()
        print(f"\n=== TOTAL: {total} ofert w bazie ===")


if __name__ == "__main__":
    asyncio.run(main())
