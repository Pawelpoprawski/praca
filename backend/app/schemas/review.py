from datetime import datetime
from pydantic import BaseModel, Field


class ReviewCreate(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(..., min_length=10, max_length=2000)


class ReviewResponse(BaseModel):
    id: str
    employer_id: str
    rating: int
    comment: str
    status: str
    worker_name: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReviewAdminResponse(BaseModel):
    id: str
    employer_id: str
    worker_user_id: str
    rating: int
    comment: str
    status: str
    worker_name: str
    company_name: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ReviewStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(approved|rejected)$")


class ReviewListResponse(BaseModel):
    data: list[ReviewResponse]
    total: int
    page: int
    per_page: int
    pages: int
    avg_rating: float | None
    total_reviews: int
