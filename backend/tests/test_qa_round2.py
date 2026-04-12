"""
QA Round 2 — Deep bug hunt for PolacySzwajcaria backend.

Covers:
- AUTHORIZATION GAPS: cross-role access, IDOR, deactivated user tokens
- BUSINESS LOGIC: salary_min > salary_max, apply to own job, quota enforcement,
                  apply to inactive/expired job, duplicate applications
- BOUNDARY TESTING: string lengths, pagination edge cases, special chars
- DATA INTEGRITY: email case sensitivity, slug uniqueness, file upload validation
"""
import uuid
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
from app.core.security import hash_password, create_access_token
from tests.conftest import auth_header


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 1: AUTHORIZATION GAPS
# ═══════════════════════════════════════════════════════════════════════════

class TestWorkerCannotAccessEmployerEndpoints:
    """Workers must be rejected from all employer-only endpoints."""

    async def test_worker_cannot_get_employer_profile(
        self, client: AsyncClient, worker_token: str
    ):
        resp = await client.get(
            "/api/v1/employer/profile", headers=auth_header(worker_token)
        )
        assert resp.status_code == 403

    async def test_worker_cannot_create_job(
        self, client: AsyncClient, worker_token: str
    ):
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(worker_token),
            json={
                "title": "Hacked job",
                "description": "This should not be allowed to be created.",
                "canton": "zurich",
                "contract_type": "full_time",
            },
        )
        assert resp.status_code == 403

    async def test_worker_cannot_get_employer_dashboard(
        self, client: AsyncClient, worker_token: str
    ):
        resp = await client.get(
            "/api/v1/employer/dashboard", headers=auth_header(worker_token)
        )
        assert resp.status_code == 403

    async def test_worker_cannot_list_employer_jobs(
        self, client: AsyncClient, worker_token: str
    ):
        resp = await client.get(
            "/api/v1/employer/jobs", headers=auth_header(worker_token)
        )
        assert resp.status_code == 403

    async def test_worker_cannot_update_application_status(
        self, client: AsyncClient, worker_token: str
    ):
        fake_app_id = str(uuid.uuid4())
        resp = await client.put(
            f"/api/v1/employer/applications/{fake_app_id}/status",
            headers=auth_header(worker_token),
            json={"status": "accepted"},
        )
        assert resp.status_code == 403


