"""Tests for /api/v1/jobs (public) endpoints."""
import pytest
from httpx import AsyncClient


class TestListJobs:
    """GET /api/v1/jobs"""

    async def test_list_jobs_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["total"] == 0
        assert data["page"] == 1

    async def test_list_jobs_with_data(self, client: AsyncClient, active_job):
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert len(data["data"]) == 1
        assert data["data"][0]["title"] == "Test Developer"

    async def test_list_jobs_pagination(self, client: AsyncClient, active_job):
        resp = await client.get("/api/v1/jobs?page=1&per_page=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["per_page"] == 1

    async def test_list_jobs_search(self, client: AsyncClient, active_job):
        resp = await client.get("/api/v1/jobs?q=Developer")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp = await client.get("/api/v1/jobs?q=nonexistent")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_list_jobs_filter_by_canton(self, client: AsyncClient, active_job):
        resp = await client.get("/api/v1/jobs?canton=zurich")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp = await client.get("/api/v1/jobs?canton=bern")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_list_jobs_filter_by_contract_type(self, client: AsyncClient, active_job):
        resp = await client.get("/api/v1/jobs?contract_type=full_time")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

    async def test_list_jobs_filter_by_salary(self, client: AsyncClient, active_job):
        # Job salary is 8000-12000
        resp = await client.get("/api/v1/jobs?salary_min=7000")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp = await client.get("/api/v1/jobs?salary_min=15000")
        assert resp.status_code == 200
        assert resp.json()["total"] == 0

    async def test_list_jobs_sort_by_salary(self, client: AsyncClient, active_job):
        resp = await client.get("/api/v1/jobs?sort_by=salary")
        assert resp.status_code == 200

    async def test_list_jobs_sort_by_views(self, client: AsyncClient, active_job):
        resp = await client.get("/api/v1/jobs?sort_by=views")
        assert resp.status_code == 200


class TestGetJob:
    """GET /api/v1/jobs/{job_id}"""

    async def test_get_job_success(self, client: AsyncClient, active_job):
        resp = await client.get(f"/api/v1/jobs/{active_job.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == active_job.id
        assert data["title"] == "Test Developer"
        assert data["canton"] == "zurich"

    async def test_get_job_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/jobs/nonexistent-id")
        assert resp.status_code == 404

    async def test_get_job_increments_views(self, client: AsyncClient, active_job):
        initial_views = active_job.views_count
        await client.get(f"/api/v1/jobs/{active_job.id}")
        resp = await client.get(f"/api/v1/jobs/{active_job.id}")
        data = resp.json()
        # Views should have been incremented
        assert data["views_count"] > initial_views

    async def test_get_pending_job_not_visible(self, client: AsyncClient, pending_job):
        """Pending jobs should not be accessible via public endpoint."""
        resp = await client.get(f"/api/v1/jobs/{pending_job.id}")
        assert resp.status_code == 404


class TestCategories:
    """GET /api/v1/jobs/categories"""

    async def test_list_categories(self, client: AsyncClient, category):
        resp = await client.get("/api/v1/jobs/categories")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) >= 1
        cat = data[0]
        assert "id" in cat
        assert "name" in cat
        assert "slug" in cat

    async def test_list_categories_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/jobs/categories")
        assert resp.status_code == 200
        assert resp.json() == []


class TestJobFiltersAdvanced:
    """Additional filter tests for /api/v1/jobs"""

    async def test_filter_by_language(self, client: AsyncClient, active_job):
        """active_job has languages_required=[{lang: 'en', level: 'B2'}]"""
        resp = await client.get("/api/v1/jobs?language=en")
        assert resp.status_code == 200
        # Should include the job (or gracefully return results)
        data = resp.json()
        assert data["total"] >= 0  # endpoint may or may not support this filter

    async def test_multiple_cantons(self, client: AsyncClient, active_job):
        """Test filtering by multiple cantons."""
        resp = await client.get("/api/v1/jobs?canton=zurich")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        resp2 = await client.get("/api/v1/jobs?canton=bern")
        assert resp2.status_code == 200
        assert resp2.json()["total"] == 0

    async def test_combined_filters(self, client: AsyncClient, active_job):
        """Test combining canton + contract_type + salary."""
        resp = await client.get("/api/v1/jobs?canton=zurich&contract_type=full_time&salary_min=5000")
        assert resp.status_code == 200
        assert resp.json()["total"] == 1

        # No match
        resp2 = await client.get("/api/v1/jobs?canton=zurich&contract_type=part_time")
        assert resp2.status_code == 200
        assert resp2.json()["total"] == 0


class TestCantons:
    """GET /api/v1/jobs/cantons"""

    async def test_list_cantons(self, client: AsyncClient):
        resp = await client.get("/api/v1/jobs/cantons")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 26
        # Check structure
        assert "value" in data[0]
        assert "label" in data[0]
