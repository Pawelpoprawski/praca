from datetime import datetime
from pydantic import BaseModel, Field, model_validator


class LanguageRequirement(BaseModel):
    lang: str = Field(max_length=5)
    level: str = Field(max_length=5)


class JobCreateRequest(BaseModel):
    title: str = Field(min_length=3, max_length=255)
    description: str = Field(min_length=20)
    canton: str = Field(min_length=2, max_length=50)
    city: str | None = Field(None, max_length=100)
    category_id: str | None = None
    contract_type: str = Field(pattern="^(full_time|part_time|temporary|contract|internship|freelance)$")
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    salary_type: str = Field(default="monthly", pattern="^(monthly|yearly|hourly|negotiable)$")
    experience_min: int = Field(default=0, ge=0, le=50)
    is_remote: str = Field(default="no", pattern="^(no|yes|hybrid)$")
    car_required: bool = False
    driving_license_required: bool = False
    languages_required: list[LanguageRequirement] = Field(default_factory=list)
    contact_email: str | None = Field(None, max_length=255)
    apply_via: str = Field(default="portal", pattern="^(portal|email|external_url)$")
    external_url: str | None = Field(None, max_length=500)

    @model_validator(mode="after")
    def check_salary_range(self) -> "JobCreateRequest":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min nie może być większe niż salary_max")
        return self


class JobUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = Field(None, min_length=20)
    canton: str | None = Field(None, min_length=2, max_length=50)
    city: str | None = None
    category_id: str | None = None
    contract_type: str | None = Field(None, pattern="^(full_time|part_time|temporary|contract|internship|freelance)$")
    salary_min: float | None = Field(None, ge=0)
    salary_max: float | None = Field(None, ge=0)
    salary_type: str | None = Field(None, pattern="^(monthly|yearly|hourly|negotiable)$")
    experience_min: int | None = Field(None, ge=0, le=50)
    is_remote: str | None = Field(None, pattern="^(no|yes|hybrid)$")
    car_required: bool | None = None
    driving_license_required: bool | None = None
    languages_required: list[LanguageRequirement] | None = None
    contact_email: str | None = None
    apply_via: str | None = Field(None, pattern="^(portal|email|external_url)$")
    external_url: str | None = None

    @model_validator(mode="after")
    def check_salary_range(self) -> "JobUpdateRequest":
        if (
            self.salary_min is not None
            and self.salary_max is not None
            and self.salary_min > self.salary_max
        ):
            raise ValueError("salary_min nie może być większe niż salary_max")
        return self


class CompanyBrief(BaseModel):
    id: str
    company_name: str
    company_slug: str
    logo_url: str | None
    is_verified: bool

    model_config = {"from_attributes": True}


class CategoryBrief(BaseModel):
    id: str
    name: str
    slug: str
    icon: str | None

    model_config = {"from_attributes": True}


class JobResponse(BaseModel):
    id: str
    title: str
    description: str
    canton: str
    city: str | None
    contract_type: str
    salary_min: float | None
    salary_max: float | None
    salary_type: str
    salary_currency: str
    experience_min: int
    is_remote: str
    car_required: bool
    driving_license_required: bool
    languages_required: list[LanguageRequirement]
    apply_via: str
    external_url: str | None
    status: str
    views_count: int
    is_featured: bool
    published_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    ai_keywords: str | None = None
    recruiter_type: str | None = None
    skills: list | None = None
    seniority_level: str | None = None
    work_permit_required: str | None = None
    accommodation_provided: bool = False
    shift_work: bool = False
    extraction_status: str = "pending"
    match_ready: bool = False
    employer: CompanyBrief | None = None
    category: CategoryBrief | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    id: str
    title: str
    canton: str
    city: str | None
    contract_type: str
    salary_min: float | None
    salary_max: float | None
    salary_type: str
    salary_currency: str
    is_remote: str
    is_featured: bool
    published_at: datetime | None
    recruiter_type: str | None = None
    seniority_level: str | None = None
    employer: CompanyBrief | None = None
    category: CategoryBrief | None = None

    model_config = {"from_attributes": True}
