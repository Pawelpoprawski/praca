from datetime import date, datetime
from pydantic import BaseModel, Field


class WorkerLanguage(BaseModel):
    lang: str = Field(max_length=5)
    level: str = Field(max_length=5)


class WorkerProfileUpdate(BaseModel):
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    phone: str | None = Field(None, max_length=20)
    canton: str | None = Field(None, max_length=50)
    work_permit: str | None = Field(
        None,
        pattern="^(permit_b|permit_c|permit_g|permit_l|eu_efta|swiss_citizen|none|other)$",
    )
    experience_years: int | None = Field(None, ge=0, le=50)
    bio: str | None = Field(None, max_length=2000)
    languages: list[WorkerLanguage] | None = None
    skills: list[str] | None = None
    desired_salary_min: int | None = Field(None, ge=0)
    desired_salary_max: int | None = Field(None, ge=0)
    available_from: date | None = None
    industry: str | None = Field(None, max_length=100)


class CVConsentRequest(BaseModel):
    consent: bool
    job_preferences: str | None = Field(None, max_length=2000)


class WorkerProfileResponse(BaseModel):
    id: str
    user_id: str
    canton: str | None
    work_permit: str | None
    experience_years: int
    bio: str | None
    languages: list[WorkerLanguage]
    skills: list[str]
    desired_salary_min: int | None
    desired_salary_max: int | None
    available_from: date | None
    industry: str | None
    has_cv: bool = False
    cv_filename: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    email: str | None = None
    phone: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
