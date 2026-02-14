"""Tests for /api/v1/companies (public) endpoints."""
import pytest
from httpx import AsyncClient


class TestGetCompany:
    """GET /api/v1/companies/{slug}"""

    async def test_get_company_success(self, client: AsyncClient, employer_user):
        resp = await client.get("/api/v1/companies/test-gmbh")
        assert resp.status_code == 200
        data = resp.json()
        assert data["company_name"] == "Test GmbH"
        assert data["company_slug"] == "test-gmbh"

    async def test_get_company_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/companies/nonexistent-company")
        assert resp.status_code == 404


class TestCompanyJobs:
    """GET /api/v1/companies/{slug}/jobs"""

    async def test_company_jobs_success(self, client: AsyncClient, employer_user, active_job):
        resp = await client.get("/api/v1/companies/test-gmbh/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 1

    async def test_company_jobs_empty(self, client: AsyncClient, employer_user):
        resp = await client.get("/api/v1/companies/test-gmbh/jobs")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_company_jobs_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/companies/nonexistent/jobs")
        assert resp.status_code == 404

    async def test_company_jobs_pagination(self, client: AsyncClient, employer_user, active_job):
        resp = await client.get("/api/v1/companies/test-gmbh/jobs?page=1&per_page=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["per_page"] == 1

    async def test_company_pending_jobs_not_shown(self, client: AsyncClient, employer_user, pending_job):
        """Pending jobs should not appear in the public company jobs listing."""
        resp = await client.get("/api/v1/companies/test-gmbh/jobs")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0  # pending_job shouldn't be visible
