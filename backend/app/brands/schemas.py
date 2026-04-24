from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class BrandCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=512)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Brand name cannot be blank.")
        return stripped


class BrandUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    website: str | None = Field(default=None, max_length=512)
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        stripped = value.strip()
        if not stripped:
            raise ValueError("Brand name cannot be blank.")
        return stripped


class BrandResponse(BaseModel):
    id: str
    name: str
    website: str | None = None
    notes: str | None = None
    archived_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    campaign_count: int | None = None


class BrandListResponse(BaseModel):
    brands: list[BrandResponse]
