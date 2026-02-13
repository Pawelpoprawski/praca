from datetime import date, datetime
from pydantic import BaseModel, Field


class EmployerProfileUpdate(BaseModel):
    company_name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = Field(None, max_length=5000)
    website: str | None = Field(None, max_length=500)
    industry: str | None = Field(None, max_length=100)
    canton: str | None = Field(None, max_length=50)
    city: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=255)
    uid_number: str | None = Field(None, max_length=20)
    company_size: str | None = Field(
        None, pattern="^(1-10|11-50|51-200|201-500|500\\+)$"
    )


class EmployerProfileResponse(BaseModel):
    id: str
    user_id: str
    company_name: str
    company_slug: str
    description: str | None
    logo_url: str | None
    website: str | None
    industry: str | None
    canton: str | None
    city: str | None
    address: str | None
    uid_number: str | None
    company_size: str | None
    is_verified: bool
    created_at: datetime
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None

    model_config = {"from_attributes": True}


class EmployerDashboard(BaseModel):
    active_jobs: int
    total_applications: int
    new_applications: int
    quota_used: int
    quota_limit: int
    quota_reset_date: date | None


class QuotaResponse(BaseModel):
    plan_type: str
    monthly_limit: int
    used_count: int
    remaining: int
    period_start: date
    period_end: date
    days_until_reset: int
    has_custom_limit: bool
