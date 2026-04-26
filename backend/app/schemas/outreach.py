from pydantic import BaseModel, Field


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
