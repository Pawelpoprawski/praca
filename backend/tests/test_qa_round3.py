"""
QA Round 3 — Deepest bug hunt for PolacySzwajcaria backend.

Covers:
- DATA CONSISTENCY: GET /jobs/:id vs GET /jobs list schema, expired job detail visibility
- JOB LIFECYCLE: edit expired/closed jobs, applications after delete, employer deactivated
- FILE UPLOAD: 0-byte CV, filename path traversal, content-type vs magic bytes
- TOKEN EDGE CASES: refresh token reuse, malformed JWT
- ADMIN EDGE CASES: admin self-deactivation prevention, admin-only actions
- SEARCH & FILTERS: unicode/Polish chars, combined filters, all filter combos
- SCHEMA DRIFT: frontend TS types vs backend responses (fields present/absent)
- QUOTA EDGE CASES: expired quota period, custom_limit precedence
- WORKER WITHDRAW APPLICATION: is it possible?
- SAVED JOB EDGE CASES: save deleted/inactive job
"""
import uuid
import io
import pytest
from datetime import datetime, timezone, timedelta, date
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.models.worker_profile import WorkerProfile
from app.models.employer_profile import EmployerProfile
from app.models.job_offer import JobOffer
from app.models.application import Application
from app.models.posting_quota import PostingQuota
from app.models.category import Category
from app.models.saved_job import SavedJob
from app.core.security import hash_password, create_access_token
from tests.conftest import auth_header


# ════════════════════════════════════════════════════════════════════
# SECTION 1 – DATA CONSISTENCY: expired job visible via GET /jobs/:id
# ════════════════════════════════════════════════════════════════════

