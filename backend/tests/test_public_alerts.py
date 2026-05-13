"""Tests for the public (no-login) job alert system.

Covers:
  - POST /public-alerts/subscribe (create, dedup, per-email cap)
  - GET  /public-alerts/unsubscribe (archive + delete, idempotent)
  - scheduler check_public_alerts (cooldown, keyword match, last_sent_at update)
"""
from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from sqlalchemy import select, func

from app.models.public_job_alert import PublicJobAlert
from app.models.unsubscribed_email import UnsubscribedEmail
from app.models.job_offer import JobOffer
from app.models.employer_profile import EmployerProfile

from tests.conftest import TestSession


pytestmark = pytest.mark.asyncio


# ────────────────────────────────────────────────────────────────────
# Subscribe endpoint
# ────────────────────────────────────────────────────────────────────


class TestSubscribe:
    async def test_creates_alert(self, client, db_session):
        resp = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "test@example.com", "query": "monter"},
        )
        assert resp.status_code == 201

        rows = (await db_session.execute(select(PublicJobAlert))).scalars().all()
        assert len(rows) == 1
        alert = rows[0]
        assert alert.email == "test@example.com"
        assert alert.query == "monter"
        assert alert.query_key == "monter"
        assert alert.unsubscribe_token and len(alert.unsubscribe_token) >= 20
        assert alert.last_sent_at is None

    async def test_email_normalized_to_lowercase(self, client, db_session):
        resp = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "JAN.KOWALSKI@EXAMPLE.com", "query": "spawacz"},
        )
        assert resp.status_code == 201
        alert = (await db_session.execute(select(PublicJobAlert))).scalar_one()
        assert alert.email == "jan.kowalski@example.com"

    async def test_query_key_is_lowercased(self, client, db_session):
        resp = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "x@example.com", "query": "Monter Rusztowań"},
        )
        assert resp.status_code == 201
        alert = (await db_session.execute(select(PublicJobAlert))).scalar_one()
        assert alert.query == "Monter Rusztowań"
        assert alert.query_key == "monter rusztowań"

    async def test_dedup_same_email_query(self, client, db_session):
        body = {"email": "dup@example.com", "query": "kierowca"}
        r1 = await client.post("/api/v1/public-alerts/subscribe", json=body)
        r2 = await client.post("/api/v1/public-alerts/subscribe", json=body)
        assert r1.status_code == 201
        assert r2.status_code == 201

        count = (await db_session.execute(
            select(func.count(PublicJobAlert.id))
        )).scalar()
        assert count == 1  # second call should not create a duplicate

    async def test_dedup_is_case_insensitive_on_query(self, client, db_session):
        await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "case@example.com", "query": "Monter"},
        )
        await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "case@example.com", "query": "MONTER"},
        )
        count = (await db_session.execute(
            select(func.count(PublicJobAlert.id))
        )).scalar()
        assert count == 1

    async def test_max_alerts_per_email_cap(self, client, db_session):
        for i in range(10):
            r = await client.post(
                "/api/v1/public-alerts/subscribe",
                json={"email": "spam@example.com", "query": f"fraza{i}"},
            )
            assert r.status_code == 201

        # 11th should fail
        r = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "spam@example.com", "query": "frazaX"},
        )
        assert r.status_code == 400
        assert "limit" in r.json()["detail"].lower()

    async def test_rejects_invalid_email(self, client):
        r = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "not-an-email", "query": "monter"},
        )
        assert r.status_code == 422

    async def test_rejects_too_short_query(self, client):
        r = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "x@example.com", "query": "a"},
        )
        assert r.status_code == 422

    async def test_accepts_multiple_keywords(self, client, db_session):
        r = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "multi@example.com", "queries": ["Monter", "Hydraulik"]},
        )
        assert r.status_code == 201
        alert = (await db_session.execute(select(PublicJobAlert))).scalar_one()
        assert alert.queries == ["monter", "hydraulik"]
        assert alert.query == "Monter, Hydraulik"
        assert alert.query_key == "monter, hydraulik"

    async def test_rejects_empty_keywords_list(self, client):
        r = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "x@example.com", "queries": []},
        )
        assert r.status_code == 422

    async def test_drops_duplicate_keywords(self, client, db_session):
        r = await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "dup@example.com", "queries": ["monter", "MONTER", "Hydraulik"]},
        )
        assert r.status_code == 201
        alert = (await db_session.execute(select(PublicJobAlert))).scalar_one()
        assert alert.queries == ["monter", "Hydraulik".lower()]


# ────────────────────────────────────────────────────────────────────
# Unsubscribe endpoint
# ────────────────────────────────────────────────────────────────────


