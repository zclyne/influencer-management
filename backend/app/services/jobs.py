import logging
from collections.abc import Callable
from typing import Any

from sqlalchemy.orm import Session

from app.db import models
from app.db.models import utc_now
from app.domain.enums import JobStatus
from app.jobs.schemas import JobListResponse, JobRecordResponse
from app.repositories.sqlalchemy import JobRecordRepository

logger = logging.getLogger(__name__)


class JobServiceError(Exception):
    code = "job_error"
    status_code = 422

    def __init__(self, message: str, details: dict[str, object] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details


class JobNotFound(JobServiceError):
    code = "not_found"
    status_code = 404


class JobService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.jobs = JobRecordRepository(db)

    def create_job(self, type: str, *, progress_total: int | None = None) -> JobRecordResponse:
        job = self.jobs.create(
            type=type,
            status=JobStatus.QUEUED.value,
            progress_current=0,
            progress_total=progress_total,
        )
        self.db.commit()
        return self._response(job)

    def get_job(self, job_id: str) -> JobRecordResponse:
        return self._response(self._require_job(job_id))

    def list_jobs(
        self, *, status: JobStatus | None = None, type: str | None = None
    ) -> JobListResponse:
        jobs = self.jobs.list(status=status.value if status else None, type=type)
        return JobListResponse(jobs=[self._response(job) for job in jobs])

    def mark_running(self, job_id: str) -> models.JobRecord:
        job = self._require_job(job_id)
        self.jobs.update(job, status=JobStatus.RUNNING.value, started_at=utc_now())
        self.db.commit()
        logger.info("job started job_id=%s type=%s", job.id, job.type)
        return job

    def mark_progress(
        self, job_id: str, *, current: int, total: int | None = None
    ) -> models.JobRecord:
        job = self._require_job(job_id)
        values: dict[str, object] = {"progress_current": current}
        if total is not None:
            values["progress_total"] = total
        self.jobs.update(job, **values)
        self.db.commit()
        return job

    def mark_succeeded(
        self, job_id: str, *, result_json: dict[str, Any] | None = None
    ) -> models.JobRecord:
        job = self._require_job(job_id)
        self.jobs.update(
            job,
            status=JobStatus.SUCCEEDED.value,
            result_json=result_json,
            error_code=None,
            error_message=None,
            finished_at=utc_now(),
        )
        self.db.commit()
        logger.info("job succeeded job_id=%s type=%s", job.id, job.type)
        return job

    def mark_failed(
        self,
        job_id: str,
        *,
        error_code: str = "job_failed",
        error_message: str = "Job failed.",
    ) -> models.JobRecord:
        job = self._require_job(job_id)
        self.jobs.update(
            job,
            status=JobStatus.FAILED.value,
            error_code=error_code,
            error_message=self._sanitize_error(error_message),
            finished_at=utc_now(),
        )
        self.db.commit()
        logger.info("job failed job_id=%s type=%s error_code=%s", job.id, job.type, error_code)
        return job

    def run_sync(
        self,
        job_id: str,
        handler: Callable[[], dict[str, Any] | None],
    ) -> JobRecordResponse:
        self.mark_running(job_id)
        try:
            result = handler()
        except Exception as exc:
            logger.exception("job handler failed job_id=%s", job_id)
            return self._response(
                self.mark_failed(job_id, error_code="job_failed", error_message=str(exc))
            )
        return self._response(self.mark_succeeded(job_id, result_json=result))

    def _require_job(self, job_id: str) -> models.JobRecord:
        job = self.jobs.get(job_id)
        if not job:
            raise JobNotFound("Job not found.", details={"job_id": job_id})
        return job

    def _sanitize_error(self, message: str) -> str:
        normalized = " ".join(message.split())
        if not normalized:
            return "Job failed."
        return normalized[:500]

    def _response(self, job: models.JobRecord) -> JobRecordResponse:
        return JobRecordResponse(
            id=job.id,
            type=job.type,
            status=JobStatus(job.status),
            progress_current=job.progress_current,
            progress_total=job.progress_total,
            result_json=job.result_json,
            error_code=job.error_code,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            finished_at=job.finished_at,
        )
