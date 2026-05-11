"""Globalny licznik wszystkich kiedykolwiek dodanych ofert pracy.

Counter monotonicznie rosnacy - nie zmniejsza sie nawet gdy oferta zostanie usunieta.
Przechowywany w tabeli system_settings pod kluczem 'total_jobs_lifetime'.
"""
from sqlalchemy import select, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.system_setting import SystemSetting
from app.models.job_offer import JobOffer

COUNTER_KEY = "total_jobs_lifetime"


async def _ensure_initialized(db: AsyncSession) -> SystemSetting:
    """Zwroc wiersz licznika; jezeli nie istnieje - zainicjuj na aktualny COUNT(*) z job_offers."""
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == COUNTER_KEY)
    )
    setting = result.scalar_one_or_none()
    if setting is not None:
        return setting

    current_count_res = await db.execute(select(func.count(JobOffer.id)))
    current_count = int(current_count_res.scalar_one() or 0)
    setting = SystemSetting(
        key=COUNTER_KEY,
        value=str(current_count),
        value_type="integer",
        description="Liczba wszystkich kiedykolwiek dodanych ofert pracy (monotoniczny).",
    )
    db.add(setting)
    await db.flush()
    return setting


async def increment_lifetime_jobs_counter(db: AsyncSession, by: int = 1) -> None:
    """Atomowo inkrementuj licznik o `by`. Bezpieczne wzgledem rownoleglych insertow."""
    await _ensure_initialized(db)
    await db.execute(
        text(
            "UPDATE system_settings "
            "SET value = CAST(CAST(value AS INTEGER) + :by AS TEXT) "
            "WHERE key = :key"
        ),
        {"by": by, "key": COUNTER_KEY},
    )


async def get_lifetime_jobs_total(db: AsyncSession) -> int:
    setting = await _ensure_initialized(db)
    try:
        return int(setting.value)
    except (TypeError, ValueError):
        return 0
