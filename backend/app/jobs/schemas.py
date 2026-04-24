from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.domain.enums import JobStatus


class JobRecordResponse(BaseModel):
    id: str
    type: str
    status: JobStatus
    progress_current: int
    progress_total: int | None = None
    result_json: dict[str, Any] | None = None
    error_code: str | None = None
    error_message: str | None = None
    created_at: datetime
    started_at: datetime | None = None
    finished_at: datetime | None = None


class JobListResponse(BaseModel):
    jobs: list[JobRecordResponse]
