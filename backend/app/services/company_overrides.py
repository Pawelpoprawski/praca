"""Company-level overrides for the apply flow.

When a job is sourced from one of these companies (matched by employer.company_name,
case-insensitive, with surrounding whitespace stripped), we force the apply path to go
through our internal email form instead of an external URL. This way the candidate sends
the application through us, and we forward / track the email to the agreed inbox.

To add a new mapping, just put a new line in COMPANY_APPLY_OVERRIDES.
"""
from __future__ import annotations


# normalized lowercase company name -> recipient email
COMPANY_APPLY_OVERRIDES: dict[str, str] = {
    "njujob": "praca@njujob.pl",
}


def _normalize(name: str | None) -> str:
    return (name or "").strip().lower()


def get_override_email(company_name: str | None) -> str | None:
    """Return the override email for a company name, or None if no override is configured."""
    if not company_name:
        return None
    return COMPANY_APPLY_OVERRIDES.get(_normalize(company_name))


def apply_company_override(job) -> None:
    """Mutate a JobOffer-like object in place so apply_via -> 'email' for overridden companies.

    Expects `job.employer.company_name`, `job.apply_via`, `job.contact_email`, `job.external_url`.
    Safe to call on jobs without employer (no-op).
    """
    employer = getattr(job, "employer", None)
    company_name = getattr(employer, "company_name", None) if employer else None
    override_email = get_override_email(company_name)
    if not override_email:
        return
    job.apply_via = "email"
    job.contact_email = override_email
    job.external_url = None
