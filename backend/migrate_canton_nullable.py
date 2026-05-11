"""SQLite: zmien job_offers.canton na NULL-ABLE."""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))


async def main():
    from sqlalchemy import text
    from app.database import async_session

    async with async_session() as db:
        # Sprawdz schemat
        r = await db.execute(text("PRAGMA table_info(job_offers)"))
        canton_info = next((row for row in r.all() if row[1] == "canton"), None)
        if canton_info and canton_info[3] == 0:
            print("canton juz NULL-able, nic do roboty")
            return

        print("Wykonuje SQLite ALTER (rebuild tabeli)...")
        # SQLite od 3.35 obsluguje DROP NOT NULL, ale tylko z osobnym ALTER
        # Najpewniej: rebuild kopiujac dane
        await db.execute(text("PRAGMA foreign_keys=OFF"))
        await db.execute(text("BEGIN"))
        try:
            # Wez schemat oryginalnej tabeli, podmien NOT NULL na NULL dla canton
            r = await db.execute(text(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='job_offers'"
            ))
            sql = r.scalar()
            print("oryginalny schemat:")
            print(sql)
            new_sql = sql.replace(
                'canton VARCHAR(50) NOT NULL', 'canton VARCHAR(50)'
            ).replace(
                '"canton" VARCHAR(50) NOT NULL', '"canton" VARCHAR(50)'
            ).replace(
                'job_offers', 'job_offers_new', 1
            )
            print("\nnowy schemat:")
            print(new_sql)

            await db.execute(text(new_sql))
            await db.execute(text(
                "INSERT INTO job_offers_new SELECT * FROM job_offers"
            ))
            await db.execute(text("DROP TABLE job_offers"))
            await db.execute(text("ALTER TABLE job_offers_new RENAME TO job_offers"))

            # Odbuduj indeksy
            r = await db.execute(text(
                "SELECT sql FROM sqlite_master WHERE type='index' AND tbl_name='job_offers' AND sql IS NOT NULL"
            ))
            for (idx_sql,) in r.all():
                try:
                    await db.execute(text(idx_sql))
                except Exception as e:
                    print(f"  index skip: {e}")

            await db.commit()
            print("\n✓ migracja OK")
        except Exception as e:
            await db.rollback()
            print(f"\n✗ blad: {e}")
            raise
        finally:
            await db.execute(text("PRAGMA foreign_keys=ON"))


if __name__ == "__main__":
    asyncio.run(main())
