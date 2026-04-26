from datetime import date, datetime

from pydantic import BaseModel, Field

from app.enums import DeliverableStatus


class DeliverableCreateRequest(BaseModel):
    type: str = Field(min_length=1, max_length=128)
    quantity: int = Field(default=1, gt=0)
    due_date: date | None = None
    status: DeliverableStatus = DeliverableStatus.TODO
    published_url: str | None = Field(default=None, max_length=1024)
    notes: str | None = None


class DeliverableUpdateRequest(BaseModel):
    type: str | None = Field(default=None, min_length=1, max_length=128)
    quantity: int | None = Field(default=None, gt=0)
    due_date: date | None = None
    status: DeliverableStatus | None = None
    published_url: str | None = Field(default=None, max_length=1024)
    notes: str | None = None


class DeliverableResponse(BaseModel):
    id: str
    deal_id: str
    type: str
    quantity: int
    due_date: date | None = None
    status: DeliverableStatus
    published_url: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class DeliverableListResponse(BaseModel):
    deliverables: list[DeliverableResponse]
