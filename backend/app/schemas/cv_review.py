from datetime import date, datetime
from pydantic import BaseModel, EmailStr


class CVAnalysisResult(BaseModel):
    overall_score: int
    summary: str
    strengths: list[str]
    improvements: list[str]
    missing: list[str]
    tips: list[str]


class CVReviewResponse(BaseModel):
    id: str
    email: str | None = None
    cv_filename: str
    cv_original_filename: str
    overall_score: int | None = None
    analysis: CVAnalysisResult | None = None
    status: str
    previous_score: int | None = None
    created_at: datetime | None = None


class CVReviewEmailRequest(BaseModel):
    email: EmailStr


class CVDatabaseSubmitRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str | None = None
    job_preferences: str
    available_from: date | None = None
    preferred_cantons: list[str] = []
    expected_salary_min: int | None = None
    expected_salary_max: int | None = None
    work_mode: str | None = None  # onsite, remote, hybrid
    languages: list[dict] = []  # [{language, level}]
    driving_license: list[str] | None = None
    has_car: bool = False
    additional_notes: str | None = None
    consent_given: bool = False


class CVDatabaseListItem(BaseModel):
    id: str
    full_name: str | None = None
    email: str | None = None
    phone: str | None = None
    job_preferences: str | None = None
    available_from: date | None = None
    preferred_cantons: list[str] | None = None
    expected_salary_min: int | None = None
    expected_salary_max: int | None = None
    work_mode: str | None = None
    languages: list[dict] | None = None
    driving_license: list[str] | None = None
    has_car: bool = False
    overall_score: int | None = None
    is_active: bool = True
    extraction_status: str = "pending"
    match_ready: bool = False
    created_at: datetime | None = None


class CVDatabaseDetail(CVDatabaseListItem):
    cv_text: str | None = None
    cv_file_path: str | None = None
    extracted_data: dict | None = None
    additional_notes: str | None = None
    consent_given: bool = False
    cv_review_id: str | None = None
    cv_file_id: str | None = None
    user_id: str | None = None
    experience_years: int | None = None
    experience_entries: list[dict] | None = None
    category_slugs: list[str] | None = None
    skills: list[str] | None = None
    ai_keywords: str | None = None
    education: list[dict] | None = None
    location: str | None = None
    extraction_version: int = 0
    updated_at: datetime | None = None
