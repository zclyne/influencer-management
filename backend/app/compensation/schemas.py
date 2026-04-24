from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, model_validator

from app.domain.enums import CompensationItemStatus, CompensationItemType


class CompensationItemCreateRequest(BaseModel):
    type: CompensationItemType = CompensationItemType.OTHER
    description: str | None = None
    amount: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    recipient_name: str | None = Field(default=None, max_length=255)
    status: CompensationItemStatus = CompensationItemStatus.PLANNED
    due_date: date | None = None
    completed_at: datetime | None = None
    receipt_file_id: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def normalize_currency(self) -> "CompensationItemCreateRequest":
        if self.currency is not None:
            self.currency = self.currency.upper()
        return self


class CompensationItemUpdateRequest(BaseModel):
    type: CompensationItemType | None = None
    description: str | None = None
    amount: Decimal | None = Field(default=None, ge=0)
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    recipient_name: str | None = Field(default=None, max_length=255)
    status: CompensationItemStatus | None = None
    due_date: date | None = None
    completed_at: datetime | None = None
    receipt_file_id: str | None = None
    notes: str | None = None

    @model_validator(mode="after")
    def normalize_currency(self) -> "CompensationItemUpdateRequest":
        if self.currency is not None:
            self.currency = self.currency.upper()
        return self


class CompensationItemResponse(BaseModel):
    id: str
    deal_id: str
    type: CompensationItemType
    description: str | None = None
    amount: Decimal | None = None
    currency: str | None = None
    recipient_name: str | None = None
    status: CompensationItemStatus
    due_date: date | None = None
    completed_at: datetime | None = None
    receipt_file_id: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CompensationItemListResponse(BaseModel):
    compensation_items: list[CompensationItemResponse]
