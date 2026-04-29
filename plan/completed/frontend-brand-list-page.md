# Frontend Brand List Page Plan

## Status

- Implemented and verified.
- `/brands` renders the Brand List page.
- Backend Brand CRUD exists under `/api/v1/brands`.

## Sources

- Root `AGENTS.md`: Brand is a core MVP entity and CampaignBrand owns campaign association.
- `frontend/AGENTS.md`: use Ant Design Vue primitives and keep page-specific actions out of the top bar.
- Backend Brand API and tests.
- Existing Campaign and Influencer list page patterns.

## Goal

Implement a real Brand List page that lets users browse, create, edit, and archive standalone brand records.

## Scope

In scope:

- `/brands` route renders a Brand List page.
- Brand API client and TypeScript types.
- Brand feature composable for loading, filtering, create, update, archive, and bulk archive.
- Ant Design Vue table, modal forms, popconfirm, and notifications.

Out of scope:

- Brand detail page.
- Campaign-brand association management from the Brand page.
- Hard delete.

## UX

Page:

- Title: `Brands`.
- Description: standalone brand records used across campaigns.
- Summary cards: active brands, linked campaigns, archived brands when archived are included.
- Table toolbar: search, include archived, `Delete selected`, `New brand`.

Table columns:

- Brand.
- Website.
- Campaigns.
- Updated.
- Actions.

Actions:

- `New brand` opens a modal.
- `Edit` opens the same modal populated with the selected brand.
- `Delete` archives a row after confirmation.
- `Delete selected` archives selected active rows after confirmation.

## API

Add frontend API wrappers:

- `GET /api/v1/brands`
- `POST /api/v1/brands`
- `PATCH /api/v1/brands/{brand_id}`
- `DELETE /api/v1/brands/{brand_id}`

Use existing backend response fields:

- id.
- name.
- website.
- notes.
- campaign_count.
- archived_at.
- created_at.
- updated_at.

## Tests

Frontend:

- `bun run typecheck` passed.
- `bun run build` passed.

Backend:

- `uv run pytest tests/test_brands.py` passed.
- `uv run ruff check .` passed.

Manual:

- `/brands` loads real Brand API data.
- search filters through API query param.
- include archived toggles archived rows.
- create, edit, single archive, and bulk archive refresh the list.

## Done Criteria

- `/brands` no longer uses `PlaceholderPage`.
- All page controls use Ant Design Vue primitives.
- Delete semantics remain archive.
- Pagination spacing matches the other list pages.
- Plan file is moved from `plan/todo` to `plan/completed`.
