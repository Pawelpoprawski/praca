from datetime import datetime
from pydantic import BaseModel
from app.schemas.job import JobListResponse


class SavedJobResponse(BaseModel):
    id: str
    job_offer_id: str
    created_at: datetime
    job: JobListResponse | None = None

    model_config = {"from_attributes": True}


class SavedJobCheckResponse(BaseModel):
    is_saved: bool


class QuickApplyRequest(BaseModel):
    cover_letter: str | None = None
