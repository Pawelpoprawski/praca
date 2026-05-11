"""Wymus translation + extraction dla wszystkich oczekujacych ofert."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


async def main():
    from sqlalchemy import select, text
    from app.database import async_session
    from app.models.job_offer import JobOffer
    from app.services.job_translation_service import process_pending_job_translations
    from app.services.job_extraction_service import process_pending_job_extractions

    print("=== TRANSLATION (batches po 10) ===")
    total_t = 0
    for i in range(50):
        n = await process_pending_job_translations()
        print(f"  batch {i+1}: {n} ok")
        total_t += n
        if n == 0:
            break
    print(f"  TOTAL translated: {total_t}")

    print("\n=== EXTRACTION (batches po 10) ===")
    total_e = 0
    for i in range(50):
        n = await process_pending_job_extractions()
        print(f"  batch {i+1}: {n} ok")
        total_e += n
        if n == 0:
            break
    print(f"  TOTAL extracted: {total_e}")

    print("\n=== STAN OFERT ===")
    async with async_session() as db:
        rows = await db.execute(text(
            "SELECT translation_status, extraction_status, status, COUNT(*) "
            "FROM job_offers GROUP BY 1,2,3"
        ))
        for r in rows.all():
            print(f"  trans={r[0]} extr={r[1]} status={r[2]}: {r[3]}")

        print("\n=== TYTULY + LOKALIZACJA ===")
        rows = await db.execute(text(
            "SELECT title, city, canton, source_name FROM job_offers ORDER BY source_name, title LIMIT 50"
        ))
        for r in rows.all():
            t = (r[0] or "")[:55]
            city = r[1] or "-"
            canton = r[2] or "-"
            src = r[3] or "?"
            print(f"  [{src:9}] {t:55} | {city:20} | {canton}")


if __name__ == "__main__":
    asyncio.run(main())
