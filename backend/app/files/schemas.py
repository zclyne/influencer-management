from datetime import datetime

from pydantic import BaseModel

from app.domain.enums import StoredFileKind


class StoredFileResponse(BaseModel):
    id: str
    kind: StoredFileKind
    original_name: str
    mime_type: str | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    exists: bool
    created_at: datetime
    updated_at: datetime