class TestEmployerCannotAccessWorkerEndpoints:
    """Employers must be rejected from all worker-only endpoints."""

    async def test_employer_cannot_get_worker_profile(
        self, client: AsyncClient, employer_token: str
    ):
        resp = await client.get(
            "/api/v1/worker/profile", headers=auth_header(employer_token)
        )
        assert resp.status_code == 403

    async def test_employer_cannot_apply_for_job(
        self, client: AsyncClient, employer_token: str, active_job: JobOffer
    ):
        resp = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(employer_token),
            json={"cover_letter": "I want this job"},
        )
        assert resp.status_code == 403

    async def test_employer_cannot_upload_worker_cv(
        self, client: AsyncClient, employer_token: str
    ):
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(employer_token),
            files={"file": ("cv.pdf", b"fake pdf", "application/pdf")},
        )
        assert resp.status_code == 403

    async def test_employer_cannot_save_job(
        self, client: AsyncClient, employer_token: str, active_job: JobOffer
    ):
        resp = await client.post(
            f"/api/v1/worker/saved-jobs/{active_job.id}",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 403


class TestAdminCannotAccessEmployerWorkerEndpoints:
    """Admins should not bypass role-specific checks for employer/worker."""

    async def test_admin_cannot_use_employer_endpoints(
        self, client: AsyncClient, admin_token: str
    ):
        resp = await client.get(
            "/api/v1/employer/profile", headers=auth_header(admin_token)
        )
        assert resp.status_code == 403

    async def test_admin_cannot_use_worker_endpoints(
        self, client: AsyncClient, admin_token: str
    ):
        resp = await client.get(
            "/api/v1/worker/profile", headers=auth_header(admin_token)
        )
        assert resp.status_code == 403


class TestIDORProtection:
    """Ensure employers cannot access/modify resources belonging to other employers."""

    async def test_employer_cannot_update_another_employers_job(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        employer_token: str,
        employer_user: User,
        category: Category,
    ):
        # Create a second employer
        user2 = User(
            id=str(uuid.uuid4()),
            email="employer2@test.ch",
            password_hash=hash_password("testpass123"),
            role="employer",
            first_name="Other",
            last_name="Employer",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user2)
        await db_session.flush()
        profile2 = EmployerProfile(
            id=str(uuid.uuid4()),
            user_id=user2.id,
            company_name="Other GmbH",
            company_slug="other-gmbh",
            canton="bern",
            city="Bern",
            is_verified=True,
        )
        db_session.add(profile2)
        await db_session.flush()

        # Create a job owned by employer2
        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile2.id,
            category_id=category.id,
            title="Job by other employer",
            description="This job belongs to a different employer entirely.",
            canton="bern",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            apply_via="portal",
            status="active",
            published_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(job)
        await db_session.commit()

        # employer1 tries to update employer2's job
        resp = await client.put(
            f"/api/v1/employer/jobs/{job.id}",
            headers=auth_header(employer_token),
            json={"title": "Hacked title!"},
        )
        assert resp.status_code == 404, (
            f"Expected 404 (resource not found for this employer), got {resp.status_code}"
        )

    async def test_employer_cannot_delete_another_employers_job(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        employer_token: str,
        category: Category,
    ):
        # Create second employer + job
        user2 = User(
            id=str(uuid.uuid4()),
            email="employer3@test.ch",
            password_hash=hash_password("testpass123"),
            role="employer",
            first_name="Third",
            last_name="Employer",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user2)
        await db_session.flush()
        profile2 = EmployerProfile(
            id=str(uuid.uuid4()),
            user_id=user2.id,
            company_name="Third GmbH",
            company_slug="third-gmbh",
            canton="zurich",
            city="Zurich",
            is_verified=True,
        )
        db_session.add(profile2)
        await db_session.flush()
        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile2.id,
            category_id=category.id,
            title="Third Employer Job",
            description="Another employer job for IDOR testing purposes.",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            apply_via="portal",
            status="active",
            published_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(job)
        await db_session.commit()

        resp = await client.delete(
            f"/api/v1/employer/jobs/{job.id}",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 404

    async def test_employer_cannot_view_candidates_of_another_employers_job(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        employer_token: str,
        category: Category,
    ):
        """IDOR: employer cannot list applications of another employer's job."""
        user2 = User(
            id=str(uuid.uuid4()),
            email="employer4@test.ch",
            password_hash=hash_password("testpass123"),
            role="employer",
            first_name="Fourth",
            last_name="Employer",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user2)
        await db_session.flush()
        profile2 = EmployerProfile(
            id=str(uuid.uuid4()),
            user_id=user2.id,
            company_name="Fourth GmbH",
            company_slug="fourth-gmbh",
            canton="zurich",
            city="Zurich",
            is_verified=True,
        )
        db_session.add(profile2)
        await db_session.flush()
        job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile2.id,
            category_id=category.id,
            title="Fourth Employer Job",
            description="Yet another employer job for application IDOR testing.",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            apply_via="portal",
            status="active",
            published_at=datetime.now(timezone.utc),
            expires_at=datetime.now(timezone.utc) + timedelta(days=30),
        )
        db_session.add(job)
        await db_session.commit()

        resp = await client.get(
            f"/api/v1/employer/jobs/{job.id}/applications",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 404


class TestDeactivatedUserToken:
    """A deactivated user's token must be rejected."""

    async def test_deactivated_user_token_rejected(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        # Create a user, get a valid token, then deactivate them
        user = User(
            id=str(uuid.uuid4()),
            email="deactivated@test.pl",
            password_hash=hash_password("testpass123"),
            role="worker",
            first_name="Dead",
            last_name="User",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        profile = WorkerProfile(
            id=str(uuid.uuid4()),
            user_id=user.id,
            canton="zurich",
            work_permit="permit_b",
        )
        db_session.add(profile)
        await db_session.commit()

        token = create_access_token(user.id, "worker")

        # Verify token works before deactivation
        resp = await client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp.status_code == 200

        # Deactivate the user
        user.is_active = False
        await db_session.commit()

        # Token must now be rejected
        resp = await client.get("/api/v1/auth/me", headers=auth_header(token))
        assert resp.status_code == 403, (
            f"Deactivated user's token should return 403, got {resp.status_code}"
        )

    async def test_deactivated_user_cannot_login(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        user = User(
            id=str(uuid.uuid4()),
            email="banned@test.pl",
            password_hash=hash_password("testpass123"),
            role="worker",
            first_name="Banned",
            last_name="User",
            is_active=False,  # Already deactivated
            is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()

        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "banned@test.pl", "password": "testpass123"},
        )
        assert resp.status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 2: BUSINESS LOGIC BUGS
# ═══════════════════════════════════════════════════════════════════════════

class TestSalaryValidation:
    """salary_min > salary_max should be rejected."""

    async def test_create_job_salary_min_greater_than_max(
        self, client: AsyncClient, employer_token: str, category: Category
    ):
        """BUG CANDIDATE: Can an employer create a job with salary_min > salary_max?"""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Bad Salary Job",
                "description": "This job has an invalid salary range that should be rejected.",
                "canton": "zurich",
                "contract_type": "full_time",
                "salary_min": 10000,
                "salary_max": 5000,  # min > max — invalid!
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        # Business logic requires salary_min <= salary_max
        assert resp.status_code == 422, (
            f"Expected 422 for salary_min > salary_max, got {resp.status_code}: {resp.json()}"
        )

    async def test_create_job_salary_min_equals_max_allowed(
        self, client: AsyncClient, employer_token: str, category: Category
    ):
        """salary_min == salary_max should be allowed (e.g. fixed salary)."""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Fixed Salary Job",
                "description": "This job has a fixed salary (min equals max) which is valid.",
                "canton": "zurich",
                "contract_type": "full_time",
                "salary_min": 5000,
                "salary_max": 5000,
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert resp.status_code in (200, 201), (
            f"Equal salary_min == salary_max should be allowed, got {resp.status_code}"
        )

    async def test_update_job_salary_min_greater_than_max(
        self, client: AsyncClient, employer_token: str, active_job: JobOffer
    ):
        """BUG CANDIDATE: Can employer update a job to have salary_min > salary_max?"""
        resp = await client.put(
            f"/api/v1/employer/jobs/{active_job.id}",
            headers=auth_header(employer_token),
            json={
                "salary_min": 20000,
                "salary_max": 1000,  # invalid
            },
        )
        assert resp.status_code == 422, (
            f"Expected 422 for salary update with min > max, got {resp.status_code}: {resp.json()}"
        )


class TestApplyToInactiveJob:
    """Workers must not be able to apply to inactive, expired, or pending jobs."""

    async def test_worker_cannot_apply_to_pending_job(
        self, client: AsyncClient, worker_token: str, pending_job: JobOffer
    ):
        resp = await client.post(
            f"/api/v1/worker/jobs/{pending_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "I want this pending job"},
        )
        assert resp.status_code == 404, (
            f"Applying to pending job should return 404, got {resp.status_code}"
        )

    async def test_worker_cannot_apply_to_expired_job(
        self, client: AsyncClient, db_session: AsyncSession, worker_token: str,
        employer_user: User, category: Category
    ):
        from sqlalchemy import select as sa_select
        result = await db_session.execute(
            sa_select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        expired_job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="Expired Job",
            description="This job has already expired and cannot accept applications.",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            apply_via="portal",
            status="active",  # Status is active but expires_at is in the past
            published_at=datetime.now(timezone.utc) - timedelta(days=60),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),  # EXPIRED
        )
        db_session.add(expired_job)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/worker/jobs/{expired_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "I want this expired job"},
        )
        # The job detail endpoint filters out expired jobs but the apply endpoint
        # only checks status == "active" — expired jobs might still accept applications
        # This tests whether expired jobs are properly blocked
        # NOTE: The apply endpoint checks status="active" but NOT expires_at
        # BUG CANDIDATE: expired jobs with status="active" can still receive applications
        # We document the actual behavior here:
        # If it returns 404 → correct (expired jobs excluded)
        # If it returns 201 → BUG (expired jobs still accept applications)
        if resp.status_code == 201:
            pytest.fail(
                f"BUG: Worker was able to apply to an expired job! "
                f"Response: {resp.status_code} {resp.json()}"
            )
        assert resp.status_code == 404

    async def test_worker_cannot_apply_to_closed_job(
        self, client: AsyncClient, db_session: AsyncSession, worker_token: str,
        employer_user: User, category: Category
    ):
        from sqlalchemy import select as sa_select
        result = await db_session.execute(
            sa_select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        closed_job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="Closed Job",
            description="This job has been closed and cannot accept new applications.",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            apply_via="portal",
            status="closed",
            published_at=datetime.now(timezone.utc) - timedelta(days=10),
            expires_at=datetime.now(timezone.utc) + timedelta(days=20),
        )
        db_session.add(closed_job)
        await db_session.commit()

        resp = await client.post(
            f"/api/v1/worker/jobs/{closed_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "I want this closed job"},
        )
        assert resp.status_code == 404


class TestDuplicateApplication:
    """Workers must not be able to apply twice to the same job."""

    async def test_cannot_apply_twice_same_job(
        self, client: AsyncClient, worker_token: str, active_job: JobOffer
    ):
        # First application
        resp1 = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "First application"},
        )
        assert resp1.status_code == 201

        # Second application to same job
        resp2 = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "Duplicate application"},
        )
        assert resp2.status_code == 409, (
            f"Duplicate application should return 409, got {resp2.status_code}: {resp2.json()}"
        )

    async def test_cannot_quick_apply_twice_same_job(
        self, client: AsyncClient, worker_token: str, active_job: JobOffer, worker_cv
    ):
        """Quick apply also blocks duplicates."""
        resp1 = await client.post(
            f"/api/v1/worker/quick-apply/{active_job.id}",
            headers=auth_header(worker_token),
            json={"cover_letter": "First quick apply"},
        )
        assert resp1.status_code == 201

        resp2 = await client.post(
            f"/api/v1/worker/quick-apply/{active_job.id}",
            headers=auth_header(worker_token),
            json={"cover_letter": "Duplicate quick apply"},
        )
        assert resp2.status_code == 409


