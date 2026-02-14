"""Tests for /api/v1/worker endpoints."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


class TestWorkerProfile:
    """GET/PUT /api/v1/worker/profile"""

    async def test_get_profile_success(self, client: AsyncClient, worker_token):
        resp = await client.get("/api/v1/worker/profile", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "worker@test.pl"
        assert data["first_name"] == "Jan"
        assert data["canton"] == "zurich"

    async def test_get_profile_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/worker/profile")
        assert resp.status_code == 403

    async def test_get_profile_employer_forbidden(self, client: AsyncClient, employer_token):
        resp = await client.get("/api/v1/worker/profile", headers=auth_header(employer_token))
        assert resp.status_code == 403

    async def test_update_profile_success(self, client: AsyncClient, worker_token):
        resp = await client.put("/api/v1/worker/profile", headers=auth_header(worker_token), json={
            "first_name": "Janusz",
            "bio": "Updated bio",
            "experience_years": 5,
            "canton": "bern",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["first_name"] == "Janusz"
        assert data["bio"] == "Updated bio"
        assert data["experience_years"] == 5
        assert data["canton"] == "bern"

    async def test_update_profile_languages(self, client: AsyncClient, worker_token):
        resp = await client.put("/api/v1/worker/profile", headers=auth_header(worker_token), json={
            "languages": [
                {"lang": "pl", "level": "C2"},
                {"lang": "de", "level": "B1"},
            ],
        })
        assert resp.status_code == 200
        assert len(resp.json()["languages"]) == 2

    async def test_update_profile_skills(self, client: AsyncClient, worker_token):
        resp = await client.put("/api/v1/worker/profile", headers=auth_header(worker_token), json={
            "skills": ["python", "fastapi", "react"],
        })
        assert resp.status_code == 200
        assert resp.json()["skills"] == ["python", "fastapi", "react"]


class TestWorkerCV:
    """POST/GET/DELETE /api/v1/worker/cv"""

    async def test_get_cv_info_with_cv(self, client: AsyncClient, worker_token, worker_cv):
        resp = await client.get("/api/v1/worker/cv-info", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["original_filename"] == "test_cv.pdf"
        assert data["extraction_status"] == "completed"
        assert data["extracted_name"] == "Jan Testowy"

    async def test_get_cv_info_no_cv(self, client: AsyncClient, worker_token):
        resp = await client.get("/api/v1/worker/cv-info", headers=auth_header(worker_token))
        assert resp.status_code == 404

    async def test_delete_cv_success(self, client: AsyncClient, worker_token, worker_cv):
        resp = await client.delete("/api/v1/worker/cv", headers=auth_header(worker_token))
        assert resp.status_code == 200
        assert "usunięte" in resp.json()["message"].lower()

    async def test_delete_cv_no_cv(self, client: AsyncClient, worker_token):
        resp = await client.delete("/api/v1/worker/cv", headers=auth_header(worker_token))
        assert resp.status_code == 404


class TestCVAnalysis:
    """POST /api/v1/worker/cv-analyze"""

    async def test_analyze_cv_success(self, client: AsyncClient, worker_token, worker_cv):
        resp = await client.post("/api/v1/worker/cv-analyze", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "strengths" in data
        assert "weaknesses" in data
        assert "tips" in data
        assert "score" in data
        assert 10 <= data["score"] <= 100

    async def test_analyze_cv_no_cv(self, client: AsyncClient, worker_token):
        resp = await client.post("/api/v1/worker/cv-analyze", headers=auth_header(worker_token))
        assert resp.status_code == 404


class TestCVConsent:
    """POST /api/v1/worker/cv-consent"""

    async def test_cv_consent_success(self, client: AsyncClient, worker_token, worker_cv):
        resp = await client.post("/api/v1/worker/cv-consent", headers=auth_header(worker_token), json={
            "consent": True,
            "job_preferences": "Szukam pracy w IT",
        })
        assert resp.status_code == 200
        assert "udostępnione" in resp.json()["message"].lower()

    async def test_cv_consent_without_consent(self, client: AsyncClient, worker_token, worker_cv):
        resp = await client.post("/api/v1/worker/cv-consent", headers=auth_header(worker_token), json={
            "consent": False,
        })
        assert resp.status_code == 400

    async def test_cv_consent_no_cv(self, client: AsyncClient, worker_token):
        resp = await client.post("/api/v1/worker/cv-consent", headers=auth_header(worker_token), json={
            "consent": True,
        })
        assert resp.status_code == 404


class TestWorkerCVUpload:
    """Additional CV upload tests."""

    async def test_upload_cv_wrong_type(self, client: AsyncClient, worker_token):
        """Uploading a non-PDF/DOCX file should fail."""
        import io
        file_content = b"not a real image"
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(worker_token),
            files={"file": ("test.jpg", io.BytesIO(file_content), "image/jpeg")},
        )
        assert resp.status_code == 400
        assert "PDF" in resp.json()["detail"] or "DOCX" in resp.json()["detail"]


class TestApplyForJob:
    """POST /api/v1/worker/jobs/{job_id}/apply"""

    async def test_apply_success(self, client: AsyncClient, worker_token, active_job):
        resp = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Jestem zainteresowany tą ofertą."},
        )
        assert resp.status_code == 201
        assert "wysłana" in resp.json()["message"].lower()

    async def test_apply_duplicate(self, client: AsyncClient, worker_token, active_job):
        # First application
        await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "First"},
        )
        # Second (should fail)
        resp = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Duplicate"},
        )
        assert resp.status_code == 409

    async def test_apply_to_nonexistent_job(self, client: AsyncClient, worker_token):
        resp = await client.post(
            "/api/v1/worker/jobs/nonexistent/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Hello"},
        )
        assert resp.status_code == 404

    async def test_apply_to_pending_job(self, client: AsyncClient, worker_token, pending_job):
        resp = await client.post(
            f"/api/v1/worker/jobs/{pending_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Hello"},
        )
        assert resp.status_code == 404  # Pending jobs are not "active"

    async def test_apply_employer_forbidden(self, client: AsyncClient, employer_token, active_job):
        resp = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(employer_token),
            json={"cover_letter": "I'm an employer"},
        )
        assert resp.status_code == 403


class TestListApplications:
    """GET /api/v1/worker/applications"""

    async def test_list_applications_empty(self, client: AsyncClient, worker_token):
        resp = await client.get("/api/v1/worker/applications", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["data"] == []

    async def test_list_applications_with_data(self, client: AsyncClient, worker_token, active_job):
        # Apply first
        await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Test"},
        )
        # List
        resp = await client.get("/api/v1/worker/applications", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["data"][0]["status"] == "sent"
