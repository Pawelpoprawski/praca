"""Tests for /api/v1/auth endpoints."""
import pytest
from httpx import AsyncClient
from tests.conftest import auth_header


# ── Registration ─────────────────────────────────────────────────────

class TestRegister:
    """POST /api/v1/auth/register"""

    async def test_register_worker_success(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "new.worker@test.pl",
            "password": "securepass123",
            "role": "worker",
            "first_name": "Nowy",
            "last_name": "Pracownik",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["email"] == "new.worker@test.pl"
        assert data["role"] == "worker"
        assert data["is_active"] is True
        assert data["is_verified"] is False

    async def test_register_employer_success(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "new.employer@test.ch",
            "password": "securepass123",
            "role": "employer",
            "first_name": "HR",
            "last_name": "Nowy",
            "company_name": "NoweFirma AG",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert data["role"] == "employer"

    async def test_register_employer_without_company_name(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "nocompany@test.ch",
            "password": "securepass123",
            "role": "employer",
            "first_name": "HR",
            "last_name": "NoName",
        })
        assert resp.status_code == 400
        assert "firma" in resp.json()["detail"].lower() or "Nazwa" in resp.json()["detail"]

    async def test_register_duplicate_email(self, client: AsyncClient, worker_user):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "worker@test.pl",
            "password": "securepass123",
            "role": "worker",
            "first_name": "Klon",
            "last_name": "Testowy",
        })
        assert resp.status_code == 409

    async def test_register_invalid_role(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "bad@test.pl",
            "password": "securepass123",
            "role": "admin",
            "first_name": "Bad",
            "last_name": "Role",
        })
        assert resp.status_code == 422

    async def test_register_short_password(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "short@test.pl",
            "password": "abc",
            "role": "worker",
            "first_name": "Short",
            "last_name": "Pass",
        })
        assert resp.status_code == 422

    async def test_register_invalid_email(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "not-an-email",
            "password": "securepass123",
            "role": "worker",
            "first_name": "Bad",
            "last_name": "Email",
        })
        assert resp.status_code == 422


# ── Login ────────────────────────────────────────────────────────────

class TestLogin:
    """POST /api/v1/auth/login"""

    async def test_login_success(self, client: AsyncClient, worker_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "worker@test.pl",
            "password": "testpass123",
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, worker_user):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "worker@test.pl",
            "password": "wrongpassword",
        })
        assert resp.status_code == 401

    async def test_login_nonexistent_user(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/login", json={
            "email": "ghost@test.pl",
            "password": "whatever123",
        })
        assert resp.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient, db_session):
        from app.models.user import User
        from app.core.security import hash_password
        import uuid
        user = User(
            id=str(uuid.uuid4()),
            email="inactive@test.pl",
            password_hash=hash_password("testpass123"),
            role="worker",
            first_name="Inactive",
            last_name="User",
            is_active=False,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()

        resp = await client.post("/api/v1/auth/login", json={
            "email": "inactive@test.pl",
            "password": "testpass123",
        })
        assert resp.status_code == 403


# ── Token refresh ────────────────────────────────────────────────────

class TestRefresh:
    """POST /api/v1/auth/refresh"""

    async def test_refresh_success(self, client: AsyncClient, worker_user):
        # First login
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "worker@test.pl",
            "password": "testpass123",
        })
        refresh_token = login_resp.json()["refresh_token"]

        # Refresh
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": refresh_token,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_refresh_invalid_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/refresh", json={
            "refresh_token": "invalid.token.here",
        })
        assert resp.status_code == 401


# ── Get current user ─────────────────────────────────────────────────

