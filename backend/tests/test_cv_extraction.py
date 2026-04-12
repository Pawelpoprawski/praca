"""Tests for the unified CV extraction system."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from tests.conftest import TestSession, auth_header

from app.models.cv_database import CVDatabase
from app.models.cv_review import CVReview
from app.services.cv_extraction_service import (
    map_extraction_to_cv_database,
    process_single_cv_extraction,
    process_pending_cv_extractions,
    EXTRACTION_VERSION,
)


# ── Sample AI response ────────────────────────────────────────────────

MOCK_AI_RESPONSE = {
    "full_name": "Jan Kowalski",
    "email": "jan@gmail.com",
    "phone": "+48 600 123 456",
    "location": "Polska",
    "experience_years": 5,
    "experience_entries": [
        {"position": "Spawacz", "company": "Hilti AG", "from": "2020", "to": "2023", "months": 36},
        {"position": "Monter", "company": "ABB", "from": "2018", "to": "2020", "months": 24},
    ],
    "category_slugs": ["budownictwo", "produkcja"],
    "skills": ["spawanie MIG/MAG", "montaz konstrukcji"],
    "keywords": "spawacz; spawanie; MIG; MAG; monter",
    "languages": [
        {"lang": "de", "level": "B1"},
        {"lang": "pl", "level": "native"},
    ],
    "driving_license": ["B"],
    "has_car": True,
    "education": [
        {"degree": "Technik mechanik", "institution": "ZSZ nr 2", "year": "2017"},
    ],
}


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def cv_review_entry(db_session):
    """Create a CVReview for testing Flow 1."""
    review = CVReview(
        id=str(uuid.uuid4()),
        cv_filename="test.pdf",
        cv_original_filename="cv_jan.pdf",
        cv_text="Jan Kowalski, spawacz z 5-letnim doswiadczeniem. Prawo jazdy kat. B.",
        status="analyzed",
        overall_score=7,
        analysis_json={"overall_score": 7, "summary": "test"},
    )
    db_session.add(review)
    await db_session.commit()
    return review


@pytest_asyncio.fixture
async def cv_db_pending(db_session, cv_review_entry):
    """Create a CVDatabase entry with pending extraction."""
    cv_db = CVDatabase(
        id=str(uuid.uuid4()),
        cv_review_id=cv_review_entry.id,
        full_name="Jan Kowalski",
        email="jan@gmail.com",
        phone="+48 600 123 456",
        cv_text="Jan Kowalski, spawacz z 5-letnim doswiadczeniem w Szwajcarii. Prawo jazdy kat. B. Jezyk niemiecki B1.",
        extraction_status="pending",
        consent_given=True,
    )
    db_session.add(cv_db)
    await db_session.commit()
    return cv_db


@pytest_asyncio.fixture
async def cv_db_no_text(db_session, cv_review_entry):
    """Create a CVDatabase entry without cv_text."""
    cv_db = CVDatabase(
        id=str(uuid.uuid4()),
        cv_review_id=cv_review_entry.id,
        full_name="Empty CV",
        email="empty@test.pl",
        cv_text=None,
        extraction_status="pending",
        consent_given=True,
    )
    db_session.add(cv_db)
    await db_session.commit()
    return cv_db


# ── Tests: map_extraction_to_cv_database ──────────────────────────────

class TestMapExtraction:
    """Test mapping AI response to CVDatabase columns."""

    def test_maps_all_fields(self, db_session):
        cv_db = CVDatabase(id=str(uuid.uuid4()))
        map_extraction_to_cv_database(cv_db, MOCK_AI_RESPONSE)

        assert cv_db.full_name == "Jan Kowalski"
        assert cv_db.email == "jan@gmail.com"
        assert cv_db.location == "Polska"
        assert cv_db.experience_years == 5
        assert len(cv_db.experience_entries) == 2
        assert cv_db.category_slugs == ["budownictwo", "produkcja"]
        assert "spawanie MIG/MAG" in cv_db.skills
        assert cv_db.ai_keywords == "spawacz; spawanie; MIG; MAG; monter"
        assert len(cv_db.education) == 1
        assert cv_db.driving_license == ["B"]
        assert cv_db.has_car is True
        assert cv_db.languages == [{"lang": "de", "level": "B1"}, {"lang": "pl", "level": "native"}]

    def test_does_not_overwrite_form_name_email_phone(self, db_session):
        """Human-provided values should take precedence."""
        cv_db = CVDatabase(
            id=str(uuid.uuid4()),
            full_name="Anna Nowak",
            email="anna@test.pl",
            phone="+48 500 000 000",
        )
        map_extraction_to_cv_database(cv_db, MOCK_AI_RESPONSE)

        assert cv_db.full_name == "Anna Nowak"  # NOT overwritten
        assert cv_db.email == "anna@test.pl"  # NOT overwritten
        assert cv_db.phone == "+48 500 000 000"  # NOT overwritten
        # But AI fields are still filled
        assert cv_db.location == "Polska"
        assert cv_db.experience_years == 5

    def test_handles_empty_ai_response(self, db_session):
        cv_db = CVDatabase(id=str(uuid.uuid4()))
        map_extraction_to_cv_database(cv_db, {})

        assert cv_db.experience_years == 0
        assert cv_db.experience_entries == []
        assert cv_db.category_slugs == []
        assert cv_db.skills == []
        assert cv_db.ai_keywords == ""
        assert cv_db.education == []

    def test_driving_license_string_to_list(self, db_session):
        """If AI returns string instead of list, normalize to list."""
        cv_db = CVDatabase(id=str(uuid.uuid4()))
        map_extraction_to_cv_database(cv_db, {"driving_license": "B"})
        assert cv_db.driving_license == ["B"]

    def test_stores_extracted_data_blob(self, db_session):
        cv_db = CVDatabase(id=str(uuid.uuid4()))
        map_extraction_to_cv_database(cv_db, MOCK_AI_RESPONSE)
        assert cv_db.extracted_data == MOCK_AI_RESPONSE

    def test_does_not_overwrite_existing_languages(self, db_session):
        """Form languages should take precedence if present."""
        cv_db = CVDatabase(
            id=str(uuid.uuid4()),
            languages=[{"lang": "fr", "level": "C1"}],
        )
        map_extraction_to_cv_database(cv_db, MOCK_AI_RESPONSE)
        assert cv_db.languages == [{"lang": "fr", "level": "C1"}]

    def test_does_not_overwrite_existing_driving_license(self, db_session):
        cv_db = CVDatabase(
            id=str(uuid.uuid4()),
            driving_license=["B", "C"],
        )
        map_extraction_to_cv_database(cv_db, MOCK_AI_RESPONSE)
        assert cv_db.driving_license == ["B", "C"]


# ── Tests: process_single_cv_extraction ───────────────────────────────

class TestProcessSingleExtraction:
    """Test the full extraction pipeline for a single CV."""

    @patch("app.services.cv_extraction_service.extract_cv_data_unified")
    async def test_successful_extraction(self, mock_extract, cv_db_pending):
        mock_extract.return_value = MOCK_AI_RESPONSE

        result = await process_single_cv_extraction(cv_db_pending.id, session_factory=TestSession)
        assert result is True

        # Verify DB was updated
        async with TestSession() as session:
            row = await session.execute(
                select(CVDatabase).where(CVDatabase.id == cv_db_pending.id)
            )
            cv_db = row.scalar_one()
            assert cv_db.extraction_status == "completed"
            assert cv_db.match_ready is True
            assert cv_db.extraction_version == EXTRACTION_VERSION
            assert cv_db.experience_years == 5
            assert cv_db.category_slugs == ["budownictwo", "produkcja"]
            assert cv_db.location == "Polska"

    @patch("app.services.cv_extraction_service.extract_cv_data_unified")
    async def test_failed_extraction_marks_failed(self, mock_extract, cv_db_pending):
        mock_extract.return_value = None

        result = await process_single_cv_extraction(cv_db_pending.id, session_factory=TestSession)
        assert result is False

        async with TestSession() as session:
            row = await session.execute(
                select(CVDatabase).where(CVDatabase.id == cv_db_pending.id)
            )
            cv_db = row.scalar_one()
            assert cv_db.extraction_status == "failed"
            assert cv_db.match_ready is False

    async def test_no_cv_text_marks_failed(self, cv_db_no_text):
        result = await process_single_cv_extraction(cv_db_no_text.id, session_factory=TestSession)
        assert result is False

        async with TestSession() as session:
            row = await session.execute(
                select(CVDatabase).where(CVDatabase.id == cv_db_no_text.id)
            )
            cv_db = row.scalar_one()
            assert cv_db.extraction_status == "failed"

    async def test_nonexistent_id_returns_false(self):
        result = await process_single_cv_extraction("nonexistent-id", session_factory=TestSession)
        assert result is False


# ── Tests: process_pending_cv_extractions (batch) ─────────────────────

class TestProcessPendingBatch:
    """Test the batch extraction scheduler job."""

    @patch("app.services.cv_extraction_service.extract_cv_data_unified")
    async def test_processes_pending_records(self, mock_extract, cv_db_pending):
        mock_extract.return_value = MOCK_AI_RESPONSE

        count = await process_pending_cv_extractions(session_factory=TestSession)
        assert count == 1

    async def test_no_pending_returns_zero(self):
        count = await process_pending_cv_extractions(session_factory=TestSession)
        assert count == 0

    @patch("app.services.cv_extraction_service.extract_cv_data_unified")
    async def test_processes_all_pending(self, mock_extract, db_session, cv_review_entry):
        """Should process ALL pending records in one run."""
        mock_extract.return_value = MOCK_AI_RESPONSE

        # Create 7 pending records
        for i in range(7):
            cv_db = CVDatabase(
                id=str(uuid.uuid4()),
                cv_review_id=cv_review_entry.id,
                full_name=f"Person {i}",
                email=f"person{i}@test.pl",
                cv_text=f"CV text for person {i} with some content.",
                extraction_status="pending",
                consent_given=True,
            )
            db_session.add(cv_db)
        await db_session.commit()

        count = await process_pending_cv_extractions(session_factory=TestSession)
        assert count == 7  # all processed


# ── Tests: CVDatabase model ──────────────────────────────────────────

class TestCVDatabaseModel:
    """Test model defaults and nullable fields."""

    async def test_defaults(self, db_session):
        cv_db = CVDatabase(
            id=str(uuid.uuid4()),
            consent_given=True,
        )
        db_session.add(cv_db)
        await db_session.commit()

        async with TestSession() as session:
            row = await session.execute(
                select(CVDatabase).where(CVDatabase.id == cv_db.id)
            )
            loaded = row.scalar_one()
            assert loaded.extraction_status == "pending"
            assert loaded.extraction_version == 0
            assert loaded.match_ready is False
            assert loaded.cv_review_id is None  # nullable
            assert loaded.cv_file_id is None  # nullable

    async def test_driving_license_as_json_list(self, db_session):
        cv_db = CVDatabase(
            id=str(uuid.uuid4()),
            driving_license=["B", "C"],
            consent_given=True,
        )
        db_session.add(cv_db)
        await db_session.commit()

        async with TestSession() as session:
            row = await session.execute(
                select(CVDatabase).where(CVDatabase.id == cv_db.id)
            )
            loaded = row.scalar_one()
            assert loaded.driving_license == ["B", "C"]


# ── Tests: Flow 1 - submit to database (no sync AI) ─────────────────

class TestSubmitToDatabaseFlow:
    """Verify the cv_review submit endpoint queues extraction instead of calling AI sync."""

    async def test_submit_creates_pending_extraction(
        self, client, cv_review_entry, db_session
    ):
        resp = await client.post(
            f"/api/v1/cv-review/{cv_review_entry.id}/submit-to-database",
            json={
                "full_name": "Jan Kowalski",
                "email": "jan@test.pl",
                "phone": "+48 600 000 000",
                "job_preferences": "Spawacz w Zurychu",
                "consent_given": True,
                "driving_license": ["B"],
                "has_car": True,
                "languages": [{"lang": "de", "level": "B1"}],
            },
        )
        assert resp.status_code == 200

        # Verify CVDatabase was created with pending status
        async with TestSession() as session:
            result = await session.execute(
                select(CVDatabase).where(CVDatabase.cv_review_id == cv_review_entry.id)
            )
            cv_db = result.scalar_one()
            assert cv_db.extraction_status == "pending"
            assert cv_db.match_ready is False
            assert cv_db.full_name == "Jan Kowalski"
            assert cv_db.driving_license == ["B"]
            assert cv_db.has_car is True
            assert cv_db.cv_text is not None  # should copy from review

    async def test_submit_driving_license_as_list(self, client, cv_review_entry, db_session):
        """driving_license should be stored as a list."""
        resp = await client.post(
            f"/api/v1/cv-review/{cv_review_entry.id}/submit-to-database",
            json={
                "full_name": "Test",
                "email": "test@test.pl",
                "job_preferences": "Test",
                "consent_given": True,
                "driving_license": ["B", "C"],
            },
        )
        assert resp.status_code == 200

        async with TestSession() as session:
            result = await session.execute(
                select(CVDatabase).where(CVDatabase.cv_review_id == cv_review_entry.id)
            )
            cv_db = result.scalar_one()
            assert cv_db.driving_license == ["B", "C"]


# ── Tests: Flow 2 - worker upload creates CVDatabase ─────────────────

class TestWorkerUploadFlow:
    """Verify worker CV upload creates CVDatabase entry."""

    async def test_upload_creates_cv_database_entry(
        self, client, worker_token, worker_user, db_session
    ):
        # Create a small valid PDF-like file
        import io
        content = b"%PDF-1.4 test content " * 100  # minimal "PDF"

        # Mock extract_text (imported lazily inside upload_cv)
        with patch("app.services.cv_extractor.extract_text", return_value="Jan Testowy, programista Python z 3-letnim doswiadczeniem."), \
             patch("app.services.cv_extractor.extract_info_from_text", return_value={"name": "Jan Testowy", "email": "worker@test.pl", "phone": None, "languages": []}):
            resp = await client.post(
                "/api/v1/worker/cv",
                headers=auth_header(worker_token),
                files={"file": ("test_cv.pdf", io.BytesIO(content), "application/pdf")},
            )

        assert resp.status_code == 200

        # Verify CVDatabase entry was created
        async with TestSession() as session:
            result = await session.execute(
                select(CVDatabase).where(CVDatabase.user_id == worker_user.id)
            )
            cv_db = result.scalar_one_or_none()
            assert cv_db is not None
            assert cv_db.extraction_status == "pending"
            assert cv_db.cv_file_id is not None
            assert cv_db.cv_review_id is None  # Flow 2 has no review
            assert cv_db.full_name == "Jan Testowy"
            assert cv_db.email == "worker@test.pl"
