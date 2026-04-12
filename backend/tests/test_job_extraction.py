"""Tests for the job metadata extraction pipeline."""
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from tests.conftest import TestSession

from app.models.job_offer import JobOffer
from app.models.employer_profile import EmployerProfile
from app.services.job_extraction_service import (
    map_extraction_to_job,
    extract_single_job,
    process_pending_job_extractions,
    _validate_extraction,
    EXTRACTION_VERSION,
    MAX_EXTRACTION_ATTEMPTS,
)


# ── Sample AI response (metadata only, no clean_title/clean_description) ──

MOCK_AI_RESPONSE = {
    "category_slug": "budownictwo",
    "seniority_level": "mid",
    "contract_type": "full_time",
    "is_remote": "no",
    "city": "Zurych",
    "canton_raw": "Zurich",
    "salary_min": 5000,
    "salary_max": 7000,
    "salary_type": "monthly",
    "pensum_min": 80,
    "pensum_max": 100,
    "experience_min": 3,
    "required_skills": ["spawanie MIG/MAG", "czytanie rysunkow technicznych"],
    "nice_to_have_skills": ["spawanie TIG"],
    "languages": [{"lang": "de", "level": "B1"}],
    "driving_license_required": True,
    "car_required": False,
    "work_permit_required": "B",
    "accommodation_provided": True,
    "shift_work": False,
    "keywords": "spawacz; spawanie; MIG; MAG; monter; budownictwo",
    "industry_tags": ["budownictwo", "metalurgia"],
}


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest_asyncio.fixture
async def employer_profile(db_session):
    """Create a minimal employer profile for testing."""
    from app.models.user import User
    from app.core.security import hash_password

    user = User(
        id=str(uuid.uuid4()),
        email=f"test-employer-{uuid.uuid4().hex[:6]}@test.pl",
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
        company_name="Test Company",
        company_slug=f"test-company-{uuid.uuid4().hex[:6]}",
        is_verified=True,
    )
    db_session.add(profile)
    await db_session.commit()
    return profile


@pytest_asyncio.fixture
async def scraped_job_for_extraction(db_session, employer_profile):
    """Create a scraped job already translated (active, translation_status=completed)."""
    job = JobOffer(
        id=str(uuid.uuid4()),
        employer_id=employer_profile.id,
        title="Spawacz MIG/MAG",
        description="<h3>Opis stanowiska</h3><p>Spawanie konstrukcji stalowych.</p>",
        canton="zurich",
        city="Zurich",
        contract_type="full_time",
        salary_type="monthly",
        is_remote="no",
        status="active",
        source_name="JOBSPL",
        source_id="jobspl-12345",
        extraction_status="pending",
        translation_status="completed",
        published_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest_asyncio.fixture
async def manual_job_pending(db_session, employer_profile):
    """Create a manual employer job with extraction_status=pending."""
    job = JobOffer(
        id=str(uuid.uuid4()),
        employer_id=employer_profile.id,
        title="Spawacz MIG/MAG",
        description="<h3>Opis</h3><p>Szukamy spawacza do pracy w Zurychu.</p>",
        canton="zurich",
        city="Zurich",
        contract_type="full_time",
        salary_type="monthly",
        is_remote="no",
        status="active",
        source_name=None,
        extraction_status="pending",
        translation_status="none",
        published_at=datetime.now(timezone.utc),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30),
    )
    db_session.add(job)
    await db_session.commit()
    return job


@pytest_asyncio.fixture
async def job_no_description(db_session, employer_profile):
    """Create a job without description."""
    job = JobOffer(
        id=str(uuid.uuid4()),
        employer_id=employer_profile.id,
        title="Empty Job",
        description="",
        canton="zurich",
        contract_type="full_time",
        salary_type="monthly",
        is_remote="no",
        status="active",
        extraction_status="pending",
    )
    db_session.add(job)
    await db_session.commit()
    return job


# ── Tests: _validate_extraction ──────────────────────────────────────


