# Export & Reporting Plan

## Status

- Not implemented.
- `StoredFile` model exists, but no export service, job, route, or frontend action exists.

When this module is implemented and verified, move this file to `plan/completed/export-reporting.md`.

## Notion Sources

- Product doc: MVP must export campaign pipeline as CSV or Google Sheets compatible format.
- Backend Architecture doc: export generation can become a background job.
- Campaign & Deal doc: Campaign Service supports export data source.

## Goal

Allow users to export campaign pipeline data for customers, internal team members, finance, or external workflows.

## Scope

In scope:

- Export a campaign pipeline to CSV.
- Export current filtered view.
- Include influencer, platform, deal, deliverable, compensation, and notes fields.
- Support synchronous export for small MVP data sets, with a clear path to async jobs.

Out of scope:

- Client portal.
- Complex dashboard.
- ROI/performance analytics.
- Google Sheets API push. Generate compatible CSV first.

## Backend API

MVP:

- `GET /api/v1/campaigns/{campaign_id}/export.csv`

Query params should mirror pipeline filters where practical:

- `status`
- `platform`
- `lost_reason`
- `include_archived`

Future async:

- `POST /api/v1/campaigns/{campaign_id}/exports`
- `GET /api/v1/jobs/{job_id}`
- `GET /api/v1/exports/{export_id}/download`

## Backend Design

Add:

- `backend/app/exports/schemas.py`
- `backend/app/services/exports.py`
- route can live in campaigns route or `exports.py`; endpoint path remains campaign-scoped.
- tests in `backend/tests/test_exports.py`

Service rules:

- Reuse Campaign pipeline query composition to avoid export/filter drift.
- Stable column order.
- CSV must be UTF-8.
- Empty child collections produce empty strings, not JSON dumps in user-facing CSV unless a field explicitly needs JSON.
- Summary columns should be human-readable.

## Initial Columns

Recommended MVP columns:

- campaign_name.
- brand_names.
- deal_status.
- lost_reason.
- influencer_display_name.
- influencer_country.
- influencer_city.
- primary_platform.
- primary_profile_url.
- follower_count.
- primary_contact_email.
- deliverables_summary.
- compensation_summary.
- cash_total.
- reimbursement_total.
- email_thread_count.
- internal_notes.
- updated_at.

Do not export raw import metadata by default.

## Local File Handling

Synchronous endpoint can stream CSV directly.

If async export is implemented:

- write generated file under app data export directory.
- create `StoredFile` with kind `campaign_export`.
- return file id and download endpoint.

## Frontend Work

Campaign Workspace:

- Export current view.
- Show selected filters in export confirmation.
- Download/save flow through Electron.

## Tests

Backend:

- Export campaign with no deals.
- Export campaign with deals.
- Export includes deliverable and compensation summaries once those modules exist.
- Filters match pipeline query.
- CSV header stable.
- Non-ASCII names are preserved.
- Unknown campaign returns 404.

## Done Criteria

- Campaign pipeline can be exported from `/api/v1`.
- Exported CSV matches current filtered pipeline semantics.
- No duplicate export-specific business query logic diverges from Campaign/Deal service.
- `uv run pytest` and `uv run ruff check .` pass.
