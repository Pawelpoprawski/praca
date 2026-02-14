"""Tests for health check and basic app configuration."""
import pytest
from httpx import AsyncClient


class TestHealth:
    """GET /api/health"""

    async def test_health_check(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "PolacySzwajcaria API"


class TestSecurityHeaders:
    """Verify security headers are set."""

    async def test_security_headers_present(self, client: AsyncClient):
        resp = await client.get("/api/health")
        assert resp.headers.get("x-content-type-options") == "nosniff"
        assert resp.headers.get("x-frame-options") == "DENY"
        assert resp.headers.get("x-xss-protection") == "1; mode=block"
        assert resp.headers.get("referrer-policy") == "strict-origin-when-cross-origin"
