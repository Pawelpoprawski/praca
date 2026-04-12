"""
Tests for bugs discovered during QA hunt (2026-02-17).

BUG-1: Pagination broken in /oferty (frontend-only fix, no backend test needed)
BUG-2: Password reset token expiry not checked
BUG-3: Salary filter returns jobs with NULL salary data
BUG-4: LIKE wildcard injection in search query
"""
import uuid
import pytest
from datetime import datetime, timezone, timedelta, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.job_offer import JobOffer
from app.models.category import Category
from app.models.employer_profile import EmployerProfile
from app.models.user import User
from app.core.security import hash_password
from tests.conftest import auth_header


# ── Fixture: jobs with mixed salary data (some NULL) ──────────────────────────


@pytest.fixture
async def jobs_mixed_salary(db_session: AsyncSession, employer_user, category):
    """Create jobs with different salary scenarios: set, NULL, zero."""
    result = await db_session.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
    )
    profile = result.scalar_one()
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=30)

    jobs = [
        # Job with salary set (monthly 8000-12000)
        JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="Developer with salary",
            description="Job with salary data set for testing salary filter.",
            canton="zurich",
            contract_type="full_time",
            salary_min=8000,
            salary_max=12000,
            salary_type="monthly",
            is_remote="no",
            apply_via="portal",
            status="active",
            published_at=now,
            expires_at=expires,
        ),
        # Job with NULL salary (negotiable)
        JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="Developer negotiable salary",
            description="Job with no salary data for testing salary filter.",
            canton="zurich",
            contract_type="full_time",
            salary_min=None,
            salary_max=None,
            salary_type="negotiable",
            is_remote="no",
            apply_via="portal",
            status="active",
            published_at=now,
            expires_at=expires,
        ),
        # Job with low salary (hourly 25-35)
        JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="Worker hourly rate",
            description="Job with low hourly salary for testing salary filter.",
            canton="bern",
            contract_type="full_time",
            salary_min=25,
            salary_max=35,
            salary_type="hourly",
            is_remote="no",
            apply_via="portal",
            status="active",
            published_at=now,
            expires_at=expires,
        ),
    ]
    for job in jobs:
        db_session.add(job)
    await db_session.commit()
    return jobs


# ── BUG-2: Password reset token expiry ──────────────────────────────────────


class TestPasswordResetTokenExpiry:
    """BUG-2: reset_password must reject expired tokens."""

    async def test_expired_reset_token_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A reset token with expired reset_token_expires should be rejected."""
        user = User(
            id=str(uuid.uuid4()),
            email="resettest@test.pl",
            password_hash=hash_password("oldpassword"),
            role="worker",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_verified=True,
            reset_token="expired-token-12345",
            reset_token_expires=datetime.now(timezone.utc) - timedelta(days=2),  # expired 2 days ago
        )
        db_session.add(user)
        await db_session.commit()

        resp = await client.post("/api/v1/auth/reset-password", json={
            "token": "expired-token-12345",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.text}"
        assert "wygasł" in resp.json()["detail"].lower() or "expired" in resp.json()["detail"].lower()

    async def test_valid_reset_token_accepted(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A reset token within expiry period should work."""
        user = User(
            id=str(uuid.uuid4()),
            email="resetvalid@test.pl",
            password_hash=hash_password("oldpassword"),
            role="worker",
            first_name="Test",
            last_name="User",
            is_active=True,
            is_verified=True,
            reset_token="valid-token-67890",
            reset_token_expires=datetime.now(timezone.utc) + timedelta(days=1),  # valid for 1 more day
        )
        db_session.add(user)
        await db_session.commit()

        resp = await client.post("/api/v1/auth/reset-password", json={
            "token": "valid-token-67890",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    async def test_nonexistent_reset_token_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """A completely fake token should return 400."""
        resp = await client.post("/api/v1/auth/reset-password", json={
            "token": "nonexistent-token",
            "new_password": "newpassword123",
        })
        assert resp.status_code == 400


# ── BUG-3: Salary filter with NULL salary jobs ──────────────────────────────


class TestSalaryFilterNullExclusion:
    """BUG-3: salary filters must exclude jobs with NULL salary data."""

    async def test_salary_min_excludes_null_salary_jobs(
        self, client: AsyncClient, jobs_mixed_salary
    ):
        """salary_min filter should NOT return jobs where salary_max is NULL."""
        resp = await client.get("/api/v1/jobs?salary_min=5000")
        assert resp.status_code == 200
        data = resp.json()
        titles = [j["title"] for j in data["data"]]

        # Only "Developer with salary" (salary_max=12000) should match
        assert "Developer with salary" in titles
        # "Developer negotiable salary" (salary_max=None) must NOT be included
        assert "Developer negotiable salary" not in titles
        # "Worker hourly rate" (salary_max=35) is below 5000, must NOT be included
        assert "Worker hourly rate" not in titles

    async def test_salary_max_excludes_null_salary_jobs(
        self, client: AsyncClient, jobs_mixed_salary
    ):
        """salary_max filter should NOT return jobs where salary_min is NULL."""
        resp = await client.get("/api/v1/jobs?salary_max=50")
        assert resp.status_code == 200
        data = resp.json()
        titles = [j["title"] for j in data["data"]]

        # Only "Worker hourly rate" (salary_min=25) should match
        assert "Worker hourly rate" in titles
        # "Developer negotiable salary" (salary_min=None) must NOT be included
        assert "Developer negotiable salary" not in titles

    async def test_no_salary_filter_returns_all(
        self, client: AsyncClient, jobs_mixed_salary
    ):
        """Without salary filters, all jobs (including NULL salary) are returned."""
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3  # All 3 jobs


# ── BUG-4: LIKE wildcard injection ──────────────────────────────────────────


class TestSearchWildcardEscape:
    """BUG-4: Search query must escape SQL LIKE wildcards (%, _)."""

    async def test_percent_wildcard_does_not_match_all(
        self, client: AsyncClient, jobs_mixed_salary
    ):
        """Searching for literal '%' should return 0 results, not all jobs."""
        resp = await client.get("/api/v1/jobs?q=%25")  # %25 is URL-encoded %
        assert resp.status_code == 200
        data = resp.json()
        # '%' is not in any job title/description, so should return 0
        assert data["total"] == 0, (
            f"Expected 0 results for '%' search (wildcard should be escaped), got {data['total']}"
        )

    async def test_underscore_wildcard_does_not_match_all(
        self, client: AsyncClient, jobs_mixed_salary
    ):
        """Searching for literal '_' should not match any single character."""
        resp = await client.get("/api/v1/jobs?q=_")
        assert resp.status_code == 200
        data = resp.json()
        # '_' is not literally in any title/description, so should return 0
        assert data["total"] == 0, (
            f"Expected 0 results for '_' search (wildcard should be escaped), got {data['total']}"
        )

    async def test_normal_search_still_works(
        self, client: AsyncClient, jobs_mixed_salary
    ):
        """Normal text search is unaffected by wildcard escaping."""
        resp = await client.get("/api/v1/jobs?q=Developer")
        assert resp.status_code == 200
        data = resp.json()
        # Should find the two Developer jobs
        assert data["total"] == 2
        titles = [j["title"] for j in data["data"]]
        assert "Developer with salary" in titles
        assert "Developer negotiable salary" in titles

    async def test_suggestions_escape_wildcards(
        self, client: AsyncClient, jobs_mixed_salary
    ):
        """The /jobs/suggestions endpoint also escapes wildcards."""
        resp = await client.get("/api/v1/jobs/suggestions?q=%25%25")  # %%
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 0, f"Expected 0 suggestions for '%%', got {len(data)}"