class TestUnsubscribe:
    async def test_archives_then_deletes(self, client, db_session):
        # First create an alert
        await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "bye@example.com", "query": "elektryk"},
        )
        alert = (await db_session.execute(select(PublicJobAlert))).scalar_one()
        token = alert.unsubscribe_token

        r = await client.get(f"/api/v1/public-alerts/unsubscribe?token={token}")
        assert r.status_code == 200

        # Alert must be gone
        remaining = (await db_session.execute(
            select(func.count(PublicJobAlert.id))
        )).scalar()
        assert remaining == 0

        # Archive row must exist with same email + query
        archived = (await db_session.execute(select(UnsubscribedEmail))).scalar_one()
        assert archived.email == "bye@example.com"
        assert archived.query == "elektryk"
        assert archived.unsubscribed_at is not None

    async def test_idempotent_invalid_token(self, client, db_session):
        r = await client.get(
            "/api/v1/public-alerts/unsubscribe?token=" + "x" * 40
        )
        assert r.status_code == 200
        # No archive row created for unknown token
        archived = (await db_session.execute(
            select(func.count(UnsubscribedEmail.id))
        )).scalar()
        assert archived == 0

    async def test_token_too_short_rejected(self, client):
        r = await client.get("/api/v1/public-alerts/unsubscribe?token=abc")
        assert r.status_code == 422

    async def test_double_unsubscribe_is_safe(self, client, db_session):
        await client.post(
            "/api/v1/public-alerts/subscribe",
            json={"email": "twice@example.com", "query": "logistyk"},
        )
        alert = (await db_session.execute(select(PublicJobAlert))).scalar_one()
        token = alert.unsubscribe_token

        r1 = await client.get(f"/api/v1/public-alerts/unsubscribe?token={token}")
        r2 = await client.get(f"/api/v1/public-alerts/unsubscribe?token={token}")
        assert r1.status_code == 200
        assert r2.status_code == 200
        # Archive should still only have one row (second call hits "not found")
        archived = (await db_session.execute(
            select(func.count(UnsubscribedEmail.id))
        )).scalar()
        assert archived == 1


# ────────────────────────────────────────────────────────────────────
# Scheduler: check_public_alerts
# ────────────────────────────────────────────────────────────────────


async def _make_job(
    db_session, employer_user, title: str, description: str = "Opis pracy.",
    created_offset_days: int = 0,
):
    from app.models.employer_profile import EmployerProfile
    profile = (await db_session.execute(
        select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
    )).scalar_one()

    now = datetime.now(timezone.utc)
    job = JobOffer(
        id=str(uuid.uuid4()),
        employer_id=profile.id,
        title=title,
        description=description,
        canton="zurich",
        contract_type="full_time",
        salary_type="monthly",
        is_remote="no",
        status="active",
        published_at=now,
        created_at=now - timedelta(days=created_offset_days),
        expires_at=now + timedelta(days=30),
    )
    db_session.add(job)
    await db_session.commit()
    return job


