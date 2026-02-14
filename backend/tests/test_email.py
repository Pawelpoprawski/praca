"""Tests for email service."""
import os
from unittest.mock import patch, MagicMock
import pytest


class TestEmailDisabled:
    """When EMAIL_ENABLED=false, emails are logged but not sent."""

    def test_send_verification_returns_true(self):
        from app.services.email import send_verification_email
        result = send_verification_email("test@test.pl", "Jan", "token123")
        assert result is True

    def test_send_password_reset_returns_true(self):
        from app.services.email import send_password_reset_email
        result = send_password_reset_email("test@test.pl", "Jan", "token123")
        assert result is True

    def test_send_application_notification_returns_true(self):
        from app.services.email import send_application_notification
        result = send_application_notification(
            "hr@test.ch", "HR", "Developer", "Jan Kowalski"
        )
        assert result is True

    def test_send_status_change_returns_true(self):
        from app.services.email import send_status_change_notification
        result = send_status_change_notification(
            "worker@test.pl", "Jan", "Developer", "Test GmbH", "shortlisted"
        )
        assert result is True


class TestEmailEnabled:
    """When EMAIL_ENABLED=true, Resend API is called."""

    @pytest.fixture(autouse=True)
    def enable_email(self):
        from app.config import get_settings as _gs
        _gs.cache_clear()
        os.environ["EMAIL_ENABLED"] = "true"
        os.environ["RESEND_API_KEY"] = "re_test_key"
        yield
        os.environ["EMAIL_ENABLED"] = "false"
        os.environ.pop("RESEND_API_KEY", None)
        _gs.cache_clear()

    @patch("app.services.email._resend")
    def test_send_email_calls_resend(self, mock_resend):
        mock_resend.Emails.send.return_value = {"id": "test-id"}

        from app.services.email import send_verification_email
        result = send_verification_email("test@test.pl", "Jan", "token123")

        assert result is True
        mock_resend.Emails.send.assert_called_once()
        call_args = mock_resend.Emails.send.call_args[0][0]
        assert call_args["to"] == ["test@test.pl"]
        assert "Zweryfikuj" in call_args["subject"]

    @patch("app.services.email._resend")
    def test_send_email_failure_returns_false(self, mock_resend):
        mock_resend.Emails.send.side_effect = Exception("API error")

        from app.services.email import send_verification_email
        result = send_verification_email("test@test.pl", "Jan", "token123")

        assert result is False