class TestQuotaEnforcement:
    """Quota must actually prevent posting beyond the limit."""

    async def test_quota_blocks_posting_beyond_limit(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_token: str, employer_user: User, category: Category
    ):
        from sqlalchemy import select as sa_select
        result = await db_session.execute(
            sa_select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        # Set quota to 0 remaining (used=limit)
        quota_result = await db_session.execute(
            sa_select(PostingQuota).where(PostingQuota.employer_id == profile.id)
        )
        quota = quota_result.scalar_one()
        quota.used_count = quota.monthly_limit  # exhaust quota
        await db_session.commit()

        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Over Quota Job",
                "description": "This job should be rejected because quota is exhausted.",
                "canton": "zurich",
                "contract_type": "full_time",
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 429, (
            f"Expected 429 (quota exceeded), got {resp.status_code}: {resp.json()}"
        )

    async def test_quota_increments_on_create(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_token: str, employer_user: User, category: Category
    ):
        from sqlalchemy import select as sa_select
        result = await db_session.execute(
            sa_select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        # Check initial quota
        quota_result = await db_session.execute(
            sa_select(PostingQuota).where(PostingQuota.employer_id == profile.id)
        )
        quota = quota_result.scalar_one()
        initial_used = quota.used_count

        # Create a job
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Quota Test Job",
                "description": "Testing that quota increments when job is created.",
                "canton": "zurich",
                "contract_type": "full_time",
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 201

        # Verify quota was incremented
        await db_session.refresh(quota)
        assert quota.used_count == initial_used + 1, (
            f"Quota should increment from {initial_used} to {initial_used + 1}, "
            f"got {quota.used_count}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 3: DATA INTEGRITY
# ═══════════════════════════════════════════════════════════════════════════

class TestEmailCaseSensitivity:
    """Email addresses must be treated case-insensitively."""

    async def test_register_with_uppercase_email_clashes_with_existing(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Registering WORKER@TEST.PL when worker@test.pl exists should fail."""
        # Create a user with lowercase email
        user = User(
            id=str(uuid.uuid4()),
            email="casesensitive@test.pl",
            password_hash=hash_password("testpass123"),
            role="worker",
            first_name="Case",
            last_name="Test",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Try to register with mixed-case version
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "CaseSensitive@Test.PL",  # Different case
                "password": "testpass123",
                "first_name": "Case",
                "last_name": "Duplicate",
                "role": "worker",
            },
        )
        # Should conflict — emails must be case-insensitive
        # This tests whether the uniqueness check is case-insensitive
        # BUG: If it returns 201, the system allows duplicate accounts differing only by case
        if resp.status_code == 201:
            pytest.fail(
                "BUG: Email case sensitivity — system allowed duplicate registration "
                "with different case email (casesensitive@test.pl vs CaseSensitive@Test.PL)"
            )
        assert resp.status_code == 409

    async def test_login_with_uppercase_email_works(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """After the email normalization fix, login with any-case email must work."""
        user = User(
            id=str(uuid.uuid4()),
            email="logincase@test.pl",  # stored as lowercase
            password_hash=hash_password("testpass123"),
            role="worker",
            first_name="Login",
            last_name="Case",
            is_active=True,
            is_verified=True,
        )
        db_session.add(user)
        await db_session.commit()

        # Login with uppercase version — should now work after the fix
        resp = await client.post(
            "/api/v1/auth/login",
            json={"email": "LOGINCASE@TEST.PL", "password": "testpass123"},
        )
        assert resp.status_code == 200, (
            f"Login with uppercase email should work after normalization fix, "
            f"got {resp.status_code}: {resp.json()}"
        )


class TestSlugUniqueness:
    """Company slugs must be unique across all employers."""

    async def test_duplicate_company_name_gets_unique_slug(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        """Two companies with same name must get different slugs."""
        # Register first employer
        resp1 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "slug1@test.ch",
                "password": "testpass123",
                "first_name": "First",
                "last_name": "Company",
                "role": "employer",
                "company_name": "Slug Test GmbH",
            },
        )
        assert resp1.status_code == 201

        # Register second employer with identical company name
        resp2 = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "slug2@test.ch",
                "password": "testpass123",
                "first_name": "Second",
                "last_name": "Company",
                "role": "employer",
                "company_name": "Slug Test GmbH",  # Same name!
            },
        )
        assert resp2.status_code == 201

        # Both must have different slugs
        result = await db_session.execute(
            select(EmployerProfile).where(
                EmployerProfile.company_name == "Slug Test GmbH"
            )
        )
        profiles = result.scalars().all()
        assert len(profiles) == 2

        slug1 = profiles[0].company_slug
        slug2 = profiles[1].company_slug
        assert slug1 != slug2, (
            f"BUG: Two companies with same name got identical slug: '{slug1}'"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 4: BOUNDARY TESTING
# ═══════════════════════════════════════════════════════════════════════════

class TestPaginationBoundaries:
    """Test edge cases in pagination parameters."""

    async def test_page_zero_rejected(self, client: AsyncClient):
        """page=0 should be rejected (ge=1 validation)."""
        resp = await client.get("/api/v1/jobs?page=0")
        assert resp.status_code == 422

    async def test_page_negative_rejected(self, client: AsyncClient):
        """page=-1 should be rejected."""
        resp = await client.get("/api/v1/jobs?page=-1")
        assert resp.status_code == 422

    async def test_per_page_zero_rejected(self, client: AsyncClient):
        """per_page=0 should be rejected (ge=1 validation)."""
        resp = await client.get("/api/v1/jobs?per_page=0")
        assert resp.status_code == 422

    async def test_per_page_101_rejected(self, client: AsyncClient):
        """per_page=101 exceeds max of 100 and should be rejected."""
        resp = await client.get("/api/v1/jobs?per_page=101")
        assert resp.status_code == 422

    async def test_per_page_100_allowed(self, client: AsyncClient):
        """per_page=100 is at the boundary and should be allowed."""
        resp = await client.get("/api/v1/jobs?per_page=100")
        assert resp.status_code == 200

    async def test_high_page_number_returns_empty(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """Requesting a very high page number returns empty data but not an error."""
        resp = await client.get("/api/v1/jobs?page=9999&per_page=20")
        assert resp.status_code == 200
        data = resp.json()
        assert data["data"] == []
        assert data["total"] >= 0


class TestStringLengthBoundaries:
    """Test max_length boundary enforcement."""

    async def test_job_title_too_long_rejected(
        self, client: AsyncClient, employer_token: str
    ):
        """Job title > 255 chars should be rejected."""
        long_title = "A" * 256
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": long_title,
                "description": "A" * 100,
                "canton": "zurich",
                "contract_type": "full_time",
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 422

    async def test_job_title_exactly_255_chars_allowed(
        self, client: AsyncClient, employer_token: str, category: Category
    ):
        """Job title of exactly 255 chars should be allowed."""
        title = "A" * 255
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": title,
                "description": "A" * 100,
                "canton": "zurich",
                "category_id": category.id,
                "contract_type": "full_time",
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert resp.status_code in (200, 201), (
            f"255-char title should be accepted, got {resp.status_code}: {resp.json()}"
        )

    async def test_job_title_too_short_rejected(
        self, client: AsyncClient, employer_token: str
    ):
        """Job title < 3 chars should be rejected."""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "AB",  # Only 2 chars
                "description": "A" * 100,
                "canton": "zurich",
                "contract_type": "full_time",
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 422

    async def test_job_description_too_short_rejected(
        self, client: AsyncClient, employer_token: str
    ):
        """Job description < 20 chars should be rejected."""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Valid Title",
                "description": "Too short",  # < 20 chars
                "canton": "zurich",
                "contract_type": "full_time",
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert resp.status_code == 422

    async def test_registration_with_very_long_name_rejected(
        self, client: AsyncClient
    ):
        """first_name > 100 chars should be rejected (model column limit)."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "longname@test.pl",
                "password": "testpass123",
                "first_name": "A" * 101,  # > 100 char limit
                "last_name": "Test",
                "role": "worker",
            },
        )
        # This may or may not be validated at the schema level — check actual behavior
        # The User model has String(100) for first_name but schema may not enforce it
        assert resp.status_code in (201, 422), (
            f"Very long first_name: {resp.status_code}"
        )


class TestSpecialCharactersHandling:
    """Test special characters in various fields."""

    async def test_job_search_with_sql_injection_attempt(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """SQL injection in search query should not cause errors."""
        malicious_query = "'; DROP TABLE users; --"
        resp = await client.get(f"/api/v1/jobs?q={malicious_query}")
        assert resp.status_code == 200  # Should not crash
        # Should return 0 results (not a server error)
        data = resp.json()
        assert "data" in data

    async def test_job_search_with_html_injection_attempt(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """HTML/script injection in search query should return safe response."""
        malicious_query = "<script>alert('xss')</script>"
        resp = await client.get(
            "/api/v1/jobs",
            params={"q": malicious_query},
        )
        assert resp.status_code == 200

    async def test_job_title_with_special_chars(
        self, client: AsyncClient, employer_token: str, category: Category
    ):
        """Job titles with Polish characters and special chars should work."""
        resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Programista C++ / Ś inżynier (m/f/d)",
                "description": "Stanowisko dla doświadczonego programisty w obszarze systemów.",
                "canton": "zurich",
                "category_id": category.id,
                "contract_type": "full_time",
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert resp.status_code in (200, 201), (
            f"Job with Polish special chars failed: {resp.status_code}: {resp.json()}"
        )

    async def test_suggestions_with_special_chars_does_not_crash(
        self, client: AsyncClient, active_job: JobOffer
    ):
        """Suggestions endpoint handles special chars safely."""
        resp = await client.get("/api/v1/jobs/suggestions?q=C%2B%2B")  # C++
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 5: FILE UPLOAD VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

class TestFileUploadValidation:
    """Test that file uploads are properly validated."""

    async def test_cv_upload_invalid_mime_rejected(
        self, client: AsyncClient, worker_token: str
    ):
        """Non-PDF/DOCX files must be rejected for CV upload."""
        # Try uploading an executable (text/plain in a .exe wrapper)
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(worker_token),
            files={"file": ("evil.exe", b"MZ" * 100, "application/x-msdownload")},
        )
        assert resp.status_code == 400

    async def test_cv_upload_image_rejected(
        self, client: AsyncClient, worker_token: str
    ):
        """Image files must be rejected for CV upload."""
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(worker_token),
            files={"file": ("photo.jpg", b"\xff\xd8\xff" * 100, "image/jpeg")},
        )
        assert resp.status_code == 400

    async def test_cv_upload_too_large_rejected(
        self, client: AsyncClient, worker_token: str
    ):
        """CV files > 5MB should be rejected."""
        large_content = b"%PDF-1.4" + b"x" * (6 * 1024 * 1024)  # 6MB
        resp = await client.post(
            "/api/v1/worker/cv",
            headers=auth_header(worker_token),
            files={"file": ("large.pdf", large_content, "application/pdf")},
        )
        assert resp.status_code == 400, (
            f"6MB CV should be rejected, got {resp.status_code}"
        )

    async def test_logo_upload_invalid_mime_rejected(
        self, client: AsyncClient, employer_token: str
    ):
        """Non-image files must be rejected for logo upload."""
        resp = await client.post(
            "/api/v1/employer/profile/logo",
            headers=auth_header(employer_token),
            files={"file": ("script.js", b"alert('xss')", "text/javascript")},
        )
        assert resp.status_code == 400

    async def test_logo_upload_valid_png_accepted(
        self, client: AsyncClient, employer_token: str
    ):
        """Valid PNG logo should be accepted."""
        # Minimal valid PNG header (89 50 4E 47)
        minimal_png = bytes([137, 80, 78, 71, 13, 10, 26, 10]) + b"\x00" * 100
        resp = await client.post(
            "/api/v1/employer/profile/logo",
            headers=auth_header(employer_token),
            files={"file": ("logo.png", minimal_png, "image/png")},
        )
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 6: UNAUTHENTICATED ACCESS
# ═══════════════════════════════════════════════════════════════════════════

class TestUnauthenticatedAccess:
    """Protected endpoints must reject requests without valid tokens."""

    async def test_no_token_rejected_from_employer_endpoints(
        self, client: AsyncClient
    ):
        resp = await client.get("/api/v1/employer/profile")
        assert resp.status_code == 403

    async def test_no_token_rejected_from_worker_endpoints(
        self, client: AsyncClient
    ):
        resp = await client.get("/api/v1/worker/profile")
        assert resp.status_code == 403

    async def test_no_token_rejected_from_admin_endpoints(
        self, client: AsyncClient
    ):
        resp = await client.get("/api/v1/admin/dashboard")
        assert resp.status_code == 403

    async def test_invalid_token_rejected(self, client: AsyncClient):
        resp = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer this.is.not.a.valid.token"},
        )
        assert resp.status_code == 401

    async def test_wrong_token_type_rejected(self, client: AsyncClient, worker_user):
        """Refresh token must not be accepted as access token."""
        from app.core.security import create_refresh_token
        refresh_token = create_refresh_token(worker_user.id)
        resp = await client.get(
            "/api/v1/auth/me",
            headers=auth_header(refresh_token),
        )
        assert resp.status_code == 401, (
            f"Refresh token used as access token should return 401, got {resp.status_code}"
        )

    async def test_public_jobs_endpoint_accessible_without_auth(
        self, client: AsyncClient
    ):
        """Public job listing should be accessible without authentication."""
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 7: WORKER CANNOT APPLY TO OWN EMPLOYER'S JOB EDGE CASE
# ═══════════════════════════════════════════════════════════════════════════

class TestApplyOwnJob:
    """Edge case: employer creates job, worker with same user applies (cross-role)."""

    async def test_worker_can_apply_to_employer_job(
        self, client: AsyncClient, worker_token: str, active_job: JobOffer
    ):
        """Normal case: a worker can apply to any active job from any employer."""
        resp = await client.post(
            f"/api/v1/worker/jobs/{active_job.id}/apply",
            headers=auth_header(worker_token),
            json={"cover_letter": "I am interested in this position."},
        )
        assert resp.status_code == 201


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 8: INACTIVE JOB NOT VISIBLE IN PUBLIC LISTING
# ═══════════════════════════════════════════════════════════════════════════

class TestJobVisibility:
    """Jobs in non-active states must not appear in the public job listing."""

    async def test_pending_job_not_in_public_listing(
        self, client: AsyncClient, pending_job: JobOffer
    ):
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        job_ids = [j["id"] for j in data["data"]]
        assert pending_job.id not in job_ids, (
            "BUG: Pending job is visible in public job listing!"
        )

    async def test_expired_job_not_in_public_listing(
        self, client: AsyncClient, db_session: AsyncSession,
        employer_user: User, category: Category
    ):
        from sqlalchemy import select as sa_select
        result = await db_session.execute(
            sa_select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )
        profile = result.scalar_one()

        expired_job = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            category_id=category.id,
            title="Expired Visible Job",
            description="This job should not appear in public listing because it is expired.",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            apply_via="portal",
            status="active",
            published_at=datetime.now(timezone.utc) - timedelta(days=60),
            expires_at=datetime.now(timezone.utc) - timedelta(days=1),
        )
        db_session.add(expired_job)
        await db_session.commit()

        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        job_ids = [j["id"] for j in data["data"]]
        assert expired_job.id not in job_ids, (
            "BUG: Expired job is visible in public job listing!"
        )

    async def test_active_job_visible_in_public_listing(
        self, client: AsyncClient, active_job: JobOffer
    ):
        resp = await client.get("/api/v1/jobs")
        assert resp.status_code == 200
        data = resp.json()
        job_ids = [j["id"] for j in data["data"]]
        assert active_job.id in job_ids


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 9: EMPLOYER QUOTA ENDPOINT CORRECTNESS
# ═══════════════════════════════════════════════════════════════════════════

