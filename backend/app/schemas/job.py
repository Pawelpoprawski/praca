from datetime import datetime
from pydantic import BaseModel, Field


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
    salary_min: int | None = Field(None, ge=0)
    salary_max: int | None = Field(None, ge=0)
    salary_type: str = Field(default="monthly", pattern="^(monthly|yearly|hourly|negotiable)$")
    experience_min: int = Field(default=0, ge=0, le=50)
    work_permit_required: str | None = None
    work_permit_sponsored: bool = False
    is_remote: str = Field(default="no", pattern="^(no|yes|hybrid)$")
    languages_required: list[LanguageRequirement] = Field(default_factory=list)
    contact_email: str | None = Field(None, max_length=255)
    apply_via: str = Field(default="portal", pattern="^(portal|email|external_url)$")
    external_url: str | None = Field(None, max_length=500)


class JobUpdateRequest(BaseModel):
    title: str | None = Field(None, min_length=3, max_length=255)
    description: str | None = Field(None, min_length=20)
    canton: str | None = Field(None, min_length=2, max_length=50)
    city: str | None = None
    category_id: str | None = None
    contract_type: str | None = Field(None, pattern="^(full_time|part_time|temporary|contract|internship|freelance)$")
    salary_min: int | None = Field(None, ge=0)
    salary_max: int | None = Field(None, ge=0)
    salary_type: str | None = Field(None, pattern="^(monthly|yearly|hourly|negotiable)$")
    experience_min: int | None = Field(None, ge=0, le=50)
    work_permit_required: str | None = None
    work_permit_sponsored: bool | None = None
    is_remote: str | None = Field(None, pattern="^(no|yes|hybrid)$")
    languages_required: list[LanguageRequirement] | None = None
    contact_email: str | None = None
    apply_via: str | None = Field(None, pattern="^(portal|email|external_url)$")
    external_url: str | None = None


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
    salary_min: int | None
    salary_max: int | None
    salary_type: str
    salary_currency: str
    experience_min: int
    work_permit_required: str | None
    work_permit_sponsored: bool
    is_remote: str
    languages_required: list[LanguageRequirement]
    apply_via: str
    external_url: str | None
    status: str
    views_count: int
    is_featured: bool
    published_at: datetime | None
    expires_at: datetime | None
    created_at: datetime
    employer: CompanyBrief | None = None
    category: CategoryBrief | None = None

    model_config = {"from_attributes": True}


class JobListResponse(BaseModel):
    id: str
    title: str
    canton: str
    city: str | None
    contract_type: str
    salary_min: int | None
    salary_max: int | None
    salary_type: str
    salary_currency: str
    is_remote: str
    is_featured: bool
    published_at: datetime | None
    employer: CompanyBrief | None = None
    category: CategoryBrief | None = None

    model_config = {"from_attributes": True}
