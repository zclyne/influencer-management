from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from app.domain.enums import EmailLinkType


class EmailParticipant(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    name: str | None = None


class EmailThreadMetadataResponse(BaseModel):
    id: str
    provider: str
    external_thread_id: str
    account_id: str | None = None
    subject: str | None = None
    participants: list[EmailParticipant] = Field(default_factory=list)
    last_message_at: datetime | None = None
    snippet: str | None = None
    message_count: int
    created_at: datetime
    updated_at: datetime


class EmailThreadListResponse(BaseModel):
    threads: list[EmailThreadMetadataResponse]


class EmailThreadMatchRequest(BaseModel):
    provider: str
    external_thread_id: str
    participants: list[EmailParticipant] = Field(default_factory=list)
    message_count: int | None = None


class EmailThreadCandidate(BaseModel):
    type: str
    confidence: Decimal | None = None
    influencer_id: str | None = None
    campaign_id: str | None = None
    deal_id: str | None = None
    contact_id: str | None = None
    link_id: str | None = None
    reason: str
    suggested_status: str | None = None


class EmailThreadMatchResponse(BaseModel):
    provider: str
    external_thread_id: str
    candidates: list[EmailThreadCandidate]


class EmailThreadLinkCreateRequest(BaseModel):
    provider: str
    external_thread_id: str
    external_message_id: str | None = None
    influencer_id: str | None = None
    campaign_id: str | None = None
    deal_id: str | None = None
    contact_id: str | None = None
    linked_by: str | None = None


class EmailThreadLinkUpdateRequest(BaseModel):
    influencer_id: str | None = None
    campaign_id: str | None = None
    deal_id: str | None = None
    contact_id: str | None = None
    linked_by: str | None = None


class EmailThreadLinkResponse(BaseModel):
    id: str
    provider: str
    external_thread_id: str
    external_message_id: str | None = None
    influencer_id: str | None = None
    campaign_id: str | None = None
    deal_id: str | None = None
    contact_id: str | None = None
    link_type: EmailLinkType
    confidence: Decimal | None = None
    linked_by: str | None = None
    created_at: datetime
    updated_at: datetime


class EmailThreadLinkListResponse(BaseModel):
    links: list[EmailThreadLinkResponse]


class ScopedEmailThreadResponse(BaseModel):
    link: EmailThreadLinkResponse
    thread: EmailThreadMetadataResponse | None = None


class ScopedEmailThreadListResponse(BaseModel):
    threads: list[ScopedEmailThreadResponse]