class TestMe:
    """GET /api/v1/auth/me"""

    async def test_me_success(self, client: AsyncClient, worker_user, worker_token):
        resp = await client.get("/api/v1/auth/me", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()
        assert data["email"] == "worker@test.pl"
        assert data["role"] == "worker"

    async def test_me_no_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403  # HTTPBearer returns 403 when missing

    async def test_me_invalid_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me", headers=auth_header("invalid"))
        assert resp.status_code == 401


# ── Forgot / Reset password ──────────────────────────────────────────

class TestPasswordReset:
    async def test_forgot_password_existing_email(self, client: AsyncClient, worker_user):
        resp = await client.post("/api/v1/auth/forgot-password", json={
            "email": "worker@test.pl",
        })
        assert resp.status_code == 200
        assert "wysłaliśmy" in resp.json()["message"].lower() or "link" in resp.json()["message"].lower()

    async def test_forgot_password_nonexistent_email(self, client: AsyncClient):
        """Should still return 200 (security - don't reveal if email exists)."""
        resp = await client.post("/api/v1/auth/forgot-password", json={
            "email": "nonexistent@test.pl",
        })
        assert resp.status_code == 200

    async def test_reset_password_invalid_token(self, client: AsyncClient):
        resp = await client.post("/api/v1/auth/reset-password", json={
            "token": "invalid-token",
            "new_password": "newsecurepass123",
        })
        assert resp.status_code == 400


# ── Email verification ───────────────────────────────────────────────

class TestEmailVerification:
    async def test_verify_email_invalid_token(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/verify-email/invalid-token")
        assert resp.status_code == 400

    async def test_verify_email_success(self, client: AsyncClient):
        """Register user, then verify with the token."""
        # Register creates an unverified user
        reg_resp = await client.post("/api/v1/auth/register", json={
            "email": "verify-me@test.pl",
            "password": "securepass123",
            "role": "worker",
            "first_name": "Verify",
            "last_name": "Me",
        })
        assert reg_resp.status_code == 201
        assert reg_resp.json()["is_verified"] is False

        # Get the verification token from DB
        from tests.conftest import TestSession
        from sqlalchemy import select
        from app.models.user import User
        async with TestSession() as session:
            result = await session.execute(
                select(User).where(User.email == "verify-me@test.pl")
            )
            user = result.scalar_one()
            token = user.verification_token

        # Verify
        resp = await client.get(f"/api/v1/auth/verify-email/{token}")
        assert resp.status_code == 200
        assert "zweryfikowany" in resp.json()["message"].lower()

    async def test_verify_email_double_verify(self, client: AsyncClient):
        """Verifying same token twice should fail."""
        await client.post("/api/v1/auth/register", json={
            "email": "double-verify@test.pl",
            "password": "securepass123",
            "role": "worker",
            "first_name": "Double",
            "last_name": "Verify",
        })

        from tests.conftest import TestSession
        from sqlalchemy import select
        from app.models.user import User
        async with TestSession() as session:
            result = await session.execute(
                select(User).where(User.email == "double-verify@test.pl")
            )
            user = result.scalar_one()
            token = user.verification_token

        # First verify
        resp1 = await client.get(f"/api/v1/auth/verify-email/{token}")
        assert resp1.status_code == 200

        # Second verify (token should be cleared)
        resp2 = await client.get(f"/api/v1/auth/verify-email/{token}")
        assert resp2.status_code == 400


class TestResetPasswordFull:
    async def test_reset_password_success(self, client: AsyncClient, worker_user):
        """Full forgot -> reset password flow."""
        # Request reset
        await client.post("/api/v1/auth/forgot-password", json={
            "email": "worker@test.pl",
        })

        # Get token from DB
        from tests.conftest import TestSession
        from sqlalchemy import select
        from app.models.user import User
        async with TestSession() as session:
            result = await session.execute(
                select(User).where(User.email == "worker@test.pl")
            )
            user = result.scalar_one()
            token = user.reset_token

        assert token is not None

        # Reset password
        resp = await client.post("/api/v1/auth/reset-password", json={
            "token": token,
            "new_password": "newpassword123",
        })
        assert resp.status_code == 200

        # Login with new password
        login_resp = await client.post("/api/v1/auth/login", json={
            "email": "worker@test.pl",
            "password": "newpassword123",
        })
        assert login_resp.status_code == 200


class TestRegisterCreatesProfile:
    async def test_register_worker_creates_profile(self, client: AsyncClient):
        """Registering a worker creates a WorkerProfile."""
        resp = await client.post("/api/v1/auth/register", json={
            "email": "profile-test@test.pl",
            "password": "securepass123",
            "role": "worker",
            "first_name": "Profile",
            "last_name": "Test",
        })
        assert resp.status_code == 201

        # Verify profile exists
        from tests.conftest import TestSession
        from sqlalchemy import select
        from app.models.user import User
        from app.models.worker_profile import WorkerProfile
        async with TestSession() as session:
            result = await session.execute(
                select(User).where(User.email == "profile-test@test.pl")
            )
            user = result.scalar_one()
            profile_result = await session.execute(
                select(WorkerProfile).where(WorkerProfile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            assert profile is not None