class TestSchedulerCheckPublicAlerts:
    """Scheduler job uses app.database.async_session — patch it to use TestSession."""

    @pytest.fixture(autouse=True)
    def patch_session(self):
        with patch("app.tasks.scheduler.async_session", TestSession):
            yield

    async def test_sends_email_when_match_found(
        self, db_session, employer_user
    ):
        await _make_job(db_session, employer_user, "Monter rusztowań Zürich")

        alert = PublicJobAlert(
            email="match@example.com",
            query="monter",
            query_key="monter",
        )
        db_session.add(alert)
        await db_session.commit()

        sent_emails = []

        def fake_send(to, subject, html):
            sent_emails.append((to, subject, html))
            return True

        with patch("app.services.email._send_email", side_effect=fake_send):
            from app.tasks.scheduler import check_public_alerts
            await check_public_alerts()

        assert len(sent_emails) == 1
        to, subject, html = sent_emails[0]
        assert to == "match@example.com"
        assert "monter" in subject.lower()
        assert "Monter rusztowań Zürich" in html
        assert "/alerty/wypisz?token=" in html

        # last_sent_at should be set on the alert
        await db_session.refresh(alert)
        assert alert.last_sent_at is not None

    async def test_no_email_when_no_match(self, db_session, employer_user):
        await _make_job(db_session, employer_user, "Kierowca C+E")

        alert = PublicJobAlert(
            email="nomatch@example.com",
            query="spawacz",
            query_key="spawacz",
        )
        db_session.add(alert)
        await db_session.commit()

        with patch("app.services.email._send_email") as m:
            m.return_value = True
            from app.tasks.scheduler import check_public_alerts
            await check_public_alerts()
            assert m.call_count == 0

        await db_session.refresh(alert)
        assert alert.last_sent_at is None

    async def test_weekly_cooldown_skips_recent_alerts(
        self, db_session, employer_user
    ):
        await _make_job(db_session, employer_user, "Monter konstrukcji stalowych")

        recent = datetime.now(timezone.utc) - timedelta(days=2)
        alert = PublicJobAlert(
            email="recent@example.com",
            query="monter",
            query_key="monter",
            last_sent_at=recent,
        )
        db_session.add(alert)
        await db_session.commit()

        with patch("app.services.email._send_email") as m:
            m.return_value = True
            from app.tasks.scheduler import check_public_alerts
            await check_public_alerts()
            assert m.call_count == 0  # cooldown not yet passed

        await db_session.refresh(alert)
        # last_sent_at unchanged (SQLite returns naive; compare as naive)
        last = alert.last_sent_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        assert abs((last - recent).total_seconds()) < 5

    async def test_resends_after_week(self, db_session, employer_user):
        await _make_job(db_session, employer_user, "Monter elewacji")

        eight_days_ago = datetime.now(timezone.utc) - timedelta(days=8)
        alert = PublicJobAlert(
            email="ready@example.com",
            query="monter",
            query_key="monter",
            last_sent_at=eight_days_ago,
        )
        db_session.add(alert)
        await db_session.commit()

        with patch("app.services.email._send_email") as m:
            m.return_value = True
            from app.tasks.scheduler import check_public_alerts
            await check_public_alerts()
            assert m.call_count == 1

        await db_session.refresh(alert)
        last = alert.last_sent_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        assert last > eight_days_ago

    async def test_only_includes_jobs_after_last_sent_at(
        self, db_session, employer_user
    ):
        """Jobs older than last_sent_at must NOT appear in the digest."""
        # Job created 10 days ago, before the last digest 8 days ago
        old_job = await _make_job(
            db_session, employer_user,
            "Monter starszy",
            created_offset_days=10,
        )
        # Job created today (after last digest)
        new_job = await _make_job(
            db_session, employer_user,
            "Monter najnowszy",
            created_offset_days=0,
        )

        eight_days_ago = datetime.now(timezone.utc) - timedelta(days=8)
        alert = PublicJobAlert(
            email="filter@example.com",
            query="monter",
            query_key="monter",
            last_sent_at=eight_days_ago,
        )
        db_session.add(alert)
        await db_session.commit()

        captured = []

        def fake_send(to, subject, html):
            captured.append(html)
            return True

        with patch("app.services.email._send_email", side_effect=fake_send):
            from app.tasks.scheduler import check_public_alerts
            await check_public_alerts()

        assert len(captured) == 1
        html = captured[0]
        assert new_job.title in html
        assert old_job.title not in html

    async def test_multi_keyword_or_match(self, db_session, employer_user):
        """Subscription with two keywords ('monter','hydraulik') matches a job for either."""
        await _make_job(db_session, employer_user, "Hydraulik instalator")

        alert = PublicJobAlert(
            email="multi@example.com",
            query="monter, hydraulik",
            query_key="monter, hydraulik",
            queries=["monter", "hydraulik"],
        )
        db_session.add(alert)
        await db_session.commit()

        captured = []

        def fake_send(to, subject, html):
            captured.append(html)
            return True

        with patch("app.services.email._send_email", side_effect=fake_send):
            from app.tasks.scheduler import check_public_alerts
            await check_public_alerts()

        assert len(captured) == 1
        assert "Hydraulik instalator" in captured[0]

    async def test_skips_non_active_jobs(self, db_session, employer_user):
        """pending/expired jobs must not be included."""
        from app.models.employer_profile import EmployerProfile
        profile = (await db_session.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == employer_user.id)
        )).scalar_one()

        now = datetime.now(timezone.utc)
        pending = JobOffer(
            id=str(uuid.uuid4()),
            employer_id=profile.id,
            title="Monter pending",
            description="Czeka na moderację",
            canton="zurich",
            contract_type="full_time",
            salary_type="monthly",
            is_remote="no",
            status="pending",
            expires_at=now + timedelta(days=30),
        )
        db_session.add(pending)
        await db_session.commit()

        alert = PublicJobAlert(
            email="pending@example.com",
            query="monter",
            query_key="monter",
        )
        db_session.add(alert)
        await db_session.commit()

        with patch("app.services.email._send_email") as m:
            m.return_value = True
            from app.tasks.scheduler import check_public_alerts
            await check_public_alerts()
            assert m.call_count == 0