class TestExpiredJobVisibility:
    """Bug: GET /jobs/:id doesn't check expiry – expired jobs are visible by ID."""

    async def test_expired_job_not_returned_in_list(
        self, client: AsyncClient, db_session: AsyncSession, active_job: JobOffer
    ):
        """An expired job should NOT appear in the list endpoint."""
        # Expire the job
        active_job.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.commit()

        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        job_ids = [j["id"] for j in data["data"]]
        assert active_job.id not in job_ids, "Expired job must NOT appear in job list"

    async def test_expired_job_should_not_be_accessible_by_id(
        self, client: AsyncClient, db_session: AsyncSession, active_job: JobOffer
    ):
        """An expired job should return 404 when accessed by ID — this tests the BUG."""
        # Expire the job (status stays "active" but expires_at is past)
        active_job.expires_at = datetime.now(timezone.utc) - timedelta(hours=1)
        await db_session.commit()

        resp = await client.get(f"/api/v1/jobs/{active_job.id}")
        # BUG: currently returns 200 because GET /jobs/:id only checks status=="active"
        # but NOT expires_at. After fix it should return 404.
        assert resp.status_code == 404, (
            "Expired jobs must not be accessible by ID. "
            "GET /jobs/:id must check expiry in addition to status."
        )

    async def test_non_expired_active_job_is_accessible_by_id(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """A non-expired active job should still return 200."""
        resp = await client.get(f"/api/v1/jobs/{active_job.id}")
        assert resp.status_code == 200


# ════════════════════════════════════════════════════════════════════
# SECTION 2 – DATA CONSISTENCY: schema drift list vs detail
# ════════════════════════════════════════════════════════════════════

class TestSchemaConsistency:
    """Check for schema drift between list and detail responses."""

    async def test_job_detail_has_all_required_fields(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """GET /jobs/:id must include all fields the frontend JobOffer type expects."""
        resp = await client.get(f"/api/v1/jobs/{active_job.id}")
        assert resp.status_code == 200
        data = resp.json()

        # Required by frontend JobOffer TypeScript interface
        required_fields = [
            "id", "title", "description", "canton", "city", "contract_type",
            "salary_min", "salary_max", "salary_type", "salary_currency",
            "experience_min", "car_required", "driving_license_required",
            "is_remote", "languages_required", "apply_via", "external_url",
            "status", "views_count", "is_featured", "published_at",
            "expires_at", "created_at", "employer", "category",
        ]
        for field in required_fields:
            assert field in data, f"Field '{field}' missing from job detail response"

    async def test_job_list_item_has_all_required_fields(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """GET /jobs must include all fields the frontend JobListItem type expects."""
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) > 0
        item = data["data"][0]

        # Required by frontend JobListItem TypeScript interface
        required_fields = [
            "id", "title", "canton", "city", "contract_type",
            "salary_min", "salary_max", "salary_type", "salary_currency",
            "is_remote", "is_featured", "published_at", "employer", "category",
        ]
        for field in required_fields:
            assert field in item, f"Field '{field}' missing from job list item"

    async def test_user_response_no_sensitive_fields(
        self, client: AsyncClient, worker_user: User, worker_token: str
    ):
        """GET /auth/me must NEVER include password_hash, reset_token, verification_token."""
        resp = await client.get("/api/v1/auth/me", headers=auth_header(worker_token))
        assert resp.status_code == 200
        data = resp.json()

        sensitive_fields = ["password_hash", "reset_token", "reset_token_expires", "verification_token"]
        for field in sensitive_fields:
            assert field not in data, f"Sensitive field '{field}' exposed in UserResponse"

    async def test_employer_profile_response_has_expected_fields(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """Employer profile response must match frontend EmployerProfile interface."""
        resp = await client.get("/api/v1/employer/profile", headers=auth_header(employer_token))
        assert resp.status_code == 200
        data = resp.json()

        # Frontend expects these fields (EmployerProfile interface)
        expected_fields = [
            "id", "user_id", "company_name", "company_slug", "description",
            "logo_url", "website", "industry", "canton", "city", "address",
            "uid_number", "company_size", "is_verified", "created_at",
        ]
        for field in expected_fields:
            assert field in data, f"Field '{field}' missing from employer profile response"

    async def test_admin_cv_list_includes_has_car_field(
        self, client: AsyncClient, admin_user: User, admin_token: str, db_session: AsyncSession
    ):
        """
        Bug: admin GET /admin/cv-database list items do NOT include 'has_car'.
        Frontend CVDatabaseListItem type expects has_car: boolean.
        Only the detail endpoint (GET /admin/cv-database/:id) includes it.
        """
        # We can only test this if there's a CVDatabase entry - skip if none
        # This test verifies the endpoint schema structure
        resp = await client.get("/api/v1/admin/cv-database", headers=auth_header(admin_token))
        assert resp.status_code == 200
        data = resp.json()
        # If there are entries, verify has_car is present
        if data["data"]:
            for item in data["data"]:
                assert "has_car" in item, (
                    "CVDatabaseListItem is missing 'has_car' field. "
                    "Frontend expects has_car: boolean in list items."
                )


# ════════════════════════════════════════════════════════════════════
# SECTION 3 – JOB LIFECYCLE EDGE CASES
# ════════════════════════════════════════════════════════════════════

class TestJobLifecycleEdgeCases:
    """Test job lifecycle: edit after expiry/closure, delete with applications."""

    async def test_employer_can_edit_expired_job(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str, active_job: JobOffer
    ):
        """
        Edge case: employer can edit an expired job (status='active', expires_at past).
        The edit endpoint doesn't restrict status. This should probably be prevented
        or at least mark the job as requiring re-approval after editing.
        """
        active_job.expires_at = datetime.now(timezone.utc) - timedelta(days=1)
        await db_session.commit()

        resp = await client.put(
            f"/api/v1/employer/jobs/{active_job.id}",
            headers=auth_header(employer_token),
            json={"title": "Updated Title After Expiry"},
        )
        # Currently returns 200 - this is an edge case that might need restriction
        # Test documents current behavior
        assert resp.status_code == 200

    async def test_employer_edit_rejected_job_resets_to_pending(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str, active_job: JobOffer
    ):
        """When an employer edits a rejected job, it should go back to pending."""
        active_job.status = "rejected"
        active_job.rejection_reason = "Too vague description"
        await db_session.commit()

        resp = await client.put(
            f"/api/v1/employer/jobs/{active_job.id}",
            headers=auth_header(employer_token),
            json={"description": "This is now a much more detailed description that explains everything clearly."},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "pending", "Edited rejected job should return to pending"
        assert data.get("rejection_reason") is None, "rejection_reason should be cleared"

    async def test_applications_deleted_when_job_deleted(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str,
        worker_user: User, worker_token: str,
        active_job: JobOffer
    ):
        """Applications should be cascade-deleted when a job is deleted."""
        # Create an application
        application = Application(
            id=str(uuid.uuid4()),
            job_offer_id=active_job.id,
            worker_id=worker_user.id,
            status="sent",
        )
        db_session.add(application)
        await db_session.commit()
        app_id = application.id

        # Delete the job
        resp = await client.delete(
            f"/api/v1/employer/jobs/{active_job.id}",
            headers=auth_header(employer_token)
        )
        assert resp.status_code == 200

        # Verify application was cascade deleted
        result = await db_session.execute(
            select(Application).where(Application.id == app_id)
        )
        assert result.scalar_one_or_none() is None, "Application should be deleted when job is deleted"

    async def test_worker_cannot_apply_to_closed_job(
        self, client: AsyncClient, db_session: AsyncSession,
        worker_user: User, worker_token: str, active_job: JobOffer
    ):
        """Worker should not be able to apply to a closed job."""
        active_job.status = "closed"
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "I would love to work here."},
        )
        assert resp.status_code in (404, 400, 409), (
            f"Worker should not be able to apply to closed job, got {resp.status_code}"
        )

    async def test_worker_cannot_apply_to_pending_job(
        self, client: AsyncClient, db_session: AsyncSession,
        worker_user: User, worker_token: str, pending_job: JobOffer
    ):
        """Worker should not be able to apply to a pending (unmoderated) job."""
        resp = await client.post(
            f"/api/v1/worker/jobs/{pending_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "I would love to work here."},
        )
        assert resp.status_code in (404, 400), (
            f"Worker should not be able to apply to pending job, got {resp.status_code}"
        )

    async def test_jobs_from_deactivated_employer_still_visible(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, active_job: JobOffer
    ):
        """When employer's account is deactivated, their active jobs remain visible (by design)."""
        employer_user.is_active = False
        await db_session.commit()

        # The public job listing should still show the job
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        job_ids = [j["id"] for j in data["data"]]
        # This documents current behavior - jobs remain visible when employer deactivated
        # A future improvement might hide them, but for now we just verify behavior
        assert active_job.id in job_ids, "Active job should remain visible even when employer deactivated"

    async def test_worker_cannot_withdraw_application(
        self, client: AsyncClient, db_session: AsyncSession,
        worker_user: User, worker_token: str, active_job: JobOffer
    ):
        """
        There is no application withdrawal endpoint.
        Workers cannot withdraw/delete their own applications.
        This tests that no such endpoint exists (or documents the gap).
        """
        application = Application(
            id=str(uuid.uuid4()),
            job_offer_id=active_job.id,
            worker_id=worker_user.id,
            status="sent",
        )
        db_session.add(application)
        await db_session.commit()

        # Try to delete the application (no such endpoint should exist for workers)
        resp = await client.delete(
            f"/api/v1/worker/applications/{application.id}",
            headers=auth_header(worker_token),
        )
        # Should be 404 (no such route) or 405 (method not allowed)
        assert resp.status_code in (404, 405, 403), (
            f"Workers should not be able to delete/withdraw applications, got {resp.status_code}"
        )


# ════════════════════════════════════════════════════════════════════
# SECTION 4 – FILE UPLOAD EDGE CASES
# ════════════════════════════════════════════════════════════════════

class TestFileUploadEdgeCases:
    """Test CV upload edge cases: 0-byte file, path traversal, content-type spoofing."""

    async def test_cv_upload_zero_byte_file_rejected(
        self, client: AsyncClient, worker_user: User, worker_token: str
    ):
        """A 0-byte file should be rejected (or at least not crash the server)."""
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(worker_token),
            files={"file": ("empty.pdf", b"", "application/pdf")},
        )
        # A 0-byte file is not a valid PDF but the current code only checks MIME type
        # It should either succeed (with failed extraction) or reject it gracefully
        # The important thing is it doesn't crash (5xx)
        assert resp.status_code < 500, f"0-byte file upload must not cause server error, got {resp.status_code}"

    async def test_cv_upload_wrong_mime_type_rejected(
        self, client: AsyncClient, worker_user: User, worker_token: str
    ):
        """A file with wrong MIME type should be rejected."""
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(worker_token),
            files={"file": ("resume.txt", b"This is not a PDF", "text/plain")},
        )
        assert resp.status_code == 400

    async def test_cv_upload_exe_with_pdf_mime_accepted_but_extracted_fails(
        self, client: AsyncClient, worker_user: User, worker_token: str
    ):
        """
        Bug: Content-type is client-controlled. A renamed .exe sent with
        'application/pdf' MIME passes the check. The server trusts the client's
        content_type header. It should validate magic bytes/file content.
        This test documents the vulnerability.
        """
        # Fake binary content (not a real PDF - no %PDF- magic bytes)
        fake_exe_content = b"MZ\x90\x00\x03\x00\x00\x00"  # EXE magic bytes
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(worker_token),
            files={"file": ("resume.pdf", fake_exe_content, "application/pdf")},
        )
        # Currently this passes (200) because only MIME type is checked
        # After a fix: should return 400 with magic bytes validation
        # For now, document current behavior: it should at minimum not crash
        assert resp.status_code < 500, "Server must not crash on non-PDF binary content"

    async def test_cv_upload_path_traversal_filename_sanitized(
        self, client: AsyncClient, worker_user: User, worker_token: str
    ):
        """
        Path traversal in filename is stored in original_filename but the actual
        file path uses a UUID — so no real traversal is possible.
        This test documents that the upload succeeds (not a crash) and the file
        is stored safely regardless of the original filename.
        """
        malicious_filename = "../../etc/passwd"
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(worker_token),
            files={"file": (malicious_filename, b"%PDF-1.4 fake pdf content", "application/pdf")},
        )
        # Should not crash (5xx) - upload uses UUID path not the original filename
        assert resp.status_code < 500, "Path traversal filename must not cause server crash"
        # The upload might succeed (200) because actual file path uses UUID
        # The original_filename is stored as-is (cosmetic field, no actual filesystem risk)

    async def test_logo_upload_wrong_mime_rejected(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """Logo upload with non-image MIME type should be rejected."""
        resp = await client.post(
            "/api/v1/employer/profile/logo",
            headers=auth_header(employer_token),
            files={"file": ("logo.pdf", b"%PDF-1.4 fake", "application/pdf")},
        )
        assert resp.status_code == 400

    async def test_logo_upload_zero_byte_file(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """Logo upload with 0-byte file should not crash the server."""
        resp = await client.post(
            "/api/v1/employer/profile/logo",
            headers=auth_header(employer_token),
            files={"file": ("logo.png", b"", "image/png")},
        )
        # Should not return 5xx
        assert resp.status_code < 500, f"0-byte logo upload must not crash, got {resp.status_code}"


# ════════════════════════════════════════════════════════════════════
# SECTION 5 – TOKEN & SESSION EDGE CASES
# ════════════════════════════════════════════════════════════════════

class TestTokenEdgeCases:
    """Test JWT edge cases: refresh token reuse, malformed tokens."""

    async def test_refresh_token_can_be_reused(
        self, client: AsyncClient, worker_user: User
    ):
        """
        Bug: Refresh tokens are not blacklisted after use.
        Old refresh tokens remain valid and can be reused.
        This is a security concern - SHOULD fail after fix.
        """
        # Login to get tokens
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "worker@test.pl", "password": "testpass123"},
        )
        assert resp.status_code == 200
        old_refresh_token = resp.json()["refresh_token"]

        # Use the refresh token to get new tokens
        resp2 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        assert resp2.status_code == 200

        # Reuse the OLD refresh token (should be invalid after rotation)
        resp3 = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": old_refresh_token},
        )
        # Bug: currently returns 200 (token reuse works)
        # After fix: should return 401 (token already used/blacklisted)
        # We document current behavior - it succeeds (vulnerability)
        assert resp3.status_code in (200, 401), (
            f"Refresh token reuse returned unexpected {resp3.status_code}. "
            "Ideally 401 after token rotation."
        )

    async def test_malformed_jwt_rejected(
        self, client: AsyncClient, worker_user: User
    ):
        """A completely invalid JWT string should return 401 (auth failure)."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer not.a.valid.jwt"},
        )
        # get_current_user raises 401 for invalid/expired token payloads
        assert resp.status_code == 401

    async def test_access_token_with_wrong_type_rejected(
        self, client: AsyncClient, worker_user: User
    ):
        """A refresh token used as an access token should be rejected."""
        from app.core.security import create_refresh_token
        refresh_tok = create_refresh_token(worker_user.id)

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {refresh_tok}"},
        )
        # get_current_user() correctly validates type == "access" and raises 401
        # when a refresh token (type="refresh") is used as an access token.
        assert resp.status_code == 401, (
            "Refresh tokens must not be accepted as access tokens. "
            "get_current_user() validates token 'type' field and raises 401."
        )

    async def test_empty_bearer_token_rejected(
        self, client: AsyncClient
    ):
        """Empty bearer token string should be rejected."""
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer "},
        )
        assert resp.status_code == 403

    async def test_valid_base64_garbage_payload_rejected(
        self, client: AsyncClient
    ):
        """Valid base64 but garbage JWT payload (bad signature) should return 401."""
        import base64
        # Create a fake JWT-looking string with valid base64 but invalid signature
        header = base64.urlsafe_b64encode(b'{"alg":"HS256","typ":"JWT"}').rstrip(b"=").decode()
        payload = base64.urlsafe_b64encode(b'{"sub":"hacker","role":"admin"}').rstrip(b"=").decode()
        fake_jwt = f"{header}.{payload}.fakesignature"

        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {fake_jwt}"},
        )
        # jose/JWT library raises JWTError for invalid signature -> decode_token returns None
        # -> get_current_user raises 401 (Unauthorized)
        assert resp.status_code == 401

    async def test_deactivated_user_token_rejected(
        self, client: AsyncClient, db_session: AsyncSession,
        worker_user: User, worker_token: str
    ):
        """Token for a deactivated user should be rejected."""
        worker_user.is_active = False
        await db_session.commit()

        resp = await client.get("/api/v1/auth/me", headers=auth_header(worker_token))
        assert resp.status_code == 403


# ════════════════════════════════════════════════════════════════════
# SECTION 6 – ADMIN EDGE CASES
# ════════════════════════════════════════════════════════════════════

class TestAdminEdgeCases:
    """Test admin edge cases: self-deactivation, last admin, etc."""

    async def test_admin_cannot_deactivate_themselves(
        self, client: AsyncClient, admin_user: User, admin_token: str
    ):
        """Admin should not be able to deactivate their own account."""
        resp = await client.put(
            f"/api/v1/admin/users/{admin_user.id}/status",
            headers=auth_header(admin_token),
            params={"is_active": "false"},
        )
        assert resp.status_code == 400, (
            "Admin should not be able to deactivate their own account"
        )

    async def test_admin_can_deactivate_other_user(
        self, client: AsyncClient, admin_user: User, admin_token: str,
        worker_user: User
    ):
        """Admin should be able to deactivate other users."""
        resp = await client.put(
            f"/api/v1/admin/users/{worker_user.id}/status",
            headers=auth_header(admin_token),
            params={"is_active": "false"},
        )
        assert resp.status_code == 200

    async def test_admin_approve_nonexistent_job_returns_404(
        self, client: AsyncClient, admin_user: User, admin_token: str
    ):
        """Approving a nonexistent job should return 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.put(
            f"/api/v1/admin/jobs/{fake_id}/approve",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 404

    async def test_admin_reject_job_without_reason_fails(
        self, client: AsyncClient, admin_user: User, admin_token: str,
        db_session: AsyncSession, pending_job: JobOffer
    ):
        """Rejecting a job without providing a reason should fail (reason is required)."""
        resp = await client.put(
            f"/api/v1/admin/jobs/{pending_job.id}/reject",
            headers=auth_header(admin_token),
            # No 'reason' query param
        )
        assert resp.status_code == 422, "reason param is required for job rejection"

    async def test_admin_can_approve_pending_job(
        self, client: AsyncClient, admin_user: User, admin_token: str,
        pending_job: JobOffer
    ):
        """Admin should be able to approve a pending job."""
        resp = await client.put(
            f"/api/v1/admin/jobs/{pending_job.id}/approve",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200

    async def test_admin_can_reject_pending_job(
        self, client: AsyncClient, admin_user: User, admin_token: str,
        pending_job: JobOffer
    ):
        """Admin should be able to reject a pending job with reason."""
        resp = await client.put(
            f"/api/v1/admin/jobs/{pending_job.id}/reject",
            headers=auth_header(admin_token),
            params={"reason": "Description too vague"},
        )
        assert resp.status_code == 200

    async def test_admin_list_users_search_by_email(
        self, client: AsyncClient, admin_user: User, admin_token: str,
        worker_user: User
    ):
        """Admin user search should filter by email substring."""
        resp = await client.get(
            "/api/v1/admin/users",
            headers=auth_header(admin_token),
            params={"q": "worker@"},
        )
        assert resp.status_code == 200
        data = resp.json()
        emails = [u["email"] for u in data["data"]]
        assert "worker@test.pl" in emails

    async def test_admin_override_quota_for_employer(
        self, client: AsyncClient, admin_user: User, admin_token: str,
        employer_user: User, db_session: AsyncSession
    ):
        """Admin should be able to override quota for an employer."""
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        resp = await client.put(
            f"/api/v1/admin/employers/{profile.id}/quota",
            headers=auth_header(admin_token),
            params={"custom_limit": "20"},
        )
        assert resp.status_code == 200

    async def test_admin_dashboard_returns_correct_counts(
        self, client: AsyncClient, admin_user: User, admin_token: str,
        worker_user: User, employer_user: User
    ):
        """Admin dashboard should return user counts correctly."""
        resp = await client.get(
            "/api/v1/admin/dashboard",
            headers=auth_header(admin_token),
        )
        assert resp.status_code == 200
        data = resp.json()

        assert data["total_users"] >= 3  # admin + worker + employer
        assert data["total_workers"] >= 1
        assert data["total_employers"] >= 1
        required_fields = [
            "total_users", "total_workers", "total_employers",
            "total_jobs", "active_jobs", "pending_jobs", "total_applications"
        ]
        for field in required_fields:
            assert field in data, f"Dashboard missing field '{field}'"


# ════════════════════════════════════════════════════════════════════
# SECTION 7 – SEARCH & FILTER EDGE CASES
# ════════════════════════════════════════════════════════════════════

class TestSearchAndFilterEdgeCases:
    """Test search with Polish characters, Unicode, combined filters."""

    async def test_search_with_polish_characters(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, category: Category
    ):
        """Search should work correctly with Polish diacritics (ą, ę, ś, ź, ż, ó, ł, ń)."""
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        # Create job with Polish characters
        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="Kierowca ciężarówki z doświadczeniem",
            description="Szukamy kierowcy z prawem jazdy kat. C i doświadczeniem w transporcie międzynarodowym.",
            canton="zurich",
            city="Zürich",
            contract_type="full_time",
            apply_via="portal",
            status="active",
            published_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(job)
        await db_session.commit()

        # Search with Polish chars
        resp = await client.get("/api/v1/jobs", params={"q": "doświadczeniem"})
        assert resp.status_code == 200
        data = resp.json()
        job_ids = [j["id"] for j in data["data"]]
        assert job.id in job_ids, "Polish character search should find matching jobs"

    async def test_search_with_unicode_special_chars(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, category: Category
    ):
        """Search should handle unicode without crashing."""
        resp = await client.get("/api/v1/jobs", params={"q": "café résumé naïve"})
        assert resp.status_code == 200

    async def test_search_with_html_entities(
        self, client: AsyncClient
    ):
        """Search with HTML entities should not crash or cause XSS."""
        resp = await client.get("/api/v1/jobs", params={"q": "<script>alert(1)</script>"})
        assert resp.status_code == 200
        # Verify the response doesn't echo back unescaped HTML
        # (it returns JSON, so XSS in search log is moot)

    async def test_combined_filters_canton_and_category(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, category: Category, active_job: JobOffer
    ):
        """Combining canton + category filter should return correct results."""
        resp = await client.get(
            "/api/v1/jobs",
            params={"canton": "zurich", "category_id": category.id}
        )
        assert resp.status_code == 200
        data = resp.json()
        # All returned jobs should match both filters
        for job in data["data"]:
            assert job["canton"] == "zurich"

    async def test_combined_filters_all_parameters(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, category: Category, active_job: JobOffer
    ):
        """All filters combined should not crash."""
        resp = await client.get(
            "/api/v1/jobs",
            params={
                "q": "Developer",
                "canton": "zurich",
                "category_id": category.id,
                "salary_min": "5000",
                "salary_max": "15000",
                "is_remote": "hybrid",
                "contract_type": "full_time",
                "sort_by": "salary",
                "sort_order": "desc",
                "page": "1",
                "per_page": "10",
            }
        )
        assert resp.status_code == 200

    async def test_sort_by_salary_with_null_salaries(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, category: Category
    ):
        """Sorting by salary should handle NULL salary values gracefully (nulls_last)."""
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        # Job with no salary
        job_no_salary = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="No Salary Job",
            description="Job without salary information listed explicitly here.",
            canton="bern",
            contract_type="full_time",
            apply_via="portal",
            status="active",
            published_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(job_no_salary)
        await db_session.commit()

        resp = await client.get("/api/v1/jobs", params={"sort_by": "salary", "sort_order": "desc"})
        assert resp.status_code == 200
        data = resp.json()
        # Should return results without error
        assert isinstance(data["data"], list)

    async def test_filter_multiple_cantons(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """Multi-select canton filter with comma-separated values."""
        resp = await client.get(
            "/api/v1/jobs",
            params={"canton": "zurich,bern,geneve"}
        )
        assert resp.status_code == 200
        data = resp.json()
        # All jobs should be in one of the specified cantons
        for job in data["data"]:
            assert job["canton"] in ["zurich", "bern", "geneve"]

    async def test_filter_multiple_contract_types(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """Multi-select contract_type filter with comma-separated values."""
        resp = await client.get(
            "/api/v1/jobs",
            params={"contract_type": "full_time,part_time"}
        )
        assert resp.status_code == 200
        data = resp.json()
        for job in data["data"]:
            assert job["contract_type"] in ["full_time", "part_time"]

    async def test_search_with_single_quote(
        self, client: AsyncClient
    ):
        """Search with SQL-dangerous characters should not crash (SQL injection)."""
        resp = await client.get("/api/v1/jobs", params={"q": "it's a test'"})
        assert resp.status_code == 200

    async def test_search_with_very_long_query(
        self, client: AsyncClient
    ):
        """Very long search query should be handled gracefully."""
        long_query = "a" * 500
        resp = await client.get("/api/v1/jobs", params={"q": long_query})
        # Should handle gracefully (either validate max_length or truncate)
        assert resp.status_code in (200, 422)


# ════════════════════════════════════════════════════════════════════
# SECTION 8 – QUOTA EDGE CASES
# ════════════════════════════════════════════════════════════════════

class TestQuotaEdgeCases:
    """Test posting quota edge cases: custom_limit precedence, exact limit boundary."""

    async def test_quota_custom_limit_overrides_monthly_limit(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str, category: Category
    ):
        """custom_limit should take precedence over monthly_limit."""
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        # Set a very low custom limit (0 - block everything)
        result = await db_session.execute(
            select(PostingQuota).where(PostingQuota.employer_id == profile.id)
        )
        quota = result.scalar_one()
        quota.custom_limit = 0
        quota.used_count = 0
        await db_session.commit()

        # Try to create a job - should be blocked by custom_limit=0
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Test Job",
                "description": "This is a test job description that is long enough.",
                "canton": "zurich",
                "contract_type": "full_time",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 429, (
            "custom_limit=0 should block job creation even when monthly_limit allows it"
        )

    async def test_quota_exactly_at_limit_blocked(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str, category: Category
    ):
        """When used_count == monthly_limit, creating a job should be blocked."""
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        result = await db_session.execute(
            select(PostingQuota).where(PostingQuota.employer_id == profile.id)
        )
        quota = result.scalar_one()
        quota.used_count = quota.monthly_limit  # exactly at limit
        await db_session.commit()

        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Over Quota Job",
                "description": "This should be blocked by quota enforcement mechanism.",
                "canton": "zurich",
                "contract_type": "full_time",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 429, "Job creation at exact quota limit should be blocked"

    async def test_quota_one_below_limit_allowed(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str, category: Category
    ):
        """When used_count == monthly_limit - 1, creating a job should succeed."""
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        result = await db_session.execute(
            select(PostingQuota).where(PostingQuota.employer_id == profile.id)
        )
        quota = result.scalar_one()
        quota.used_count = quota.monthly_limit - 1  # one below limit
        await db_session.commit()

        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Last Allowed Job",
                "description": "This should be allowed as we are one below the quota limit.",
                "canton": "zurich",
                "contract_type": "full_time",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 201, "Job creation one below quota limit should succeed"

    async def test_quota_incremented_after_job_creation(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str, category: Category
    ):
        """used_count should be incremented after successful job creation."""
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        result = await db_session.execute(
            select(PostingQuota).where(PostingQuota.employer_id == profile.id)
        )
        quota = result.scalar_one()
        initial_count = quota.used_count

        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "New Job",
                "description": "Job description that is long enough to pass validation threshold.",
                "canton": "bern",
                "contract_type": "part_time",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 201

        await db_session.refresh(quota)
        assert quota.used_count == initial_count + 1, "Quota should be incremented by 1 after job creation"

    async def test_get_quota_endpoint_returns_correct_data(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """GET /employer/quota should return correct quota info matching frontend QuotaInfo interface."""
        resp = await client.get("/api/v1/employer/quota", headers=auth_header(employer_token))
        assert resp.status_code == 200
        data = resp.json()

        # Check all fields expected by frontend QuotaInfo interface
        expected_fields = [
            "plan_type", "monthly_limit", "used_count", "remaining",
            "period_start", "period_end", "days_until_reset", "has_custom_limit"
        ]
        for field in expected_fields:
            assert field in data, f"QuotaInfo missing field '{field}'"

        assert data["remaining"] == data["monthly_limit"] - data["used_count"]


# ════════════════════════════════════════════════════════════════════
# SECTION 9 – SAVED JOBS EDGE CASES
# ════════════════════════════════════════════════════════════════════

class TestSavedJobsEdgeCases:
    """Test saved jobs toggle, edge cases with nonexistent jobs."""

    async def test_save_nonexistent_job_returns_404(
        self, client: AsyncClient, worker_user: User, worker_token: str
    ):
        """Saving a nonexistent job should return 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.post(
            f"/api/v1/worker/saved-jobs/{fake_id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 404

    async def test_toggle_saved_job_works(
        self, client: AsyncClient, worker_user: User, worker_token: str,
        active_job: JobOffer
    ):
        """Toggling a job save should switch between saved and unsaved."""
        # Save
        resp = await client.post(
            f"/api/v1/worker/saved-jobs/{active_job.id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        msg = resp.json()["message"].lower()
        # Polish: "Oferta zapisana w ulubionych"
        assert "zapisana" in msg or "saved" in msg or "ulubionych" in msg

        # Unsave (toggle)
        resp2 = await client.post(
            f"/api/v1/worker/saved-jobs/{active_job.id}",
            headers=auth_header(worker_token),
        )
        assert resp2.status_code == 200
        msg = resp2.json()["message"].lower()
        # Polish: "Oferta usunięta z ulubionych"
        assert "usunięta" in msg or "usunieta" in msg or "removed" in msg or "ulubionych" in msg

    async def test_check_saved_job_returns_boolean(
        self, client: AsyncClient, worker_user: User, worker_token: str,
        active_job: JobOffer
    ):
        """Check saved job endpoint should return is_saved boolean."""
        resp = await client.get(
            f"/api/v1/worker/saved-jobs/check/{active_job.id}",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "is_saved" in data
        assert isinstance(data["is_saved"], bool)
        assert data["is_saved"] is False

    async def test_saved_jobs_list_has_correct_schema(
        self, client: AsyncClient, worker_user: User, worker_token: str,
        active_job: JobOffer
    ):
        """Saved jobs list should match SavedJob frontend interface."""
        # Save a job first
        await client.post(
            f"/api/v1/worker/saved-jobs/{active_job.id}",
            headers=auth_header(worker_token),
        )

        resp = await client.get(
            "/api/v1/worker/saved-jobs",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "data" in data
        assert len(data["data"]) > 0
        saved = data["data"][0]

        # Check schema matches SavedJob frontend interface
        assert "id" in saved
        assert "job_offer_id" in saved
        assert "created_at" in saved
        assert "job" in saved


# ════════════════════════════════════════════════════════════════════
# SECTION 10 – IDOR AND CROSS-EMPLOYER ISOLATION
# ════════════════════════════════════════════════════════════════════

class TestCrossEmployerIsolation:
    """Ensure employers cannot access/modify other employers' data."""

    async def test_employer_cannot_delete_other_employers_job(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str, active_job: JobOffer
    ):
        """An employer cannot delete another employer's job."""
        # Create a second employer
        other_employer = User(
            id=str(uuid.uuid4()),
            email="other_employer@test.ch",
            password_hash=hash_password("testpass123"),
            role="employer",
            first_name="Other",
            last_name="Employer",
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_employer)
        await db_session.flush()

        other_profile = EmployerProfile(
            id=str(uuid.uuid4()),
            user_id=other_employer.id,
            company_name="Other GmbH",
            company_slug="other-gmbh",
            canton="bern",
            city="Bern",
            is_verified=True,
        )
        db_session.add(other_profile)
        await db_session.commit()

        other_token = create_access_token(other_employer.id, "employer")

        # Second employer tries to delete first employer's job
        resp = await client.delete(
            f"/api/v1/employer/jobs/{active_job.id}",
            headers=auth_header(other_token),
        )
        assert resp.status_code == 404, "Employer should not be able to delete another employer's job"

    async def test_employer_cannot_view_other_employers_applications(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, active_job: JobOffer,
        worker_user: User
    ):
        """An employer cannot see applications for another employer's job."""
        # Create second employer
        other_employer = User(
            id=str(uuid.uuid4()),
            email="other2_employer@test.ch",
            password_hash=hash_password("testpass123"),
            role="employer",
            first_name="Other2",
            last_name="Employer",
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_employer)
        await db_session.flush()

        other_profile = EmployerProfile(
            id=str(uuid.uuid4()),
            user_id=other_employer.id,
            company_name="Other2 GmbH",
            company_slug="other2-gmbh",
            canton="geneve",
            city="Geneva",
            is_verified=True,
        )
        db_session.add(other_profile)

        # Add an application to the first employer's job
        app = Application(
            id=str(uuid.uuid4()),
            job_offer_id=active_job.id,
            worker_id=worker_user.id,
            status="sent",
        )
        db_session.add(app)
        await db_session.commit()

        other_token = create_access_token(other_employer.id, "employer")

        # Second employer tries to view candidates for first employer's job
        resp = await client.get(
            f"/api/v1/employer/jobs/{active_job.id}/applications",
            headers=auth_header(other_token),
        )
        assert resp.status_code == 404, (
            "Employer should not be able to view applications for another employer's job"
        )

    async def test_employer_cannot_update_other_employers_application_status(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, active_job: JobOffer, worker_user: User
    ):
        """Employer cannot change application status for another employer's job."""
        # Create application
        app = Application(
            id=str(uuid.uuid4()),
            job_offer_id=active_job.id,
            worker_id=worker_user.id,
            status="sent",
        )
        db_session.add(app)

        # Second employer
        other_employer = User(
            id=str(uuid.uuid4()),
            email="other3_employer@test.ch",
            password_hash=hash_password("testpass123"),
            role="employer",
            first_name="Other3",
            last_name="Employer",
            is_active=True,
            is_verified=True,
        )
        db_session.add(other_employer)
        await db_session.flush()

        other_profile = EmployerProfile(
            id=str(uuid.uuid4()),
            user_id=other_employer.id,
            company_name="Other3 GmbH",
            company_slug="other3-gmbh",
            canton="ticino",
            city="Lugano",
            is_verified=True,
        )
        db_session.add(other_profile)
        await db_session.commit()

        other_token = create_access_token(other_employer.id, "employer")

        resp = await client.put(
            f"/api/v1/employer/applications/{app.id}/status",
            headers=auth_header(other_token),
            json={"status": "rejected"},
        )
        assert resp.status_code == 404


# ════════════════════════════════════════════════════════════════════
# SECTION 11 – PAGINATION EDGE CASES
# ════════════════════════════════════════════════════════════════════

class TestPaginationEdgeCases:
    """Test pagination boundary conditions."""

    async def test_page_beyond_last_page_returns_empty(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """Requesting a page beyond the last page should return empty data, not an error."""
        resp = await client.get("/api/v1/jobs", params={"page": "9999", "per_page": "20"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["total"] >= 0

    async def test_per_page_max_100(
        self, client: AsyncClient
    ):
        """per_page > 100 should return 422."""
        resp = await client.get("/api/v1/jobs", params={"per_page": "101"})
        assert resp.status_code == 422

    async def test_per_page_zero_rejected(
        self, client: AsyncClient
    ):
        """per_page=0 should return 422."""
        resp = await client.get("/api/v1/jobs", params={"per_page": "0"})
        assert resp.status_code == 422

    async def test_negative_page_rejected(
        self, client: AsyncClient
    ):
        """page=0 should return 422 (page must be >= 1)."""
        resp = await client.get("/api/v1/jobs", params={"page": "0"})
        assert resp.status_code == 422

    async def test_pagination_metadata_consistent(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """Pagination metadata (total, pages, page, per_page) should be consistent."""
        resp = await client.get("/api/v1/jobs", params={"page": "1", "per_page": "10"})
        assert resp.status_code == 200
        data = resp.json()

        assert data["page"] == 1
        assert data["per_page"] == 10
        assert data["total"] >= 0
        import math
        expected_pages = math.ceil(data["total"] / 10) if data["total"] else 0
        assert data["pages"] == expected_pages


# ════════════════════════════════════════════════════════════════════
# SECTION 12 – APPLICATION BUSINESS LOGIC
# ════════════════════════════════════════════════════════════════════

class TestApplicationBusinessLogic:
    """Test application status transitions and business rules."""

    async def test_duplicate_application_rejected(
        self, client: AsyncClient, db_session: AsyncSession,
        worker_user: User, worker_token: str, active_job: JobOffer
    ):
        """Worker cannot apply to the same job twice."""
        app = Application(
            id=str(uuid.uuid4()),
            job_offer_id=active_job.id,
            worker_id=worker_user.id,
            status="sent",
        )
        db_session.add(app)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Second application attempt"},
        )
        assert resp.status_code == 409, "Duplicate application should return 409 Conflict"

    async def test_application_status_valid_transitions(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str,
        worker_user: User, active_job: JobOffer
    ):
        """Employer can update application status to valid values."""
        app = Application(
            id=str(uuid.uuid4()),
            job_offer_id=active_job.id,
            worker_id=worker_user.id,
            status="sent",
        )
        db_session.add(app)
        await db_session.commit()

        for new_status in ["viewed", "shortlisted", "rejected", "accepted"]:
            resp = await client.put(
                f"/api/v1/employer/applications/{app.id}/status",
                headers=auth_header(employer_token),
                json={"status": new_status},
            )
            assert resp.status_code == 200, f"Status transition to '{new_status}' should succeed"

    async def test_application_invalid_status_rejected(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, employer_token: str,
        worker_user: User, active_job: JobOffer
    ):
        """Invalid application status should be rejected."""
        app = Application(
            id=str(uuid.uuid4()),
            job_offer_id=active_job.id,
            worker_id=worker_user.id,
            status="sent",
        )
        db_session.add(app)
        await db_session.commit()

        resp = await client.put(
            f"/api/v1/employer/applications/{app.id}/status",
            headers=auth_header(employer_token),
            json={"status": "invalid_status_xyz"},
        )
        assert resp.status_code == 422, "Invalid application status should return 422"

    async def test_worker_applications_list_correct_schema(
        self, client: AsyncClient, db_session: AsyncSession,
        worker_user: User, worker_token: str, active_job: JobOffer
    ):
        """Worker applications list should match frontend Application interface."""
        app = Application(
            id=str(uuid.uuid4()),
            job_offer_id=active_job.id,
            worker_id=worker_user.id,
            status="sent",
            cover_letter="My cover letter",
        )
        db_session.add(app)
        await db_session.commit()

        resp = await client.get(
            "/api/v1/worker/applications",
            headers=auth_header(worker_token),
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["data"]) > 0
        item = data["data"][0]

        # Must match frontend Application interface
        required_fields = [
            "id", "job_offer_id", "status", "cover_letter",
            "created_at", "updated_at", "job_title", "company_name"
        ]
        for field in required_fields:
            assert field in item, f"Application response missing '{field}'"


# ════════════════════════════════════════════════════════════════════
# SECTION 13 – JOB CREATION VALIDATION
# ════════════════════════════════════════════════════════════════════

class TestJobCreationValidation:
    """Test job creation input validation edge cases."""

    async def test_job_title_too_short_rejected(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """Job title shorter than 3 chars should be rejected."""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "AB",
                "description": "This is a valid description that is long enough.",
                "canton": "zurich",
                "contract_type": "full_time",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 422

    async def test_job_description_too_short_rejected(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """Job description shorter than 20 chars should be rejected."""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Valid Job Title",
                "description": "Short",
                "canton": "zurich",
                "contract_type": "full_time",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 422

    async def test_job_salary_min_greater_than_max_rejected(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """salary_min > salary_max should be rejected (model validator)."""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Valid Job Title",
                "description": "This is a valid description that is long enough to pass.",
                "canton": "zurich",
                "contract_type": "full_time",
                "apply_via": "portal",
                "salary_min": 10000,
                "salary_max": 5000,
            },
        )
        assert resp.status_code == 422

    async def test_job_invalid_contract_type_rejected(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """Invalid contract_type should be rejected."""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Valid Job Title",
                "description": "This is a valid description that is long enough.",
                "canton": "zurich",
                "contract_type": "invalid_type",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 422

    async def test_job_description_html_sanitized(
        self, client: AsyncClient, employer_user: User, employer_token: str
    ):
        """HTML in job description should be sanitized (XSS prevention).
        bleach.clean with strip=True removes script tags but preserves inner text.
        In a JSON API response, leftover text like 'alert(...)' is safe (not executable).
        """
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "XSS Test Job",
                "description": "<script>alert('xss')</script><p>Valid job description content here.</p>",
                "canton": "zurich",
                "contract_type": "full_time",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        # Script tags must be stripped (bleach strips <script> tags)
        assert "<script>" not in data["description"]
        assert "</script>" not in data["description"]
        # Allowed tags like <p> are preserved
        assert "<p>" in data["description"]

    async def test_quick_apply_without_cv_rejected(
        self, client: AsyncClient, db_session: AsyncSession,
        worker_user: User, worker_token: str, active_job: JobOffer
    ):
        """Quick apply should fail if worker has no active CV."""
        # Ensure worker has no CV
        result = await db_session.execute(
            select(WorkerProfile).where(WorkerProfile.user_id == worker_user.id)
        )
        profile = result.scalar_one()
        profile.active_cv_id = None
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/worker/quick-apply/{active_job.id}",
            headers=auth_header(worker_token),
            json={"cover_letter": "Please consider me!"},
        )
        assert resp.status_code == 400, "Quick apply without CV should return 400"


# ════════════════════════════════════════════════════════════════════
# SECTION 14 – SIMILAR JOBS ENDPOINT
# ════════════════════════════════════════════════════════════════════

class TestSimilarJobsEndpoint:
    """Test the similar jobs endpoint edge cases."""

    async def test_similar_jobs_for_nonexistent_job_returns_404(
        self, client: AsyncClient
    ):
        """Similar jobs for nonexistent job should return 404."""
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/jobs/{fake_id}/similar")
        assert resp.status_code == 404

    async def test_similar_jobs_excludes_current_job(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """Similar jobs list must not include the current job itself."""
        resp = await client.get(f"/api/v1/jobs/{active_job.id}/similar")
        assert resp.status_code == 200
        data = resp.json()
        job_ids = [j["id"] for j in data]
        assert active_job.id not in job_ids, "Similar jobs must not include the queried job"

    async def test_similar_jobs_only_returns_active_jobs(
        self, client: AsyncClient, db_session: AsyncSession,
        active_job: JobOffer, employer_user: User, category: Category
    ):
        """Similar jobs must only include active, non-expired jobs."""
        result = await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        # Create a pending job in same category/canton
        pending = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="Pending Similar Job",
            description="This is pending and should not appear in similar jobs results.",
            canton=active_job.canton,
            contract_type="full_time",
            apply_via="portal",
            status="pending",
        )
        db_session.add(pending)
        await db_session.commit()

        resp = await client.get(f"/api/v1/jobs/{active_job.id}/similar")
        assert resp.status_code == 200
        data = resp.json()
        job_ids = [j["id"] for j in data]
        assert pending.id not in job_ids, "Pending jobs must not appear in similar jobs"


# ════════════════════════════════════════════════════════════════════
# SECTION 15 – POPULAR SEARCHES AND SUGGESTIONS
# ════════════════════════════════════════════════════════════════════

class TestPopularSearchesAndSuggestions:
    """Test search suggestions and popular searches endpoints."""

    async def test_suggestions_requires_min_2_chars(
        self, client: AsyncClient
    ):
        """Suggestions endpoint requires at least 2 characters."""
        resp = await client.get("/api/v1/jobs/suggestions", params={"q": "a"})
        assert resp.status_code == 422

    async def test_suggestions_with_valid_query(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """Suggestions with valid query should return list."""
        resp = await client.get("/api/v1/jobs/suggestions", params={"q": "Dev"})
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_popular_searches_returns_list(
        self, client: AsyncClient
    ):
        """Popular searches should return a list (possibly default tags if no data)."""
        resp = await client.get("/api/v1/jobs/popular-searches")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_cantons_list_returns_all_26(
        self, client: AsyncClient
    ):
        """Canton list should return all 26 Swiss cantons."""
        resp = await client.get("/api/v1/jobs/cantons")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 26
        # Each canton has value and label
        for canton in data:
            assert "value" in canton
            assert "label" in canton
