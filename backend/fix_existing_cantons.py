"""Uzupelnij canton dla istniejacych ofert na podstawie city."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))


async def main():
    from sqlalchemy import select
    from app.database import async_session
    from app.models.job_offer import JobOffer
    from app.services.job_processor import _resolve_canton_from_city

    async with async_session() as db:
        r = await db.execute(
            select(JobOffer).where(JobOffer.canton.is_(None), JobOffer.city.isnot(None))
        )
        fixed = 0
        for j in r.scalars():
            c = _resolve_canton_from_city(j.city)
            if c:
                print(f"  {j.city:20} -> {c}")
                j.canton = c
                fixed += 1
        await db.commit()
        print(f"Naprawiono {fixed} ofert (canton z city)")


if __name__ == "__main__":
    asyncio.run(main())
