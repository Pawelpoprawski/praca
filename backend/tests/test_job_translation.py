"""Tests for the job translation pipeline (DE/FR/IT -> Polish)."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from tests.conftest import TestSession

from app.models.job_offer import JobOffer
from app.models.employer_profile import EmployerProfile
from app.services.job_translation_service import (
    translate_single_job,
    process_pending_job_translations,
    _validate_translation,
    MAX_TRANSLATION_ATTEMPTS,
)


# ── Sample AI response ────────────────────────────────────────────────

MOCK_TRANSLATION_RESPONSE = {
    "translated_title": "Spawacz MIG/MAG",
    "translated_description": (
        "<h3>Opis stanowiska</h3><p>Spawanie konstrukcji stalowych.</p>"
        "<h3>Wymagania</h3><ul><li>Doswiadczenie min. 3 lata.</li></ul>"
    ),
}


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def employer_profile(db_session):
    """Create a minimal employer profile for testing."""
    from app.models.user import User
    from app.core.security import hash_password

    user = User(
        id=str(uuid.uuid4()),
        email=f"test-trans-{uuid.uuid4().hex[:6]}@test.pl",
        password_hash=hash_password("test123"),
        role="employer",
        first_name="Test",
        last_name="Employer",
        is_active=True,
    )
    db_session.add(user)
    await db_session.flush()

    profile = EmployerProfile(
        id=str(uuid.uuid4()),
        user_id=user.id,
        company_name="Test Translation Co",
        company_slug=f"test-trans-{uuid.uuid4().hex[:6]}",
        is_verified=True,
    )
    db_session.add(profile)
    await db_session.commit()
    return profile


@pytest_asyncio.fixture
async def scraped_job_for_translation(db_session, employer_profile):
    """Create a scraped job with translation_status=pending."""
    job = JobOffer(
        id=str(uuid.uuid4()),
        employer_id=employer_profile.id,
        title="Schweisser MIG/MAG 100% (m/w/d)",
        description="<p>Wir suchen einen erfahrenen Schweisser für unser Team in Zürich.</p>",
        canton="zurich",
        city="Zurich",
        contract_type="full_time",
        salary_type="monthly",
        is_remote="no",
        status="pending",
        source_name="JOBSPL",
        source_id="jobspl-trans-001",
        translation_status="pending",
        extraction_status="pending",
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest_asyncio.fixture
async def scraped_job_no_description(db_session, employer_profile):
    """Create a scraped job without description."""
    job = JobOffer(
        id=str(uuid.uuid4()),
        employer_id=employer_profile.id,
        title="Empty Scraped Job",
        description="",
        canton="zurich",
        contract_type="full_time",
        salary_type="monthly",
        is_remote="no",
        status="pending",
        source_name="JOBSPL",
        source_id="jobspl-empty-001",
        translation_status="pending",
    )
    db_session.add(job)
    await db_session.commit()
    return job


# ── Tests: _validate_translation ─────────────────────────────────────


class TestValidateTranslation:
    """Test validation of AI translation response."""

    def test_validates_all_fields(self):
        result = _validate_translation(MOCK_TRANSLATION_RESPONSE)
        assert result["translated_title"] == "Spawacz MIG/MAG"
        assert "Opis stanowiska" in result["translated_description"]

    def test_handles_empty_input(self):
        result = _validate_translation({})
        assert result["translated_title"] == ""
        assert result["translated_description"] == ""

    def test_truncates_long_title(self):
        result = _validate_translation({
            "translated_title": "A" * 300,
            "translated_description": "desc",
        })
        assert len(result["translated_title"]) == 255

    def test_handles_non_string_values(self):
        result = _validate_translation({
            "translated_title": 123,
            "translated_description": None,
        })
        assert result["translated_title"] == ""
        assert result["translated_description"] == ""


# ── Tests: translate_single_job ──────────────────────────────────────


class TestTranslateSingleJob:
    """Test the full translation pipeline for a single job."""

    @patch("app.services.job_translation_service._call_translation_ai")
    async def test_successful_translation(self, mock_ai, scraped_job_for_translation):
        mock_ai.return_value = MOCK_TRANSLATION_RESPONSE

        result = await translate_single_job(scraped_job_for_translation.id, session_factory=TestSession)
        assert result is True

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == scraped_job_for_translation.id)
            )
            job = row.scalar_one()
            assert job.translation_status == "completed"
            assert job.title == "Spawacz MIG/MAG"
            assert "Opis stanowiska" in job.description
            # Job should be activated
            assert job.status == "active"
            assert job.published_at is not None
            assert job.expires_at is not None
            # Extraction should be pending so next step picks it up
            assert job.extraction_status == "pending"

    @patch("app.services.job_translation_service._call_translation_ai")
    async def test_failed_translation_retries(self, mock_ai, scraped_job_for_translation):
        mock_ai.return_value = None

        result = await translate_single_job(scraped_job_for_translation.id, session_factory=TestSession)
        assert result is False

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == scraped_job_for_translation.id)
            )
            job = row.scalar_one()
            # Should be back to pending for retry (attempt 1 < MAX)
            assert job.translation_status == "pending"
            assert job.translation_attempts == 1

    @patch("app.services.job_translation_service._call_translation_ai")
    async def test_max_attempts_marks_failed(self, mock_ai, scraped_job_for_translation):
        mock_ai.return_value = None

        # Exhaust all attempts
        for _ in range(MAX_TRANSLATION_ATTEMPTS):
            await translate_single_job(scraped_job_for_translation.id, session_factory=TestSession)

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == scraped_job_for_translation.id)
            )
            job = row.scalar_one()
            assert job.translation_status == "failed"
            assert job.translation_attempts == MAX_TRANSLATION_ATTEMPTS

    async def test_nonexistent_id_returns_false(self):
        result = await translate_single_job("nonexistent-id", session_factory=TestSession)
        assert result is False

    async def test_no_description_marks_failed(self, scraped_job_no_description):
        result = await translate_single_job(scraped_job_no_description.id, session_factory=TestSession)
        assert result is False

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == scraped_job_no_description.id)
            )
            job = row.scalar_one()
            assert job.translation_status == "failed"


# ── Tests: process_pending_job_translations (batch) ──────────────────


class TestProcessPendingTranslationBatch:
    """Test the batch translation scheduler job."""

    @patch("app.services.job_translation_service._call_translation_ai")
    async def test_processes_pending_jobs(self, mock_ai, scraped_job_for_translation):
        mock_ai.return_value = MOCK_TRANSLATION_RESPONSE

        count = await process_pending_job_translations(session_factory=TestSession)
        assert count == 1

    async def test_no_pending_returns_zero(self):
        count = await process_pending_job_translations(session_factory=TestSession)
        assert count == 0

    @patch("app.services.job_translation_service._call_translation_ai")
    async def test_skips_manual_jobs(self, mock_ai, db_session, employer_profile):
        """Manual jobs (no source_name) should not be picked up for translation."""
        mock_ai.return_value = MOCK_TRANSLATION_RESPONSE

        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=employer_profile.id,
            title="Manual Job",
            description="<p>Opis manualny.</p>",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            status="active",
            source_name=None,
            translation_status="none",
        )
        db_session.add(job)
        await db_session.commit()

        count = await process_pending_job_translations(session_factory=TestSession)
        assert count == 0  # manual jobs should be skipped


# ── Tests: JobOffer model defaults ───────────────────────────────────


class TestJobOfferTranslationDefaults:
    """Test translation column defaults on JobOffer model."""

    async def test_defaults(self, db_session, employer_profile):
        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=employer_profile.id,
            title="Defaults Test",
            description="Testing default values for translation columns.",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
        )
        db_session.add(job)
        await db_session.commit()

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == job.id)
            )
            loaded = row.scalar_one()
            assert loaded.translation_status == "none"
            assert loaded.translation_attempts == 0
