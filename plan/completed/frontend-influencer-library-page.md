# Frontend Influencer Library Page Plan

## Status

- Implemented and verified.
- Influencer Library is now a table-first Ant Design Vue page.
- Manual influencer creation is no longer constantly visible; it opens from the page-level `New influencer` modal.
- The list API now returns lightweight multi-platform summaries so the table can show multi-platform creators without frontend N+1 detail requests.

## Sources

- Notion-derived project rules in `AGENTS.md`.
- Frontend implementation rules in `frontend/AGENTS.md`.
- Penpot overview design for the Influencer Library page.
- Existing backend influencer CRUD and ingestion APIs.

## Goal

Make the Influencer Library page usable as the global creator asset library while preserving the product boundary:

- Influencer is global reusable data.
- Import remains an Influencer sub-flow.
- Campaign-specific status, compensation, labels, and notes stay on Deal.

## Backend Changes

Extend `GET /api/v1/influencers` response with `platforms`:

- `id`
- `platform`
- `username`
- `profile_url`
- `follower_count`
- `engagement_rate`
- `is_primary`

Keep existing compact list fields:

- `primary_platform`
- `follower_count`
- `primary_contact`
- `recent_deal_count`

Do not add a new list endpoint. Do not make the frontend fetch each influencer detail row just to display platforms.

## Frontend Changes

Implement the Influencer Library screen with Ant Design Vue primitives:

- `a-table` for the library list.
- `rowSelection` for multi-select archive.
- rightmost actions column for single-row archive.
- search, platform, country, city, and include-archived controls in the table toolbar.
- page-level `Import CSV` action that routes to `/influencers/import`.
- page-level `New influencer` action that opens a modal.

Manual create modal:

- display name.
- full name.
- platform, username, profile URL, follower count.
- email.
- country and city.
- optional campaign target.
- notes.

After successful create:

- refresh the table.
- close and reset the modal.
- preserve the campaign context when a campaign target is selected.

## Boundaries

- Do not show a persistent manual add panel.
- Do not add a right-side profile preview on the library page.
- Clicking influencer name navigates to the shared Influencer Detail route.
- Keep delete semantics as archive.
- Keep Import under Influencers, not as top-level navigation.

## Tests

Backend:

- `uv run pytest tests/test_influencers.py`
- `uv run pytest`
- `uv run ruff check .`

Frontend:

- `bun run typecheck`
- `bun run build`

Manual checks:

- `/influencers` loads a table from real backend data.
- Multi-platform creators show multiple platform tags.
- `New influencer` opens the modal and the form is not constantly displayed.
- Single-row delete and multi-select delete archive records after confirmation.
- `Import CSV` links to the Influencer Import Wizard.

## Done Criteria

- Influencer Library matches the Penpot table-first direction.
- Manual add is modal-only.
- Multi-platform display works from the list response.
- Frontend uses Ant Design Vue instead of custom table/form controls.
- All verification commands pass.
