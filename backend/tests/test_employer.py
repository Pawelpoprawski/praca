"""Tests for /api/v1/employer endpoints."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


class TestEmployerProfile:
    """GET/PUT /api/v1/employer/profile"""

    async def test_get_profile_success(self, client: AsyncClient, employer_token):
        resp = await client.get("/api/v1/employer/profile", headers=auth_header(employer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "Test GmbH"
        assert data["company_slug"] == "test-gmbh"
        assert data["email"] == "employer@test.ch"

    async def test_get_profile_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/employer/profile")
        assert resp.status_code == 403

    async def test_get_profile_worker_forbidden(self, client: AsyncClient, worker_token):
        resp = await client.get("/api/v1/employer/profile", headers=auth_header(worker_token))
        assert resp.status_code == 403

    async def test_update_profile_success(self, client: AsyncClient, employer_token):
        resp = await client.put("/api/v1/employer/profile", headers=auth_header(employer_token), json={
            "description": "Updated description",
            "website": "https://test-gmbh.ch",
            "industry": "IT",
            "city": "Winterthur",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["website"] == "https://test-gmbh.ch"
        assert data["industry"] == "IT"
        assert data["city"] == "Winterthur"


class TestEmployerDashboard:
    """GET /api/v1/employer/dashboard"""

    async def test_dashboard_success(self, client: AsyncClient, employer_token):
        resp = await client.get("/api/v1/employer/dashboard", headers=auth_header(employer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "active_jobs" in data
        assert "total_applications" in data
        assert "new_applications" in data
        assert "quota_used" in data
        assert "quota_limit" in data

    async def test_dashboard_with_jobs(self, client: AsyncClient, employer_token, active_job):
        resp = await client.get("/api/v1/employer/dashboard", headers=auth_header(employer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["active_jobs"] == 1


class TestEmployerJobs:
    """CRUD for employer jobs."""

    async def test_list_my_jobs_empty(self, client: AsyncClient, employer_token):
        resp = await client.get("/api/v1/employer/jobs", headers=auth_header(employer_token))
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_list_my_jobs_with_data(self, client: AsyncClient, employer_token, active_job):
        resp = await client.get("/api/v1/employer/jobs", headers=auth_header(employer_token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_create_job_success(self, client: AsyncClient, employer_token, category):
        resp = await client.post("/api/v1/employer/jobs", headers=auth_header(employer_token), json={
            "title": "New Test Position",
            "description": "This is a brand new test position with a sufficiently long description.",
            "canton": "bern",
            "contract_type": "full_time",
            "salary_min": 5000,
            "salary_max": 7000,
            "salary_type": "monthly",
            "experience_min": 1,
            "is_remote": "no",
            "languages_required": [{"lang": "de", "level": "B1"}],
            "apply_via": "portal",
            "category_id": category.id,
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Test Position"
        assert data["status"] == "pending"  # new jobs are pending moderation

    async def test_create_job_worker_forbidden(self, client: AsyncClient, worker_token, category):
        resp = await client.post("/api/v1/employer/jobs", headers=auth_header(worker_token), json={
            "title": "Forbidden Job",
            "description": "Workers should not be able to create job postings.",
            "canton": "zurich",
            "contract_type": "full_time",
            "apply_via": "portal",
        })
        assert resp.status_code == 403

    async def test_create_job_validation_short_title(self, client: AsyncClient, employer_token):
        resp = await client.post("/api/v1/employer/jobs", headers=auth_header(employer_token), json={
            "title": "AB",
            "description": "Valid description long enough.",
            "canton": "zurich",
            "contract_type": "full_time",
            "apply_via": "portal",
        })
        assert resp.status_code == 422

    async def test_update_job_success(self, client: AsyncClient, employer_token, active_job):
        resp = await client.put(
            f"/api/v1/employer/jobs/{active_job.id}",
            headers=auth_header(employer_token),
            json={"title": "Updated Title Here"},
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Title Here"

    async def test_update_job_not_found(self, client: AsyncClient, employer_token):
        resp = await client.put(
            "/api/v1/employer/jobs/nonexistent-id",
            headers=auth_header(employer_token),
            json={"title": "Nope"},
        )
        assert resp.status_code == 404

    async def test_delete_job_success(self, client: AsyncClient, employer_token, active_job):
        resp = await client.delete(
            f"/api/v1/employer/jobs/{active_job.id}",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 200
        assert "usunięte" in resp.json()["message"].lower()

    async def test_close_job_success(self, client: AsyncClient, employer_token, active_job):
        resp = await client.patch(
            f"/api/v1/employer/jobs/{active_job.id}/close",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 200
        assert "zamknięte" in resp.json()["message"].lower()


class TestEmployerCandidates:
    """Candidate management endpoints."""

    async def test_list_candidates_empty(self, client: AsyncClient, employer_token, active_job):
        resp = await client.get(
            f"/api/v1/employer/jobs/{active_job.id}/applications",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_list_candidates_with_application(
        self, client: AsyncClient, employer_token, worker_token, active_job
    ):
        # Worker applies
        await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "I want this job"},
        )
        # Employer lists candidates
        resp = await client.get(
            f"/api/v1/employer/jobs/{active_job.id}/applications",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["status"] == "sent"
        assert data[0]["cover_letter"] == "I want this job"

    async def test_update_application_status(
        self, client: AsyncClient, employer_token, worker_token, active_job
    ):
        # Worker applies
        await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Hire me"},
        )
        # Get the application ID
        candidates = await client.get(
            f"/api/v1/employer/jobs/{active_job.id}/applications",
            headers=auth_header(employer_token),
        )
        app_id = candidates.json()[0]["id"]

        # Update status
        resp = await client.put(
            f"/api/v1/employer/applications/{app_id}/status",
            headers=auth_header(employer_token),
            json={"status": "shortlisted", "employer_notes": "Good candidate"},
        )
        assert resp.status_code == 200


class TestEmployerJobsEdgeCases:
    """Edge cases for employer job operations."""

    async def test_create_job_exceeds_quota(self, client: AsyncClient, employer_token, category, db_session):
        """Creating a job when quota is exhausted should fail."""
        from sqlalchemy import select
        from app.models.employer_profile import EmployerProfile
        from app.models.posting_quota import PostingQuota
        from tests.conftest import TestSession

        # Exhaust the quota
        async with TestSession() as session:
            result = await session.execute(select(PostingQuota))
            quota = result.scalar_one()
            quota.used_count = quota.monthly_limit or 5
            await session.commit()

        resp = await client.post("/api/v1/employer/jobs", headers=auth_header(employer_token), json={
            "title": "Over Quota Job",
            "description": "This job should be rejected because the employer exceeded their quota.",
            "canton": "bern",
            "contract_type": "full_time",
            "salary_min": 5000,
            "salary_max": 7000,
            "salary_type": "monthly",
            "experience_min": 1,
            "is_remote": "no",
            "languages_required": [],
            "apply_via": "portal",
            "category_id": category.id,
        })
        assert resp.status_code == 429  # QuotaExceededError

    async def test_delete_nonexistent_job(self, client: AsyncClient, employer_token):
        resp = await client.delete(
            "/api/v1/employer/jobs/nonexistent-id",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 404

    async def test_update_application_status_success(
        self, client: AsyncClient, employer_token, worker_token, active_job
    ):
        """Full flow: apply -> get candidates -> update status to accepted."""
        await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Hire me please"},
        )
        candidates = await client.get(
            f"/api/v1/employer/jobs/{active_job.id}/applications",
            headers=auth_header(employer_token),
        )
        app_id = candidates.json()[0]["id"]

        resp = await client.put(
            f"/api/v1/employer/applications/{app_id}/status",
            headers=auth_header(employer_token),
            json={"status": "accepted"},
        )
        assert resp.status_code == 200
        assert "accepted" in resp.json()["message"]


class TestEmployerQuota:
    """GET /api/v1/employer/quota"""

    async def test_get_quota(self, client: AsyncClient, employer_token):
        resp = await client.get("/api/v1/employer/quota", headers=auth_header(employer_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["plan_type"] == "free"
        assert data["used_count"] == 0
        assert data["remaining"] > 0
