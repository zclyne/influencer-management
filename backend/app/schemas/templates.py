from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.enums import TemplateType


class TemplateCreateRequest(BaseModel):
    type: TemplateType = TemplateType.OUTREACH_EMAIL
    name: str = Field(min_length=1, max_length=255)
    subject_template: str = Field(min_length=1, max_length=1024)
    body_template: str = Field(min_length=1)
    description: str | None = None

    @field_validator("name", "subject_template", "body_template")
    @classmethod
    def strip_required(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value cannot be blank.")
        return stripped


class TemplateUpdateRequest(BaseModel):
    type: TemplateType | None = None
    name: str | None = Field(default=None, min_length=1, max_length=255)
    subject_template: str | None = Field(default=None, min_length=1, max_length=1024)
    body_template: str | None = Field(default=None, min_length=1)
    description: str | None = None
    is_archived: bool | None = None

    @field_validator("name", "subject_template", "body_template")
    @classmethod
    def strip_optional(cls, value: str | None) -> str | None:
        if value is None:
            return value
        stripped = value.strip()
        if not stripped:
            raise ValueError("Value cannot be blank.")
        return stripped


class TemplateResponse(BaseModel):
    id: str
    type: TemplateType
    name: str
    subject_template: str
    body_template: str
    description: str | None = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class TemplateListResponse(BaseModel):
    templates: list[TemplateResponse]
