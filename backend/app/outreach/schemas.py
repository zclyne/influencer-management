from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class OutreachTemplateCreateRequest(BaseModel):
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


class OutreachTemplateUpdateRequest(BaseModel):
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


class OutreachTemplateResponse(BaseModel):
    id: str
    name: str
    subject_template: str
    body_template: str
    description: str | None = None
    is_archived: bool
    created_at: datetime
    updated_at: datetime


class OutreachTemplateListResponse(BaseModel):
    templates: list[OutreachTemplateResponse]


class OutreachDraftRequest(BaseModel):
    template_id: str


class BulkOutreachDraftRequest(BaseModel):
    template_id: str
    deal_ids: list[str] = Field(default_factory=list)


class OutreachDraftResponse(BaseModel):
    deal_id: str
    template_id: str
    subject: str
    body: str
    to_email: str | None = None
    warnings: list[str] = Field(default_factory=list)


class BulkOutreachDraftResponse(BaseModel):
    drafts: list[OutreachDraftResponse]
