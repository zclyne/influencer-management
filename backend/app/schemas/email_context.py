from datetime import datetime

from pydantic import BaseModel, Field


class GmailAuthStatusResponse(BaseModel):
    connected: bool
    email: str | None = None
    google_subject: str | None = None
    scopes: list[str] = Field(default_factory=list)
    expires_at: datetime | None = None
    reconnect_required: bool = False


class GmailAuthStartResponse(BaseModel):
    authorization_url: str


class GmailLabelResponse(BaseModel):
    id: str
    name: str
    type: str | None = None


class GmailLabelListResponse(BaseModel):
    labels: list[GmailLabelResponse]


class EmailParticipant(BaseModel):
    email: str | None = None
    name: str | None = None


class EmailCrmLink(BaseModel):
    type: str
    label_id: str
    label_name: str
    campaign_id: str | None = None
    deal_id: str | None = None


class GmailThreadSummary(BaseModel):
    id: str
    subject: str | None = None
    snippet: str | None = None
    participants: list[EmailParticipant] = Field(default_factory=list)
    last_message_at: datetime | None = None
    message_count: int = 0
    labels: list[GmailLabelResponse] = Field(default_factory=list)
    crm_links: list[EmailCrmLink] = Field(default_factory=list)


class GmailThreadListResponse(BaseModel):
    threads: list[GmailThreadSummary]
    next_page_token: str | None = None


class GmailMessageResponse(BaseModel):
    id: str
    sender: EmailParticipant | None = None
    to: list[EmailParticipant] = Field(default_factory=list)
    cc: list[EmailParticipant] = Field(default_factory=list)
    sent_at: datetime | None = None
    snippet: str | None = None
    body_text: str | None = None
    body_html: str | None = None


class GmailThreadDetailResponse(GmailThreadSummary):
    messages: list[GmailMessageResponse] = Field(default_factory=list)


class EmailThreadLinkRequest(BaseModel):
    campaign_id: str | None = None
    deal_id: str | None = None


class EmailThreadLinkResponse(BaseModel):
    thread_id: str
    links: list[EmailCrmLink]
