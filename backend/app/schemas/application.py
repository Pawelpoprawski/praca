from datetime import datetime
from pydantic import BaseModel, Field


class ApplyRequest(BaseModel):
    cover_letter: str | None = Field(None, max_length=5000)


class ApplicationStatusUpdate(BaseModel):
    status: str = Field(pattern="^(viewed|shortlisted|rejected|accepted)$")
    employer_notes: str | None = None


class ApplicationResponse(BaseModel):
    id: str
    job_offer_id: str
    status: str
    cover_letter: str | None
    created_at: datetime
    updated_at: datetime
    job_title: str | None = None
    company_name: str | None = None

    model_config = {"from_attributes": True}


class CandidateResponse(BaseModel):
    id: str
    worker_id: str
    status: str
    cover_letter: str | None
    created_at: datetime
    worker_name: str | None = None
    worker_email: str | None = None
    has_cv: bool = False
    employer_notes: str | None = None

    model_config = {"from_attributes": True}
