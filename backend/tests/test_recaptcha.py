"""Tests for reCAPTCHA v3 verification."""
import os
from unittest.mock import patch, AsyncMock, MagicMock
import pytest
from httpx import AsyncClient


class TestRecaptchaDisabled:
    """When RECAPTCHA_ENABLED=false, requests pass through."""

    async def test_register_without_recaptcha(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "norecaptcha@test.pl",
            "password": "securepass123",
            "role": "worker",
            "first_name": "Test",
            "last_name": "User",
        })
        assert resp.status_code == 201

    async def test_login_without_recaptcha(self, client: AsyncClient, worker_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "worker@test.pl",
            "password": "testpass123",
        })
        assert resp.status_code == 200


class TestRecaptchaEnabled:
    """When RECAPTCHA_ENABLED=true, token is required and verified."""

    @pytest.fixture(autouse=True)
    def enable_recaptcha(self):
        from app.config import get_settings as _gs
        _gs.cache_clear()
        os.environ["RECAPTCHA_ENABLED"] = "true"
        os.environ["RECAPTCHA_SECRET_KEY"] = "test-secret"
        yield
        os.environ["RECAPTCHA_ENABLED"] = "false"
        os.environ.pop("RECAPTCHA_SECRET_KEY", None)
        _gs.cache_clear()

    async def test_register_no_token_returns_400(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "test@test.pl",
            "password": "securepass123",
            "role": "worker",
            "first_name": "Test",
            "last_name": "User",
        })
        assert resp.status_code == 400
        assert "reCAPTCHA" in resp.json()["detail"]

    async def test_register_invalid_token_returns_403(self, client: AsyncClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": False, "score": 0.1}

        with patch("app.core.recaptcha.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            resp = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "test@test.pl",
                    "password": "securepass123",
                    "role": "worker",
                    "first_name": "Test",
                    "last_name": "User",
                },
                headers={"X-Recaptcha-Token": "invalid-token"},
            )
            assert resp.status_code == 403

    async def test_register_valid_token_passes(self, client: AsyncClient):
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "score": 0.9}

        with patch("app.core.recaptcha.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_instance.post.return_value = mock_response
            mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_instance.__aexit__ = AsyncMock(return_value=False)
            mock_client.return_value = mock_instance

            resp = await client.post(
                "/api/v1/auth/register",
                json={
                    "email": "recaptcha-ok@test.pl",
                    "password": "securepass123",
                    "role": "worker",
                    "first_name": "Test",
                    "last_name": "User",
                },
                headers={"X-Recaptcha-Token": "valid-token"},
            )
            assert resp.status_code == 201
