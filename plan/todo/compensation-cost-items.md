# Compensation & Cost Items Plan

## Status

- `CompensationItem` model and repository exist.
- No service, API routes, summary aggregation, frontend UI, or business tests exist.

When this module is implemented and verified, move this file to `plan/completed/compensation-cost-items.md`.

## Notion Sources

- Product doc: Compensation Item is an MVP object under Deal.
- Compensation & Cost Items doc: use one broad model for cash, gifts, samples, reimbursements, and subsidies.
- Data model doc: Deal must not store compensation amount or gift fields directly.

## Goal

Implement CompensationItem as the single source of truth for all Deal cost and compensation commitments.

## Scope

In scope:

- CRUD compensation items under a Deal.
- Track type, description, amount, currency, recipient, status, due date, completed date, receipt file id, notes.
- Provide Deal and Campaign summary aggregates.

Out of scope:

- Real payment execution.
- Invoice, W-9, reimbursement approval workflow.
- Receipt upload. The file reference is planned, actual file handling belongs to Local File Management.
- Full finance dashboard.

## Backend API

Deal-scoped:

- `GET /api/v1/deals/{deal_id}/compensation-items`
- `POST /api/v1/deals/{deal_id}/compensation-items`
- `PATCH /api/v1/deals/{deal_id}/compensation-items/{item_id}`
- `DELETE /api/v1/deals/{deal_id}/compensation-items/{item_id}`

Bulk add can be implemented with Deal bulk operations later:

- `POST /api/v1/deals/{deal_id}/compensation-items/bulk`

## Backend Design

Add:

- `backend/app/compensation/schemas.py`
- `backend/app/services/compensation.py`
- routes can be mounted from `deals.py` or `compensation.py`; endpoint path stays deal-scoped.
- Tests in `backend/tests/test_compensation_items.py`

Repository additions:

- `CompensationItemRepository.list_for_deal(deal_id)`
- `CompensationItemRepository.get_for_deal(deal_id, item_id)`

Service rules:

- Deal must exist and not be archived for create/update/delete.
- `amount` is optional because non-cash items may only have description.
- `currency` defaults to `USD` when amount is present and currency is omitted.
- Cancelled items do not count toward active cost totals.
- Amount cannot be negative.
- `completed_at` can be set when status becomes `COMPLETED`; do not force if user sets status manually, but support auto-fill when omitted.
- Do not update Deal status automatically.

## Types

Use existing enum:

- `CASH_STIPEND`
- `PRODUCT_GIFT`
- `SAMPLE_PRODUCT`
- `FLIGHT_REIMBURSEMENT`
- `HOTEL_REIMBURSEMENT`
- `LOCAL_TRANSPORT_REIMBURSEMENT`
- `MEAL_OR_PER_DIEM`
- `OTHER`

## Status Values

Use existing enum:

- `PLANNED`
- `PROMISED`
- `IN_PROGRESS`
- `COMPLETED`
- `CANCELLED`

## Summary Logic

Deal summary should include:

- cash total by currency.
- reimbursement total by currency.
- active item count.
- completed item count.
- non-cash descriptions.
- compact label such as `$1,000 cash + product gift`.

Campaign summary can be added after Deal pipeline:

- total active cost by currency.
- pending reimbursement total.
- count by item type.

Do not store summary columns yet. Compute from child rows.

## Frontend Work

Deal detail drawer:

- compensation item table.
- quick type/status update.
- amount/currency fields.
- completed date.
- notes.

Campaign pipeline:

- compact compensation summary column.
- filter by item status later.

## Tests

Backend:

- Create item with amount.
- Create non-cash item without amount.
- Default currency with amount.
- Reject negative amount.
- Update status to completed.
- Cancelled items excluded from summary.
- Delete item.
- Reject wrong deal/item combination.
- Deal summary includes item aggregation.

## Done Criteria

- CompensationItem is the only place where compensation/cost is represented.
- Deal has no direct compensation amount or gift shortcut fields.
- Deal and Campaign pipeline can display cost summaries.
- `uv run pytest` and `uv run ruff check .` pass.
