# Background Jobs & Observability Plan

## Status

- Docker Compose includes Redis/worker direction, and `backend/app/tasks` has a sample.
- No job table, job API, job status service, structured job logging, or production-ready queue integration exists.

When this module is implemented and verified, move this file to `plan/completed/background-jobs-observability.md`.

## Notion Sources

- Backend Architecture doc: long tasks must be async, RQ + Redis is recommended.
- Backend doc: ingestion, email sync, export, and future contract generation should not block UI.
- Technical overview: frontend starts jobs and polls job status.

## Goal

Provide a minimal reliable background job foundation for imports, exports, email sync, and future document generation.

## Scope

In scope:

- Job creation abstraction.
- Job status API.
- RQ worker integration.
- Structured logging with job id.
- Persisted job result/error metadata.

Out of scope:

- Distributed scheduling.
- Complex retries UI.
- Multi-user job ownership.
- Cloud queue.

## Data Model

Add `JobRecord`:

- id.
- type.
- status.
- progress_current.
- progress_total.
- result_json.
- error_code.
- error_message.
- created_at.
- started_at.
- finished_at.

Status values:

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`

## Backend API

- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/jobs?status=&type=`
- Future: `POST /api/v1/jobs/{job_id}/cancel`

Module-specific start endpoints can return job ids later:

- imports.
- exports.
- email sync.

## Backend Design

Add:

- `backend/app/jobs/schemas.py`
- `backend/app/services/jobs.py`
- `backend/app/api/routes/jobs.py`
- migration for `job_records`
- worker helpers under `backend/app/tasks`
- tests in `backend/tests/test_jobs.py`

Service rules:

- API creates JobRecord before enqueue.
- Worker sets `running`, then `succeeded` or `failed`.
- Store sanitized error message in DB.
- Log stack trace with job id.
- API response must not expose raw stack trace.

## RQ Integration

Use existing Redis settings.

Define:

- queue factory.
- task registry.
- worker entrypoint.
- test fake job runner for service tests.

Avoid making core service logic depend directly on RQ primitives. Service should be callable synchronously in tests.

## Observability

Logging:

- include request id when available.
- include job id for worker tasks.
- include module context, such as `influencer_ingestion`, `export`, `email_context`.

Local logs:

- stdout for Docker.
- optional app data log file later.

## Migration Path

Do not force current ingestion confirm to async immediately.

Recommended sequence:

1. Implement generic job API and worker plumbing.
2. Convert export generation if needed.
3. Convert large ingestion later after current synchronous behavior is stable.
4. Convert email sync when connector exists.

## Tests

Backend:

- Create JobRecord.
- Get status.
- Worker success updates result.
- Worker failure stores sanitized error.
- Unknown job returns 404.
- API errors follow unified error shape once available.

## Done Criteria

- Long-running modules have a common job foundation.
- Worker logs and API status are diagnosable.
- Core service code remains testable without Redis.
- `uv run pytest` and `uv run ruff check .` pass.
