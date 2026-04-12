from datetime import datetime
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    user_id: str
    type: str
    title: str
    message: str
    is_read: bool
    related_entity_type: str | None
    related_entity_id: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class NotificationList(BaseModel):
    data: list[NotificationResponse]
    total: int
    page: int
    per_page: int
    pages: int


class NotificationMarkRead(BaseModel):
    is_read: bool = True
