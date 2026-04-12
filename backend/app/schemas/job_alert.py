from datetime import datetime
from pydantic import BaseModel, Field


class JobAlertFilters(BaseModel):
    category_id: str | None = None
    canton: str | None = None
    min_salary: int | None = Field(None, ge=0)
    max_salary: int | None = Field(None, ge=0)
    keywords: str | None = Field(None, max_length=500)
    work_mode: str | None = Field(
        None, pattern="^(no|yes|hybrid)$"
    )  # maps to is_remote
    permit_sponsorship: bool | None = None


class JobAlertCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    filters: JobAlertFilters = Field(default_factory=JobAlertFilters)
    frequency: str = Field(
        default="daily", pattern="^(instant|daily|weekly)$"
    )


class JobAlertUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)
    filters: JobAlertFilters | None = None
    frequency: str | None = Field(
        None, pattern="^(instant|daily|weekly)$"
    )


class JobAlertResponse(BaseModel):
    id: str
    name: str
    filters: JobAlertFilters
    is_active: bool
    frequency: str
    last_sent_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class JobAlertList(BaseModel):
    alerts: list[JobAlertResponse]
    count: int
    max_alerts: int = 5
