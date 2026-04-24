# Brand Management Plan

## Status

- Not started as a standalone module.
- Current code has `Brand`, `CampaignBrand`, `BrandRepository`, and campaign brand link APIs.
- Missing standalone Brand CRUD, brand profile, brand contact/guideline fields, and frontend screens.

When this module is implemented and verified, move this file to `plan/completed/brand-management.md`.

## Notion Sources

- Product doc: Brand is an MVP object and Campaign can link to one or more Brands.
- Data model doc: `Brand` has `name`, `website`, `notes`; `CampaignBrand` is many-to-many.
- Campaign & Deal doc: Campaign Service manages Campaign and Brand association.

## Goal

Build Brand as a reusable client/customer object, not just an implementation detail of Campaign.

Brand should support:

- Create, list, read, update, archive.
- Search by name.
- Link and unlink campaigns through existing CampaignBrand behavior.
- Store enough brief/guideline/contact context for campaign setup.

## Scope

In scope:

- `GET /api/v1/brands`
- `POST /api/v1/brands`
- `GET /api/v1/brands/{brand_id}`
- `PATCH /api/v1/brands/{brand_id}`
- `DELETE /api/v1/brands/{brand_id}` as archive.
- Keep campaign brand link APIs under `/api/v1/campaigns/{campaign_id}/brands`.

Out of scope:

- Client portal.
- Approval workflow.
- Multi-user ownership.
- Rich document storage for brand guidelines. Store URLs/notes first.

## Backend Design

Add:

- `backend/app/brands/schemas.py`
- `backend/app/services/brands.py`
- `backend/app/api/routes/brands.py`
- Tests in `backend/tests/test_brands.py`

Extend repository:

- `BrandRepository.list(query, include_archived)`
- `BrandRepository.get_active`
- Optional uniqueness guard on normalized name at service level. Do not add hard DB uniqueness until duplicate behavior is clearer.

Service rules:

- Archive instead of hard delete.
- Archived brands are hidden from default list.
- A brand linked to campaigns can still be archived, but campaign history remains readable.
- Empty name is invalid after trim.

## API Shape

`BrandCreateRequest`:

- `name`
- `website`
- `notes`

`BrandUpdateRequest`:

- all fields optional.

`BrandResponse`:

- `id`
- `name`
- `website`
- `notes`
- `archived_at`
- `created_at`
- `updated_at`
- optional `campaign_count`

## Frontend Work

Add a Brand management surface:

- Brand list with search.
- Create/edit drawer or page.
- Brand detail showing linked campaigns.
- Campaign create/edit should be able to attach existing brands.

## Tests

Backend:

- Create brand.
- List excludes archived by default.
- Search by name.
- Patch fields.
- Archive is soft delete.
- Campaign brand link still works with Brand CRUD.

Frontend later:

- API client type coverage.
- Brand selection in Campaign form.

## Done Criteria

- Brand CRUD endpoints exist under `/api/v1`.
- Campaign brand association continues to pass existing tests.
- No campaign-specific state is stored on Brand.
- `uv run pytest` and `uv run ruff check .` pass.
