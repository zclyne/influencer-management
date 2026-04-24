# API Contract & Error Model Plan

## Status

- Routes are mounted with `/api/v1`.
- Campaign routes have a local error response shape.
- Other routes still return ad hoc dicts or raise default errors.
- No OpenAPI export workflow or frontend client generation is in place.

When this module is implemented and verified, move this file to `plan/completed/api-contract-and-errors.md`.

## Notion Sources

- Backend Architecture doc: API paths should use `/api/v1`, Pydantic response schemas, and unified errors.
- Technical overview: OpenAPI schema is the frontend/backend contract.
- Frontend doc: frontend should use OpenAPI-generated or schema-constrained API client types.

## Goal

Make backend HTTP behavior consistent enough for frontend development and module integration.

## Scope

In scope:

- Unified API error schema.
- Service error base class or shared error mapping helper.
- Response models for existing routes.
- OpenAPI export command.
- Frontend API client generation plan or script.

Out of scope:

- Full auth.
- Request tracing across processes.
- Public API documentation site.

## Backend Design

Add:

- `backend/app/api/errors.py`
- `backend/app/api/schemas.py` or shared `ApiErrorResponse`
- optional `backend/scripts/export_openapi.py`
- tests in `backend/tests/test_api_contract.py`

Error shape:

```json
{
  "code": "not_found",
  "message": "Human readable message",
  "details": {},
  "request_id": null
}
```

Service errors:

- Have `code`, `message`, `status_code`, `details`.
- API handlers use one helper to map errors.

Route cleanup:

- Influencer manual route should return a Pydantic response model.
- Ingestion routes should use the same error response model.
- Campaign local error helper should be replaced by shared helper.

## OpenAPI Export

Add a backend command:

- `uv run python -m app.api.openapi_export`

Output:

- `frontend/src/api/openapi.json` or `frontend/openapi.json`

Do not hand-edit generated schema.

## Frontend Client

Pick one approach when frontend work starts:

- Generate TypeScript client from OpenAPI.
- Or generate types and keep a small hand-written fetch wrapper.

The plan should prefer minimal complexity until API stabilizes.

## Tests

Backend:

- Existing endpoint errors follow shared shape.
- Not found returns code and details.
- Validation errors are mapped or documented.
- OpenAPI contains mounted `/api/v1` paths.
- Manual influencer endpoint has response model.

Frontend later:

- API client compiles from generated schema.

## Done Criteria

- All backend routes return consistent errors.
- OpenAPI export is repeatable.
- Frontend has a stable source of API types.
- `uv run pytest` and `uv run ruff check .` pass.
