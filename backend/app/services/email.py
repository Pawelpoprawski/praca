import base64
import logging

try:
    import resend as _resend
except ImportError:
    _resend = None  # type: ignore

from app.config import get_settings

logger = logging.getLogger(__name__)


def _send_email(to: str, subject: str, html: str, attachments: list[dict] | None = None) -> bool:
    """Send an email via Resend. Returns True on success.

    attachments: optional list of {"filename": str, "content": bytes}.
    """
    settings = get_settings()

    if not settings.EMAIL_ENABLED:
        logger.info("Email disabled - would send to %s: %s", to, subject)
        return True

    try:
        if _resend is None:
            raise RuntimeError("resend package is not installed")
        _resend.api_key = settings.RESEND_API_KEY

        payload: dict = {
            "from": settings.EMAIL_FROM,
            "to": [to],
            "subject": subject,
            "html": html,
        }
        if attachments:
            payload["attachments"] = [
                {
                    "filename": a["filename"],
                    "content": base64.b64encode(a["content"]).decode("ascii") if isinstance(a["content"], (bytes, bytearray)) else a["content"],
                }
                for a in attachments
            ]

        _resend.Emails.send(payload)
        return True
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to, e)
        return False


def send_verification_email(to: str, name: str, token: str) -> bool:
    settings = get_settings()
    link = f"{settings.FRONTEND_URL}/verify-email/{token}"
    html = f"""
    <h2>Witaj {name}!</h2>
    <p>Dziękujemy za rejestrację w Praca w Szwajcarii.</p>
    <p>Kliknij poniższy link, aby zweryfikować swój adres email:</p>
    <p><a href="{link}" style="display:inline-block;padding:12px 24px;background:#dc2626;color:white;text-decoration:none;border-radius:8px;">Zweryfikuj email</a></p>
    <p>Jeśli nie zakładałeś konta, zignoruj tę wiadomość.</p>
    """
    return _send_email(to, "Zweryfikuj swój adres email - Praca w Szwajcarii", html)


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
    return _send_email(to, "Reset hasła - Praca w Szwajcarii", html)


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
        f"Nowa aplikacja na: {job_title} - Praca w Szwajcarii",
        html,
    )


def send_external_application(
    *,
    to: str,
    job_title: str,
    job_id: str,
    company_name: str | None,
    applicant_first_name: str,
    applicant_last_name: str,
    applicant_email: str,
    applicant_phone: str,
    cv_filename: str,
    cv_bytes: bytes,
) -> bool:
    """Wysyla pracodawcy aplikacje zewnetrzna (kandydat bez konta) z CV w zalaczniku.

    HTML jest stylizowany pod Hays palette (navy + corporate red).
    """
    settings = get_settings()
    site_url = settings.FRONTEND_URL.rstrip("/")
    job_url = f"{site_url}/oferty/{job_id}"
    full_name = f"{applicant_first_name} {applicant_last_name}".strip()
    company_label = company_name or "Pracodawca"

    subject = f"Nowa aplikacja - {job_title}"

    html = f"""\
<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Nowa aplikacja</title>
</head>
<body style="margin:0;padding:0;background:#F5F6F8;font-family:Roboto,Arial,sans-serif;color:#1A1A1A;line-height:1.6;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#F5F6F8;">
    <tr>
      <td align="center" style="padding:32px 16px;">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" style="max-width:600px;width:100%;background:#FFFFFF;border:1px solid #E0E3E8;border-radius:8px;overflow:hidden;">
          <!-- Header navy with red accent -->
          <tr>
            <td style="background:#0D2240;padding:32px 40px;color:#FFFFFF;">
              <div style="width:48px;height:3px;background:#E1002A;margin-bottom:16px;"></div>
              <div style="font-family:'Roboto Slab',Georgia,serif;font-size:0.85rem;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;color:rgba(255,255,255,0.7);margin-bottom:8px;">Nowa aplikacja</div>
              <div style="font-family:'Roboto Slab',Georgia,serif;font-size:1.5rem;font-weight:700;line-height:1.3;color:#FFFFFF;">{_escape(job_title)}</div>
              <div style="margin-top:8px;font-size:0.9rem;color:rgba(255,255,255,0.7);">{_escape(company_label)}</div>
            </td>
          </tr>

          <!-- Body -->
          <tr>
            <td style="padding:32px 40px;">
              <p style="margin:0 0 16px;color:#555;">
                Otrzymano nową aplikację na ofertę <strong style="color:#0D2240;">{_escape(job_title)}</strong>.
                Poniżej dane kandydata oraz załączone CV.
              </p>

              <!-- Candidate info -->
              <h3 style="font-family:'Roboto Slab',Georgia,serif;font-size:1.05rem;font-weight:700;color:#0D2240;margin:24px 0 12px;border-bottom:1px solid #E0E3E8;padding-bottom:8px;">
                Dane kandydata
              </h3>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
                {_email_row("Imię i nazwisko", _escape(full_name))}
                {_email_row("Email", f'<a href="mailto:{_escape(applicant_email)}" style="color:#E1002A;text-decoration:none;">{_escape(applicant_email)}</a>')}
                {_email_row("Telefon", f'<a href="tel:{_escape(applicant_phone)}" style="color:#E1002A;text-decoration:none;">{_escape(applicant_phone)}</a>')}
                {_email_row("CV", f'<span style="color:#0D2240;">{_escape(cv_filename)}</span> <span style="color:#888;font-size:0.85rem;">(załącznik)</span>')}
              </table>

              <!-- CTA -->
              <div style="margin-top:32px;text-align:center;">
                <a href="{_escape(job_url)}"
                   style="display:inline-block;background:#E1002A;color:#FFFFFF;padding:12px 28px;font-weight:500;font-size:0.95rem;text-decoration:none;border-radius:4px;">
                  Zobacz ogłoszenie
                </a>
              </div>

              <p style="margin:32px 0 0;font-size:0.85rem;color:#888;border-top:1px solid #E0E3E8;padding-top:20px;">
                Wiadomość wygenerowana automatycznie przez portal
                <a href="{_escape(site_url)}" style="color:#E1002A;text-decoration:none;">Praca w Szwajcarii</a>.
                Nie odpowiadaj na ten adres — odpisuj bezpośrednio na email kandydata.
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#F5F6F8;padding:20px 40px;text-align:center;font-size:0.8rem;color:#888;border-top:1px solid #E0E3E8;">
              © Praca w Szwajcarii — Portal pracy specjalistów
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
"""

    return _send_email(
        to,
        subject,
        html,
        attachments=[{"filename": cv_filename, "content": cv_bytes}],
    )


def _escape(text: str) -> str:
    """Minimalne HTML-escape (chroni przed XSS w nazwach kandydata itp.)."""
    return (
        (text or "")
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _email_row(label: str, value: str) -> str:
    return (
        '<tr>'
        '<td style="padding:8px 0;width:160px;color:#888;font-size:0.85rem;font-weight:500;vertical-align:top;">'
        f'{_escape(label)}'
        '</td>'
        f'<td style="padding:8px 0;color:#1A1A1A;font-size:0.95rem;vertical-align:top;">{value}</td>'
        '</tr>'
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
        f"Zmiana statusu aplikacji: {job_title} - Praca w Szwajcarii",
        html,
    )
