# Outreach & Template Drafting Plan

## Status

- Not implemented.
- No template model, service, API, or frontend flow exists.
- Email Context is also not implemented, so sending and thread linking should remain loosely coupled.

When this module is implemented and verified, move this file to `plan/completed/outreach-template-drafting.md`.

## Notion Sources

- Product doc: MVP can support basic outreach templates and draft generation.
- Campaign & Deal doc: bulk generate outreach draft is a Campaign Workspace operation.
- Backend Architecture doc: template rendering orchestration belongs in service layer once template features enter scope.

## Goal

Reduce repeated copy/paste by generating outreach drafts from Campaign, Deal, Influencer, Contact, Deliverable, and Compensation data.

## Scope

In scope:

- Manage basic outreach templates.
- Render a template for one or more deals.
- Produce draft payloads for frontend copy/send workflows.
- Mark deal as `OUTREACHED` only after user confirms send or records sent status.

Out of scope:

- Automatic follow-up sequence.
- Sending email directly through Gmail.
- AI negotiation.
- Contract generation.

## Data Model

Add `OutreachTemplate`:

- id.
- name.
- subject_template.
- body_template.
- description.
- is_archived.
- created_at.
- updated_at.

Do not add follow-up sequence tables in MVP.

## Backend API

Templates:

- `GET /api/v1/outreach/templates`
- `POST /api/v1/outreach/templates`
- `GET /api/v1/outreach/templates/{template_id}`
- `PATCH /api/v1/outreach/templates/{template_id}`
- `DELETE /api/v1/outreach/templates/{template_id}`

Drafting:

- `POST /api/v1/deals/{deal_id}/outreach-drafts`
- `POST /api/v1/campaigns/{campaign_id}/outreach-drafts/bulk`
- `POST /api/v1/deals/{deal_id}/outreach-sent`

## Backend Design

Add:

- `backend/app/outreach/schemas.py`
- `backend/app/services/outreach.py`
- `backend/app/api/routes/outreach.py`
- migration for `outreach_templates`
- tests in `backend/tests/test_outreach.py`

Rendering:

- Use a small deterministic template renderer. Avoid arbitrary Python execution.
- Variables use dotted names like `influencer.display_name`, `campaign.name`, `contact.email`.
- Unknown variables return validation errors at preview/render time.

Render context should include:

- campaign name, dates, brand names.
- influencer display name.
- primary platform URL.
- primary contact email/name.
- compensation summary.
- deliverable summary.

Service rules:

- Draft generation does not mutate Deal status.
- `outreach-sent` endpoint records user-confirmed send and updates Deal status to `OUTREACHED` if appropriate.
- Do not downgrade status if deal is already `RESPONDED`, `NEGOTIATING`, `ACTIVE`, `COMPLETED`, or `LOST`.
- Missing optional fields should produce warnings, not necessarily block render.

## Frontend Work

Add:

- Template list/editor.
- Deal draft preview.
- Bulk draft preview for selected campaign rows.
- User-confirmed sent action.

## Tests

Backend:

- CRUD template.
- Render single deal draft.
- Bulk render returns row-level warnings.
- Unknown variable validation.
- Missing contact warning.
- Confirm sent updates `OUTREACHED` from `APPROVED` or `DRAFT`.
- Confirm sent does not overwrite later statuses.

## Done Criteria

- Users can create templates and generate drafts for deals.
- Rendering is deterministic and backend-owned.
- Deal status changes only after explicit send confirmation.
- `uv run pytest` and `uv run ruff check .` pass.