class TestValidateExtraction:
    """Test validation and normalization of AI response."""

    def test_validates_all_fields(self):
        result = _validate_extraction(MOCK_AI_RESPONSE)
        assert result["contract_type"] == "full_time"
        assert result["is_remote"] == "no"
        assert result["category_slug"] == "budownictwo"
        assert result["seniority_level"] == "mid"
        assert result["experience_min"] == 3
        assert result["salary_min"] == 5000
        assert result["salary_max"] == 7000
        assert result["pensum_min"] == 80
        assert result["pensum_max"] == 100
        assert len(result["required_skills"]) == 2
        assert len(result["nice_to_have_skills"]) == 1
        assert result["accommodation_provided"] is True
        assert result["shift_work"] is False
        assert len(result["languages"]) == 1
        assert result["industry_tags"] == ["budownictwo", "metalurgia"]

    def test_defaults_for_invalid_values(self):
        result = _validate_extraction({
            "contract_type": "invalid",
            "is_remote": "invalid",
            "category_slug": "invalid",
            "seniority_level": "invalid",
        })
        assert result["contract_type"] == "full_time"
        assert result["is_remote"] == "no"
        assert result["category_slug"] == "inne"
        assert result["seniority_level"] is None

    def test_clamps_experience_min(self):
        result = _validate_extraction({"experience_min": 100})
        assert result["experience_min"] == 50

        result = _validate_extraction({"experience_min": -5})
        assert result["experience_min"] == 0

    def test_filters_invalid_languages(self):
        result = _validate_extraction({
            "languages": [
                {"lang": "de", "level": "B1"},
                {"lang": "xx", "level": "B1"},
                {"lang": "fr", "level": "Z9"},
                "invalid_entry",
            ]
        })
        assert len(result["languages"]) == 1
        assert result["languages"][0]["lang"] == "de"

    def test_pensum_bounds(self):
        result = _validate_extraction({"pensum_min": 5, "pensum_max": 150})
        assert result["pensum_min"] is None
        assert result["pensum_max"] is None

    def test_handles_empty_dict(self):
        result = _validate_extraction({})
        assert result["contract_type"] == "full_time"
        assert result["required_skills"] == []
        assert result["nice_to_have_skills"] == []
        assert result["keywords"] == ""


# ── Tests: map_extraction_to_job ─────────────────────────────────────


class TestMapExtractionToJob:
    """Test mapping validated extraction data to JobOffer (metadata only)."""

    def test_preserves_title_description(self):
        """Extraction never modifies title/description (translation handles that)."""
        job = JobOffer(
            id=str(uuid.uuid4()),
            title="My Custom Title",
            description="My custom description",
        )
        data = _validate_extraction(MOCK_AI_RESPONSE)
        map_extraction_to_job(job, data)

        # Title and description should NOT be overwritten
        assert job.title == "My Custom Title"
        assert job.description == "My custom description"
        # But metadata should be filled
        assert job.skills == ["spawanie MIG/MAG", "czytanie rysunkow technicznych"]
        assert job.seniority_level == "mid"
        assert job.contract_type == "full_time"

    def test_sets_all_metadata_fields(self):
        job = JobOffer(id=str(uuid.uuid4()), title="Test", description="Test")
        data = _validate_extraction(MOCK_AI_RESPONSE)
        map_extraction_to_job(job, data)

        assert job.contract_type == "full_time"
        assert job.is_remote == "no"
        assert job.experience_min == 3
        assert job.driving_license_required is True
        assert job.car_required is False
        assert job.pensum_min == 80
        assert job.pensum_max == 100
        assert job.shift_work is False
        assert job.nice_to_have_skills == ["spawanie TIG"]
        assert job.industry_tags == ["budownictwo", "metalurgia"]
        assert "spawacz" in job.ai_keywords

    def test_stores_extracted_data(self):
        job = JobOffer(id=str(uuid.uuid4()), title="Test", description="Test")
        data = _validate_extraction(MOCK_AI_RESPONSE)
        map_extraction_to_job(job, data)

        assert job.extracted_data is not None
        assert job.extracted_data["category_slug"] == "budownictwo"


# ── Tests: extract_single_job ────────────────────────────────────────


class TestExtractSingleJob:
    """Test the full extraction pipeline for a single job."""

    @patch("app.services.job_extraction_service._call_extraction_ai")
    async def test_successful_scraped_extraction(self, mock_ai, scraped_job_for_extraction):
        mock_ai.return_value = MOCK_AI_RESPONSE

        result = await extract_single_job(scraped_job_for_extraction.id, session_factory=TestSession)
        assert result is True

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == scraped_job_for_extraction.id)
            )
            job = row.scalar_one()
            assert job.extraction_status == "completed"
            assert job.match_ready is True
            assert job.extraction_version == EXTRACTION_VERSION
            assert job.ai_extracted is True
            # Extraction does NOT change status (translation already activated it)
            assert job.status == "active"
            assert len(job.skills) == 2

    @patch("app.services.job_extraction_service._call_extraction_ai")
    async def test_successful_manual_extraction(self, mock_ai, manual_job_pending):
        mock_ai.return_value = MOCK_AI_RESPONSE

        result = await extract_single_job(manual_job_pending.id, session_factory=TestSession)
        assert result is True

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == manual_job_pending.id)
            )
            job = row.scalar_one()
            assert job.extraction_status == "completed"
            assert job.match_ready is True
            # Manual job keeps original title (extraction is metadata-only)
            assert job.title == "Spawacz MIG/MAG"
            assert job.status == "active"

    @patch("app.services.job_extraction_service._call_extraction_ai")
    async def test_failed_extraction_retries(self, mock_ai, scraped_job_for_extraction):
        mock_ai.return_value = None

        result = await extract_single_job(scraped_job_for_extraction.id, session_factory=TestSession)
        assert result is False

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == scraped_job_for_extraction.id)
            )
            job = row.scalar_one()
            # Should be back to pending for retry (attempt 1 < MAX)
            assert job.extraction_status == "pending"
            assert job.extraction_attempts == 1
            assert job.match_ready is False

    @patch("app.services.job_extraction_service._call_extraction_ai")
    async def test_max_attempts_marks_failed(self, mock_ai, scraped_job_for_extraction):
        mock_ai.return_value = None

        # Exhaust all attempts
        for _ in range(MAX_EXTRACTION_ATTEMPTS):
            await extract_single_job(scraped_job_for_extraction.id, session_factory=TestSession)

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == scraped_job_for_extraction.id)
            )
            job = row.scalar_one()
            assert job.extraction_status == "failed"
            assert job.extraction_attempts == MAX_EXTRACTION_ATTEMPTS

    async def test_no_description_marks_failed(self, job_no_description):
        result = await extract_single_job(job_no_description.id, session_factory=TestSession)
        assert result is False

        async with TestSession() as session:
            row = await session.execute(
                select(JobOffer).where(JobOffer.id == job_no_description.id)
            )
            job = row.scalar_one()
            assert job.extraction_status == "failed"

    async def test_nonexistent_id_returns_false(self):
        result = await extract_single_job("nonexistent-id", session_factory=TestSession)
        assert result is False


