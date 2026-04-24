# AGENTS.md

## Project Overview

Desktop IRM is a local-first desktop influencer relationship manager for small agency teams running influencer marketing campaigns. The core workflow is:

1. Import influencers from external lists, especially Modash CSV exports.
2. Normalize, preview, deduplicate, and confirm influencer writes.
3. Reuse influencers from a global Influencer Library.
4. Add influencers to Campaigns as campaign-specific Deals.
5. Track Deal status, deliverables, compensation/cost items, email context, and exportable campaign progress.

The product is campaign-first. Influencer data is a global reusable asset, but day-to-day work happens through Campaign Workspace and Deal rows.

## Source Of Truth

Use the Notion product and technical docs as the product/architecture source of truth. The current implementation and `plan/` files reflect the latest execution state.

Important Notion concepts already reflected in this repo:

- Import/Ingestion belongs under the Influencer module, not a top-level Import domain.
- Import preview is source-specific. Current MVP source is Modash CSV.
- Import confirm is source-agnostic and writes canonical influencer rows through InfluencerService and InfluencerBulkWriter.
- Influencer, InfluencerPlatform, InfluencerAudienceSnapshot, and InfluencerContact are global assets.
- Deal is campaign-specific and is the Campaign Workspace row.
- Deal owns status, lost reason, labels, internal notes, deliverables, compensation items, and email links.
- CompensationItem is the only source of compensation/cost data. Do not add compensation amount or gift shortcuts to Deal.
- Campaign and Brand are many-to-many through CampaignBrand.
- Contract Draft Generator is deferred and must not enter MVP data model or Deal status.

## Plan Workflow

Plans live under `plan/` and follow the existing structure:

```text
plan/
  todo/
  completed/
```

Rules:

- New implementation plans go in `plan/todo/`.
- A module plan stays in `plan/todo/` while the module is incomplete.
- After a plan is implemented, verified, and accepted, move that plan file to `plan/completed/`.
- Do not leave completed implementation plans in `plan/todo/`.
- Do not create one-off plan locations outside this structure.
- If a module is already completed, do not write a duplicate todo plan for it.
- Keep plan files focused on module boundaries, API shape, service responsibilities, tests, and done criteria.

Current todo plan files:

- `plan/todo/contract-draft-generator-deferred.md`

Current completed plan files:

- `plan/completed/api-contract-and-errors.md`
- `plan/completed/background-jobs-observability.md`
- `plan/completed/brand-management.md`
- `plan/completed/compensation-cost-items.md`
- `plan/completed/deal-pipeline-management.md`
- `plan/completed/deliverables.md`
- `plan/completed/email-context-linking.md`
- `plan/completed/export-reporting.md`
- `plan/completed/frontend-workbench.md`
- `plan/completed/influencer-library-crud.md`
- `plan/completed/local-file-management.md`
- `plan/completed/outreach-template-drafting.md`

## Current Implementation State

Implemented or mostly implemented:

- Backend FastAPI app with `/api/v1` route prefix.
- SQLAlchemy models and Alembic migrations for core MVP tables, jobs, email metadata, and outreach templates.
- Repository implementations for core models.
- Influencer ingestion/import flow for Modash CSV preview and confirm.
- InfluencerBulkWriter for batch influencer graph writes.
- Manual influencer creation entrypoint.
- Full Influencer Library CRUD and platform/contact subresources.
- Standalone Brand CRUD.
- Campaign CRUD.
- CampaignBrand association APIs.
- Deal pipeline APIs, bulk deal operations, and campaign pipeline query.
- Deliverable APIs.
- CompensationItem APIs and summaries.
- Email Context and Linking service.
- Outreach template drafting.
- Export/reporting.
- Background job API and persisted job records.
- Local file management service.
- Unified API error model and OpenAPI export helper.
- Initial Vue/Electron frontend workbench.
- Backend tests for health, data model, influencer ingestion, campaigns, brands, influencers, deals, deliverables, compensation, jobs/files, exports, email context, and outreach.

Not yet complete:

- Contract Draft Generator. It remains deferred and is not part of MVP.

## Architecture Rules

Backend layering should follow:

```text
API handler -> Service -> Repository -> SQLAlchemy model/database
```

Keep responsibilities strict:

- API handlers validate HTTP request/response, call services, and map service errors to HTTP errors.
- Services contain business rules.
- Repositories hide database query details.
- SQLAlchemy models define persistence shape.
- Connectors wrap external systems or infrastructure and do not make business decisions.

Do not put business rules in FastAPI route handlers.

Do not let frontend code bypass backend services or directly access the database.

## API Rules

- All backend endpoints must be under `/api/v1`.
- Use Pydantic request and response schemas for public API contracts.
- Prefer shared error response shape:

