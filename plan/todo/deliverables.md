# Deliverables Plan

## Status

- `Deliverable` model and repository exist.
- No service, API routes, frontend UI, or business tests exist.

When this module is implemented and verified, move this file to `plan/completed/deliverables.md`.

## Notion Sources

- Product doc: Deliverable is a lightweight object under Deal.
- Data model doc: Deliverable fields include type, quantity, due date, status, published URL, notes.
- Campaign & Deal doc: Deal detail aggregates deliverables and Deal completion can be suggested based on deliverable state.

## Goal

Allow users to track content or event commitments for a Deal without building a full content review workflow.

## Scope

In scope:

- Add, list, update, delete deliverables under a Deal.
- Track type, quantity, due date, status, published URL, notes.
- Provide summaries for Deal detail and Campaign pipeline.

Out of scope:

- Brand approval workflow.
- Draft review and revision flow.
- Automatic platform performance sync.
- Asset upload.

## Backend API

Deal-scoped endpoints:

- `GET /api/v1/deals/{deal_id}/deliverables`
- `POST /api/v1/deals/{deal_id}/deliverables`
- `PATCH /api/v1/deals/{deal_id}/deliverables/{deliverable_id}`
- `DELETE /api/v1/deals/{deal_id}/deliverables/{deliverable_id}`

Optional summary endpoint can be deferred because Deal detail and pipeline rows should embed summary data.

## Backend Design

Add:

- `backend/app/deliverables/schemas.py`
- `backend/app/services/deliverables.py`
- routes can live in `backend/app/api/routes/deals.py` or `deliverables.py`; prefer `deals.py` while the API is deal-scoped.
- Tests in `backend/tests/test_deliverables.py`

Repository additions:

- `DeliverableRepository.list_for_deal(deal_id)`
- `DeliverableRepository.get_for_deal(deal_id, deliverable_id)`

Service rules:

- Deal must exist and not be archived for create/update/delete.
- Quantity must be positive.
- `published_url` is optional except when status is `POSTED` or `COMPLETED`; MVP can warn but not block if needed.
- Delete can be hard delete because Deliverable is a child detail, but consider archive if audit becomes important. MVP can delete.
- Do not automatically mark Deal complete. Return a suggestion flag when all deliverables and compensation items are complete.

## Status Values

Use existing enum:

- `TODO`
- `IN_PROGRESS`
- `SUBMITTED`
- `POSTED`
- `COMPLETED`
- `CANCELLED`

MVP UI can emphasize `TODO`, `POSTED`, and `COMPLETED`, while backend accepts full enum.

## Summary Logic

Add a utility in service layer or Deal query composition:

- total deliverables.
- completed count.
- next due date.
- published URL count.
- compact label such as `2 videos, 1 posted`.

Avoid storing summary fields in the DB unless performance demands it.

## Frontend Work

Deal detail drawer:

- deliverable list.
- add/edit rows.
- quick status update.
- published URL field.

Campaign pipeline:

- compact deliverable summary column.
- optional due date sort once available.

## Tests

Backend:

- Create deliverable.
- List by deal.
- Update status and published URL.
- Delete deliverable.
- Reject missing deal.
- Reject deliverable from wrong deal.
- Quantity validation.
- Summary output on deal detail or pipeline once wired.

## Done Criteria

- Deliverables are manageable from Deal API.
- Deal and Campaign pipeline can display deliverable summaries.
- No content approval workflow is introduced.
- `uv run pytest` and `uv run ruff check .` pass.
