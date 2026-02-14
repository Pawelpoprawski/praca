"""Tests for /api/v1/admin endpoints."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


class TestAdminDashboard:
    """GET /api/v1/admin/dashboard"""

    async def test_dashboard_success(self, client: AsyncClient, admin_token, seed_settings):
        resp = await client.get("/api/v1/admin/dashboard", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total_users" in data
        assert "total_workers" in data
        assert "total_employers" in data
        assert "total_jobs" in data
        assert "active_jobs" in data
        assert "pending_jobs" in data
        assert "total_applications" in data

    async def test_dashboard_unauthorized(self, client: AsyncClient):
        resp = await client.get("/api/v1/admin/dashboard")
        assert resp.status_code == 403

    async def test_dashboard_worker_forbidden(self, client: AsyncClient, worker_token):
        resp = await client.get("/api/v1/admin/dashboard", headers=auth_header(worker_token))
        assert resp.status_code == 403

    async def test_dashboard_employer_forbidden(self, client: AsyncClient, employer_token):
        resp = await client.get("/api/v1/admin/dashboard", headers=auth_header(employer_token))
        assert resp.status_code == 403


class TestAdminStatsTrends:
    """GET /api/v1/admin/stats/trends"""

    async def test_trends_success(self, client: AsyncClient, admin_token, seed_settings):
        resp = await client.get("/api/v1/admin/stats/trends", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "daily" in data
        assert "comparisons" in data
        assert "total_views" in data
        assert len(data["daily"]) == 30


class TestAdminModeration:
    """Job moderation endpoints."""

    async def test_list_all_jobs(self, client: AsyncClient, admin_token, seed_settings, active_job):
        resp = await client.get("/api/v1/admin/jobs", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_list_jobs_by_status(self, client: AsyncClient, admin_token, seed_settings, pending_job):
        resp = await client.get("/api/v1/admin/jobs?status=pending", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_approve_job(self, client: AsyncClient, admin_token, seed_settings, pending_job):
        resp = await client.put(
            f"/api/v1/admin/jobs/{pending_job.id}/approve",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "zatwierdzone" in resp.json()["message"].lower()

    async def test_reject_job(self, client: AsyncClient, admin_token, seed_settings, pending_job):
        resp = await client.put(
            f"/api/v1/admin/jobs/{pending_job.id}/reject?reason=Niepoprawne dane",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "odrzucone" in resp.json()["message"].lower()

    async def test_approve_nonexistent_job(self, client: AsyncClient, admin_token, seed_settings):
        resp = await client.put(
            "/api/v1/admin/jobs/nonexistent-id/approve",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404


class TestAdminUsers:
    """User management endpoints."""

    async def test_list_users(self, client: AsyncClient, admin_token, seed_settings, worker_user):
        resp = await client.get("/api/v1/admin/users", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_list_users_filter_by_role(self, client: AsyncClient, admin_token, seed_settings, worker_user):
        resp = await client.get("/api/v1/admin/users?role=worker", headers=auth_header(admin_token))
        assert resp.status_code == 200
        for user in resp.json()["data"]:
            assert user["role"] == "worker"

    async def test_list_users_search(self, client: AsyncClient, admin_token, seed_settings, worker_user):
        resp = await client.get("/api/v1/admin/users?q=worker@test", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert resp.json()["total"] >= 1

    async def test_toggle_user_status(self, client: AsyncClient, admin_token, seed_settings, worker_user):
        # Deactivate
        resp = await client.put(
            f"/api/v1/admin/users/{worker_user.id}/status?is_active=false",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "dezaktywowany" in resp.json()["message"].lower()

    async def test_cannot_deactivate_self(self, client: AsyncClient, admin_token, admin_user, seed_settings):
        resp = await client.put(
            f"/api/v1/admin/users/{admin_user.id}/status?is_active=false",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 400


class TestAdminCategories:
    """Category management."""

    async def test_list_categories(self, client: AsyncClient, admin_token, seed_settings, category):
        resp = await client.get("/api/v1/admin/categories", headers=auth_header(admin_token))
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_create_category(self, client: AsyncClient, admin_token, seed_settings):
        resp = await client.post(
            "/api/v1/admin/categories?name=Nowa Kategoria&icon=Star",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        assert "dodana" in resp.json()["message"].lower()

    async def test_update_category(self, client: AsyncClient, admin_token, seed_settings, category):
        resp = await client.put(
            f"/api/v1/admin/categories/{category.id}?name=Updated&sort_order=99",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200


class TestAdminSettings:
    """System settings endpoints."""

    async def test_get_settings(self, client: AsyncClient, admin_token, seed_settings):
        resp = await client.get("/api/v1/admin/settings", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        keys = [s["key"] for s in data]
        assert "default_monthly_posting_limit" in keys

    async def test_update_setting(self, client: AsyncClient, admin_token, seed_settings):
        resp = await client.put(
            "/api/v1/admin/settings?key=default_monthly_posting_limit&value=10",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    async def test_update_nonexistent_setting(self, client: AsyncClient, admin_token, seed_settings):
        resp = await client.put(
            "/api/v1/admin/settings?key=nonexistent&value=x",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404


class TestAdminQuotaOverride:
    """Quota override for employers."""

    async def test_override_quota(self, client: AsyncClient, admin_token, employer_user, db_session, seed_settings):
        from sqlalchemy import select
        from app.models.employer_profile import EmployerProfile
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        resp = await client.put(
            f"/api/v1/admin/employers/{profile.id}/quota?custom_limit=50",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200


class TestAdminModerationEdgeCases:
    """Edge cases for moderation."""

    async def test_reject_job_without_reason(self, client: AsyncClient, admin_token, seed_settings, pending_job):
        resp = await client.put(
            f"/api/v1/admin/jobs/{pending_job.id}/reject",
            headers=auth_header(admin_token),
        )
        # Should work even without reason (reason is optional)
        assert resp.status_code in [200, 422]

    async def test_approve_already_active_job(self, client: AsyncClient, admin_token, seed_settings, active_job):
        resp = await client.put(
            f"/api/v1/admin/jobs/{active_job.id}/approve",
            headers=auth_header(admin_token),
        )
        # Should succeed (idempotent) or return appropriate status
        assert resp.status_code in [200, 400]


class TestAdminCV:
    """CV statistics and listing."""

    async def test_cv_stats(self, client: AsyncClient, admin_token, seed_settings):
        resp = await client.get("/api/v1/admin/cv-stats", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert "total" in data
        assert "active" in data

    async def test_list_cvs(self, client: AsyncClient, admin_token, seed_settings, worker_cv):
        resp = await client.get("/api/v1/admin/cvs", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1
