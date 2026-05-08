from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.enums import CampaignStatus


class CampaignCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    brief: str | None = None
    budget: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: CampaignStatus = CampaignStatus.PLANNING
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Campaign name cannot be blank.")
        return stripped


class CampaignUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    brief: str | None = None
    budget: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: CampaignStatus | None = None
    notes: str | None = None
    tags: list[str] | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("Campaign name cannot be blank.")
        return stripped


class CampaignBrandLinkRequest(BaseModel):
    brand_id: str
    role: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class CampaignBrandUpdateRequest(BaseModel):
    role: str | None = Field(default=None, max_length=64)
    notes: str | None = None


class BrandSummary(BaseModel):
    id: str
    name: str
    website: str | None = None
    notes: str | None = None


class CampaignBrandResponse(BaseModel):
    id: str
    brand: BrandSummary
    role: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class CampaignResponse(BaseModel):
    id: str
    name: str
    brief: str | None = None
    budget: Decimal | None = None
    start_date: date | None = None
    end_date: date | None = None
    status: CampaignStatus
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
    archived_at: datetime | None = None
    brands: list[CampaignBrandResponse] = Field(default_factory=list)


class CampaignListResponse(BaseModel):
    campaigns: list[CampaignResponse]