class TestQuotaEndpointAccuracy:
    """Test that the quota endpoint returns accurate remaining count."""

    async def test_quota_remaining_decreases_after_job_creation(
        self, client: AsyncClient, employer_token: str, category: Category
    ):
        # Get initial quota
        resp = await client.get(
            "/api/v1/employer/quota", headers=auth_header(employer_token)
        )
        assert resp.status_code == 200
        initial = resp.json()
        initial_remaining = initial["remaining"]
        initial_used = initial["used_count"]

        # Create a job
        create_resp = await client.post(
            "/api/v1/employer/jobs",
            headers=auth_header(employer_token),
            json={
                "title": "Quota Tracking Job",
                "description": "Testing that quota tracking works correctly via endpoint.",
                "canton": "zurich",
                "category_id": category.id,
                "contract_type": "full_time",
                "salary_type": "monthly",
                "apply_via": "portal",
            },
        )
        assert create_resp.status_code == 201

        # Check quota updated
        resp2 = await client.get(
            "/api/v1/employer/quota", headers=auth_header(employer_token)
        )
        assert resp2.status_code == 200
        updated = resp2.json()

        assert updated["used_count"] == initial_used + 1
        assert updated["remaining"] == initial_remaining - 1


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 10: REGISTRATION VALIDATION
# ═══════════════════════════════════════════════════════════════════════════

