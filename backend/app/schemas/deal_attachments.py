from datetime import datetime

from pydantic import BaseModel

from app.schemas.files import StoredFileResponse


class DealAttachmentResponse(BaseModel):
    id: str
    deal_id: str
    file: StoredFileResponse
    created_at: datetime
    updated_at: datetime


class DealAttachmentListResponse(BaseModel):
    attachments: list[DealAttachmentResponse]
