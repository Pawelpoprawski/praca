import logging

try:
    import resend as _resend
except ImportError:
    _resend = None  # type: ignore

from app.config import get_settings

logger = logging.getLogger(__name__)


def _send_email(to: str, subject: str, html: str) -> bool:
    """Send an email via Resend. Returns True on success."""
    settings = get_settings()

    if not settings.EMAIL_ENABLED:
        logger.info("Email disabled - would send to %s: %s", to, subject)
        return True

    try:
        if _resend is None:
            raise RuntimeError("resend package is not installed")
        _resend.api_key = settings.RESEND_API_KEY

        _resend.Emails.send({
            "from": settings.EMAIL_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        })
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def send_verification_email(to: str, name: str, token: str) -> bool:
    settings = get_settings()
    link = f"{settings.FRONTEND_URL}/api/v1/auth/verify-email/{token}"
    html = f"""
    <h2>Witaj {name}!</h2>
    <p>Dziękujemy za rejestrację w PolacySzwajcaria.</p>
    <p>Kliknij poniższy link, aby zweryfikować swój adres email:</p>
    <p><a href="{link}" style="display:inline-block;padding:12px 24px;background:#dc2626;color:white;text-decoration:none;border-radius:8px;">Zweryfikuj email</a></p>
    <p>Jeśli nie zakładałeś konta, zignoruj tę wiadomość.</p>
    """
    return _send_email(to, "Zweryfikuj swój adres email - PolacySzwajcaria", html)


def send_password_reset_email(to: str, name: str, token: str) -> bool:
    settings = get_settings()
    link = f"{settings.FRONTEND_URL}/reset-password?token={token}"
    html = f"""
    <h2>Resetowanie hasła</h2>
    <p>Cześć {name},</p>
    <p>Otrzymaliśmy prośbę o reset hasła do Twojego konta.</p>
    <p><a href="{link}" style="display:inline-block;padding:12px 24px;background:#dc2626;color:white;text-decoration:none;border-radius:8px;">Zmień hasło</a></p>
    <p>Link wygasa za 1 godzinę. Jeśli nie prosiłeś o reset, zignoruj tę wiadomość.</p>
    """
    return _send_email(to, "Reset hasła - PolacySzwajcaria", html)


def send_application_notification(
    employer_email: str, employer_name: str, job_title: str, applicant_name: str
) -> bool:
    html = f"""
    <h2>Nowa aplikacja!</h2>
    <p>Cześć {employer_name},</p>
    <p><strong>{applicant_name}</strong> aplikował/a na Twoje ogłoszenie: <strong>{job_title}</strong>.</p>
    <p>Zaloguj się do panelu pracodawcy, aby przejrzeć kandydatów.</p>
    """
    return _send_email(
        employer_email,
        f"Nowa aplikacja na: {job_title} - PolacySzwajcaria",
        html,
    )


def send_status_change_notification(
    worker_email: str, worker_name: str, job_title: str, company_name: str, new_status: str
) -> bool:
    status_labels = {
        "viewed": "przejrzana",
        "shortlisted": "na krótkiej liście",
        "accepted": "zaakceptowana",
        "rejected": "odrzucona",
    }
    status_text = status_labels.get(new_status, new_status)
    html = f"""
    <h2>Aktualizacja statusu aplikacji</h2>
    <p>Cześć {worker_name},</p>
    <p>Status Twojej aplikacji na stanowisko <strong>{job_title}</strong>
    w firmie <strong>{company_name}</strong> został zmieniony na: <strong>{status_text}</strong>.</p>
    <p>Zaloguj się do panelu pracownika, aby zobaczyć szczegóły.</p>
    """
    return _send_email(
        worker_email,
        f"Zmiana statusu aplikacji: {job_title} - PolacySzwajcaria",
        html,
    )
