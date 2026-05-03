from datetime import date, datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.enums import DealStatus


class ApiErrorResponse(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None
    request_id: str | None = None


class DealCreateRequest(BaseModel):
    influencer_id: str
    status: DealStatus = DealStatus.DRAFT
    lost_reason: str | None = Field(default=None, max_length=255)
    labels: list[str] = Field(default_factory=list)
    internal_notes: str | None = None


class DealUpdateRequest(BaseModel):
    status: DealStatus | None = None
    lost_reason: str | None = Field(default=None, max_length=255)
    labels: list[str] | None = None
    internal_notes: str | None = None


class DealBulkCreateRequest(BaseModel):
    influencer_ids: list[str] = Field(min_length=1)
    skip_existing: bool = True


class DealBulkUpdateRequest(BaseModel):
    deal_ids: list[str] = Field(min_length=1)
    status: DealStatus | None = None
    lost_reason: str | None = Field(default=None, max_length=255)
    labels: list[str] | None = None
    label_mode: Literal["replace", "add", "remove"] = "replace"
    internal_notes: str | None = None
    notes_mode: Literal["replace", "append"] = "replace"


class InfluencerSummary(BaseModel):
    id: str
    display_name: str
    country: str | None = None
    city: str | None = None


class PrimaryPlatformSummary(BaseModel):
    platform: str
    username: str | None = None
    profile_url: str | None = None
    follower_count: int | None = None


class PrimaryContactSummary(BaseModel):
    id: str
    name: str | None = None
    email: str
    role: str
    is_primary: bool


class DeliverableSummary(BaseModel):
    total_count: int = 0
    completed_count: int = 0
    next_due_date: date | None = None
    published_url_count: int = 0
    label: str | None = None


class CompensationSummary(BaseModel):
    active_item_count: int = 0
    completed_item_count: int = 0
    cash_totals: dict[str, Decimal] = Field(default_factory=dict)
    reimbursement_totals: dict[str, Decimal] = Field(default_factory=dict)
    non_cash_descriptions: list[str] = Field(default_factory=list)
    label: str | None = None


class DealResponse(BaseModel):
    id: str
    campaign_id: str
    influencer_id: str
    status: DealStatus
    lost_reason: str | None = None
    labels: list[str] = Field(default_factory=list)
    internal_notes: str | None = None
    source_list_status: str | None = None
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None


class DealPipelineRow(BaseModel):
    id: str
    campaign_id: str
    status: DealStatus
    lost_reason: str | None = None
    labels: list[str] = Field(default_factory=list)
    internal_notes: str | None = None
    influencer: InfluencerSummary
    primary_platform: PrimaryPlatformSummary | None = None
    platforms: list[PrimaryPlatformSummary] = Field(default_factory=list)
    primary_contact: PrimaryContactSummary | None = None
    deliverables: DeliverableSummary
    compensation: CompensationSummary
    completion_suggested: bool = False
    updated_at: datetime
    archived_at: datetime | None = None


class DealDetailResponse(DealPipelineRow):
    created_at: datetime
    source_list_status: str | None = None


class DealListResponse(BaseModel):
    deals: list[DealPipelineRow]


class DealBulkCreateRowResult(BaseModel):
    influencer_id: str
    deal_id: str | None = None
    status: Literal["created", "skipped", "conflict", "error"]
    errors: list[str] = Field(default_factory=list)


class DealBulkCreateResponse(BaseModel):
    created_count: int
    skipped_count: int
    conflict_count: int
    error_count: int
    rows: list[DealBulkCreateRowResult]


class DealBulkUpdateRowResult(BaseModel):
    deal_id: str
    status: Literal["updated", "error"]
    errors: list[str] = Field(default_factory=list)


class DealBulkUpdateResponse(BaseModel):
    updated_count: int
    error_count: int
    rows: list[DealBulkUpdateRowResult]