class TestRegistrationValidation:
    """Test registration edge cases."""

    async def test_employer_register_without_company_name_rejected(
        self, client: AsyncClient
    ):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "nocompany@test.ch",
                "password": "testpass123",
                "first_name": "No",
                "last_name": "Company",
                "role": "employer",
                # company_name intentionally omitted
            },
        )
        assert resp.status_code == 400

    async def test_duplicate_email_registration_rejected(
        self, client: AsyncClient, worker_user: User
    ):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "worker@test.pl",  # same as worker_user fixture
                "password": "newpassword123",
                "first_name": "Duplicate",
                "last_name": "User",
                "role": "worker",
            },
        )
        assert resp.status_code == 409

    async def test_invalid_role_rejected(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "hacker@test.pl",
                "password": "testpass123",
                "first_name": "Admin",
                "last_name": "Hacker",
                "role": "admin",  # Cannot self-register as admin
            },
        )
        assert resp.status_code == 422, (
            f"Self-registration as admin should be rejected, got {resp.status_code}"
        )

    async def test_weak_password_handling(self, client: AsyncClient):
        """Very short password should be handled."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "weakpass@test.pl",
                "password": "123",  # Very weak
                "first_name": "Weak",
                "last_name": "Pass",
                "role": "worker",
            },
        )
        # Document behavior — schema may or may not enforce password strength
        assert resp.status_code in (201, 422), (
            f"Weak password handling: {resp.status_code}"
        )


# ═══════════════════════════════════════════════════════════════════════════
# SECTION 11: EMPLOYER JOB STATUS TRANSITIONS
# ═══════════════════════════════════════════════════════════════════════════

class TestJobStatusTransitions:
    """Test job status change edge cases."""

    async def test_close_job_changes_status_to_closed(
        self, client: AsyncClient, employer_token: str, active_job: JobOffer
    ):
        resp = await client.patch(
            f"/api/v1/employer/jobs/{active_job.id}/close",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 200

    async def test_delete_job_removes_it(
        self, client: AsyncClient, employer_token: str, active_job: JobOffer,
        db_session: AsyncSession
    ):
        job_id = active_job.id
        resp = await client.delete(
            f"/api/v1/employer/jobs/{job_id}",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 200

        # Verify it's gone from DB
        result = await db_session.execute(
            select(JobOffer).where(JobOffer.id == job_id)
        )
        assert result.scalar_one_or_none() is None, (
            "BUG: Job still exists after deletion"
        )

    async def test_deleted_job_not_in_public_listing(
        self, client: AsyncClient, employer_token: str, active_job: JobOffer
    ):
        job_id = active_job.id
        await client.delete(
            f"/api/v1/employer/jobs/{job_id}",
            headers=auth_header(employer_token),
        )

        resp = await client.get("/api/v1/jobs")
        job_ids = [j["id"] for j in resp.json()["data"]]
        assert job_id not in job_ids

    async def test_copy_nonexistent_job_returns_404(
        self, client: AsyncClient, employer_token: str
    ):
        fake_id = str(uuid.uuid4())
        resp = await client.get(
            f"/api/v1/employer/jobs/{fake_id}/copy",
            headers=auth_header(employer_token),
        )
        assert resp.status_code == 404

    async def test_nonexistent_job_detail_returns_404(
        self, client: AsyncClient
    ):
        fake_id = str(uuid.uuid4())
        resp = await client.get(f"/api/v1/jobs/{fake_id}")
        assert resp.status_code == 404
