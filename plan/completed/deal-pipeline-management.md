# Deal Pipeline Management Plan

## Status

- Campaign CRUD is implemented.
- `Deal` model and `DealService.create_if_missing` exist.
- Missing standalone Deal APIs, campaign pipeline query, status updates, bulk operations, and deal detail aggregation.

When this module is implemented and verified, move this file to `plan/completed/deal-pipeline-management.md`.

## Notion Sources

- Product doc: Deal is the campaign-specific work unit and each Campaign Workspace row.
- Campaign & Deal doc: Campaign Service owns pipeline query; Deal Service owns state, lost reason, labels, notes, and related objects.
- Data model doc: `Deal` is unique by `campaign_id + influencer_id`.

## Goal

Implement Deal as the central campaign pipeline row.

The user should be able to add influencers to a campaign, update deal state, inspect deal detail, and query the campaign pipeline.

## Scope

In scope:

- Create a deal from an existing influencer and campaign.
- List campaign pipeline rows.
- Read/update/archive a deal.
- Bulk update selected deals.
- Support status, lost reason, labels, internal notes.
- Provide compact summaries from deliverables, compensation, contacts, and email links when available.

Out of scope:

- Deliverable CRUD implementation details. That is a separate plan.
- Compensation CRUD implementation details. That is a separate plan.
- Email sync/linking implementation details. That is a separate plan.
- Kanban view and custom status builder.

## Backend API

Campaign-scoped:

- `GET /api/v1/campaigns/{campaign_id}/deals`
- `POST /api/v1/campaigns/{campaign_id}/deals`
- `POST /api/v1/campaigns/{campaign_id}/deals/bulk`
- `PATCH /api/v1/campaigns/{campaign_id}/deals/bulk`

Deal-scoped:

- `GET /api/v1/deals/{deal_id}`
- `PATCH /api/v1/deals/{deal_id}`
- `DELETE /api/v1/deals/{deal_id}`

Use `/api/v1` prefix through app router inclusion.

## Backend Design

Add:

- `backend/app/deals/schemas.py`
- Expand `backend/app/services/deals.py`
- `backend/app/api/routes/deals.py`
- Tests in `backend/tests/test_deals.py`

Repository additions:

- `DealRepository.list_for_campaign(filters, sort, pagination)`
- `DealRepository.get_detail(deal_id)`
- `DealRepository.list_by_ids(ids)`

Service rules:

- Same campaign and influencer defaults to one deal.
- Creating an existing campaign/influencer deal returns conflict or existing-deal metadata. Do not silently create duplicates.
- Allow manual status correction. Do not enforce a strict linear state machine in MVP.
- Setting status to `LOST` should allow `lost_reason`; it can warn when missing but should not block in MVP.
- Archiving a deal keeps related deliverables, compensation, and email links for history.

## Pipeline Query Fields

Each row should include:

- deal id/status/lost reason/labels/internal notes.
- influencer id/display name/country/city.
- primary platform and follower count.
- primary contact email.
- deliverable summary.
- compensation summary.
- email thread count and last activity when available.
- updated_at.

Filters:

- status.
- platform.
- lost reason.
- has email thread.
- archived.

Sort:

- updated_at.
- follower_count.
- status.
- due_date once deliverables exist.

## Bulk Operations

MVP bulk update:

- status.
- labels add/remove/replace.
- internal notes append or replace.

Bulk create:

- create deals from influencer ids.
- skip or conflict on existing deals.
- return row-level results.

Bulk operations must return counts and row-level failures.

## Frontend Work

Add Campaign Workspace pipeline table:

- load campaign deals.
- status filter.
- row selection.
- bulk status update.
- open deal detail drawer.
- add influencers to campaign from library.

## Tests

Backend:

- Create deal.
- Duplicate campaign/influencer is rejected or returned as conflict.
- List campaign pipeline.
- Update status and lost reason.
- Archive deal.
- Bulk create row-level skip/conflict.
- Bulk update selected deals.
- Campaign not found, influencer not found, deal not found errors.

## Done Criteria

- Campaign Workspace can be powered by backend pipeline API.
- Deal status and notes are campaign-specific only.
- Ingestion confirm with target campaign continues to create deals through DealService.
- `uv run pytest` and `uv run ruff check .` pass.