# ── Tests: process_pending_job_extractions (batch) ───────────────────


class TestProcessPendingBatch:
    """Test the batch extraction scheduler job."""

    @patch("app.services.job_extraction_service._call_extraction_ai")
    async def test_processes_pending_active_jobs(self, mock_ai, scraped_job_for_extraction):
        """Active jobs with extraction_status=pending should be processed."""
        mock_ai.return_value = MOCK_AI_RESPONSE

        count = await process_pending_job_extractions(session_factory=TestSession)
        assert count == 1

    async def test_no_pending_returns_zero(self):
        count = await process_pending_job_extractions(session_factory=TestSession)
        assert count == 0

    @patch("app.services.job_extraction_service._call_extraction_ai")
    async def test_skips_pending_status_jobs(self, mock_ai, db_session, employer_profile):
        """Jobs with status='pending' (not yet translated/activated) should be skipped."""
        mock_ai.return_value = MOCK_AI_RESPONSE

        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=employer_profile.id,
            title="Untranslated Job",
            description="Some German description.",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            status="pending",
            source_name="JOBSPL",
            source_id="batch-untranslated",
            extraction_status="pending",
            translation_status="pending",
        )
        db_session.add(job)
        await db_session.commit()

        count = await process_pending_job_extractions(session_factory=TestSession)
        assert count == 0  # should skip job with status='pending'

    @patch("app.services.job_extraction_service._call_extraction_ai")
    async def test_respects_batch_limit(self, mock_ai, db_session, employer_profile):
        """Should process at most 10 jobs per batch."""
        mock_ai.return_value = MOCK_AI_RESPONSE

        # Create 12 active pending-extraction jobs
        for i in range(12):
            job = JobOffer(
                id=str(uuid.uuid4()),
                employer_id=employer_profile.id,
                title=f"Job {i}",
                description=f"Description for job {i} with enough content.",
                canton="zurich",
                contract_type="full_time",
                salary_type="monthly",
                is_remote="no",
                status="active",
                source_name="JOBSPL",
                source_id=f"batch-{i}",
                extraction_status="pending",
                translation_status="completed",
                published_at=datetime.now(timezone.utc),
                expires_at=datetime.now(timezone.utc) + timedelta(days=30),
            )
            db_session.add(job)
        await db_session.commit()

        count = await process_pending_job_extractions(session_factory=TestSession)
        assert count == 10  # max 10 per batch

    @patch("app.services.job_extraction_service._call_extraction_ai")
    async def test_skips_max_attempts_jobs(self, mock_ai, db_session, employer_profile):
        """Jobs that exceeded max attempts should not be retried."""
        mock_ai.return_value = MOCK_AI_RESPONSE

        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=employer_profile.id,
            title="Exhausted Job",
            description="This job has exceeded max extraction attempts.",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            status="active",
            extraction_status="pending",
            extraction_attempts=MAX_EXTRACTION_ATTEMPTS,
        )
        db_session.add(job)
        await db_session.commit()

        count = await process_pending_job_extractions(session_factory=TestSession)
        assert count == 0  # should skip this job


# ── Tests: JobOffer model defaults ───────────────────────────────────


class TestJobOfferModelDefaults:
    """Test new column defaults on JobOffer model."""

    async def test_defaults(self, db_session, employer_profile):
        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=employer_profile.id,
            title="Defaults Test",
            description="Testing default values for new columns.",
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
            assert loaded.extraction_status == "pending"
            assert loaded.extraction_version == 0
            assert loaded.extraction_attempts == 0
            assert loaded.match_ready is False
            assert loaded.accommodation_provided is False
            assert loaded.shift_work is False
            assert loaded.skills is None
            assert loaded.seniority_level is None
            assert loaded.extracted_data is None
            assert loaded.translation_status == "none"
            assert loaded.translation_attempts == 0