```json
{
  "code": "not_found",
  "message": "Human readable message",
  "details": {},
  "request_id": null
}
```

- Keep import APIs under `/api/v1/influencers/imports/...`.
- Do not add a top-level `/imports` business domain.
- Do not add `/imports/normalized/preview` unless a real generic canonical preview use case is introduced later.

Current ingestion API direction:

- `POST /api/v1/influencers/imports/modash/preview`
- `POST /api/v1/influencers/imports/confirm`

## Domain Boundaries

### Influencer

Influencer is global and reusable across campaigns.

Allowed global data:

- display name.
- full name.
- country/city.
- bio.
- global notes.
- platforms.
- contacts.
- audience snapshots.

Do not store campaign-specific status, compensation, labels, or campaign notes on Influencer.

### Import / Ingestion

Import is an Influencer ingestion use case.

Dependency direction:

```text
InfluencerIngestionService -> InfluencerService -> InfluencerBulkWriter
```

Adapters parse source-specific data into canonical influencer candidates. They do not write to the database and do not own business decisions.

InfluencerIngestionService owns:

- adapter selection.
- canonical normalization.
- dedup preview.
- row decisions.
- confirm validation.
- ImportSession/result reporting.

InfluencerService owns:

- influencer CRUD.
- platform/contact operations.
- canonical influencer bulk create/update.

InfluencerBulkWriter owns:

- writing Influencer.
- writing InfluencerPlatform.
- writing InfluencerAudienceSnapshot.
- writing InfluencerContact.

Deal creation belongs to DealService, even when orchestrated by ingestion confirm.

### Campaign And Deal

Campaign is the project container. Deal is the campaign-specific row.

Deal owns:

- status.
- lost reason.
- labels.
- internal notes.
- deliverables.
- compensation items.
- email thread links.

Default Deal statuses:

- `DRAFT`
- `APPROVED`
- `OUTREACHED`
- `RESPONDED`
- `NEGOTIATING`
- `ACTIVE`
- `COMPLETED`
- `LOST`

MVP should allow manual status correction. Do not enforce an overly strict linear workflow unless the plan explicitly calls for it.

### Compensation

Use CompensationItem for all cash, gifts, samples, reimbursements, travel, meals, and other costs.

Do not add compensation fields directly to Deal.

### Email Context

Email linking must handle multiple contacts, multiple threads, and managers representing multiple influencers.

Manual links have highest priority. Known contact matching should produce candidates unless the match is already unambiguous and confirmed by rules.

Do not silently mutate Deal status from email activity in MVP. Return hints and let the user confirm.

### Contract Drafts

Contract Draft Generator is deferred.

Do not add:

- ContractDraft table.
- contract statuses.
- contract-specific Deal fields.
- contract generation tasks.

Keep Deliverables, CompensationItems, Local File Management, and Outreach clean enough that a future contract renderer can consume them.

## Backend Commands

Run from `backend/` unless otherwise noted:

```bash
uv run pytest
uv run ruff check .
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
uv run alembic upgrade head
uv run python -m app.tasks.worker
```

Docker Compose from repo root:

```bash
docker compose up backend redis worker
```

## Frontend Commands

Run from `frontend/`:

```bash
bun run dev
bun run typecheck
bun run build
bun run electron
```

Frontend communicates with backend through `VITE_API_BASE_URL`, defaulting to `http://localhost:8000`.

## Testing Expectations

For backend changes:

- Add focused tests under `backend/tests/`.
- Cover service behavior and API behavior when adding endpoints.
- Include row-level result tests for bulk/import operations.
- Run `uv run pytest`.
- Run `uv run ruff check .`.

For frontend changes:

- Run `bun run typecheck`.
- Run `bun run build`.
- Add UI tests when the frontend test framework is introduced.

For docs-only changes:

- No test run is required unless the docs generation process or repo tooling changes.

## Coding Conventions

- Python target is 3.12.
- Backend formatting/linting follows Ruff with line length 100.
- Prefer SQLAlchemy 2.x typed ORM style already used in `backend/app/db/models.py`.
- Keep request/response schemas close to their domain package.
- Keep services in `backend/app/services/` unless a module grows enough to justify a local service package.
- Keep API route modules in `backend/app/api/routes/`.
- Use existing normalization helpers before adding new parsing logic.
- Use soft archive for core historical entities such as Brand, Campaign, Influencer, and Deal.
- Avoid compatibility layers while the app is in early development unless explicitly requested.

## File And Data Safety

- Do not hard delete historical business objects unless the relevant plan explicitly calls for it.
- Do not revert unrelated user changes.
- Do not move a todo plan to completed until implementation and verification are done.
- If a plan becomes obsolete, update the plan with the new decision instead of silently deleting it.
