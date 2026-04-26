from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from app.api.schemas import ApiErrorResponse
from app.db.session import get_db
from app.enums import JobStatus
from app.jobs.schemas import JobListResponse, JobRecordResponse
from app.services.jobs import JobService, JobServiceError

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _http_error_response(error: JobServiceError) -> JSONResponse:
    return JSONResponse(
        status_code=error.status_code,
        content=ApiErrorResponse(
            code=error.code,
            message=error.message,
            details=error.details,
            request_id=None,
        ).model_dump(),
    )


ERROR_RESPONSES = {404: {"model": ApiErrorResponse}, 422: {"model": ApiErrorResponse}}


@router.get("", response_model=JobListResponse, responses=ERROR_RESPONSES)
def list_jobs(
    db: Annotated[Session, Depends(get_db)],
    status: JobStatus | None = None,
    type: str | None = None,
) -> JobListResponse | JSONResponse:
    try:
        return JobService(db).list_jobs(status=status, type=type)
    except JobServiceError as exc:
        return _http_error_response(exc)


@router.get("/{job_id}", response_model=JobRecordResponse, responses=ERROR_RESPONSES)
def get_job(
    job_id: str,
    db: Annotated[Session, Depends(get_db)],
) -> JobRecordResponse | JSONResponse:
    try:
        return JobService(db).get_job(job_id)
    except JobServiceError as exc:
        return _http_error_response(exc)
