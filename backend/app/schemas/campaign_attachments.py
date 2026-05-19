from datetime import datetime

from pydantic import BaseModel

from app.schemas.files import StoredFileResponse


class CampaignAttachmentResponse(BaseModel):
    id: str
    campaign_id: str
    file: StoredFileResponse
    created_at: datetime
    updated_at: datetime


class CampaignAttachmentListResponse(BaseModel):
    attachments: list[CampaignAttachmentResponse]
