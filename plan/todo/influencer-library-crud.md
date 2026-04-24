# Influencer Library CRUD Plan

## Status

- Partially implemented through ingestion and manual create.
- Current code has `InfluencerService.manual_create`, `bulk_create_or_update`, `InfluencerBulkWriter`, and ingestion tests.
- Missing full library CRUD, search/filter, profile detail, platform/contact subresource APIs, and frontend library UI.

When this module is implemented and verified, move this file to `plan/completed/influencer-library-crud.md`.

## Notion Sources

- Product doc: Influencer Library is the global creator asset library.
- Data model doc: Influencer, InfluencerPlatform, InfluencerAudienceSnapshot, InfluencerContact are global assets.
- Import/Ingestion doc: InfluencerService owns canonical influencer operations; ingestion calls into it.

## Goal

Make Influencer Library a first-class module that supports browsing, editing, reusing, and deduplicating creators across campaigns.

## Boundaries

Influencer stores global reusable data:

- name, full name, location, bio, global notes.
- platform accounts and metrics.
- contacts.
- historical deals through relationships.

Influencer must not store:

- campaign-specific status.
- campaign-specific compensation.
- campaign-specific labels or notes.
- campaign-specific qualification.

## Backend API

Add or complete:

- `GET /api/v1/influencers`
- `POST /api/v1/influencers`
- `GET /api/v1/influencers/{influencer_id}`
- `PATCH /api/v1/influencers/{influencer_id}`
- `DELETE /api/v1/influencers/{influencer_id}`
- `GET /api/v1/influencers/{influencer_id}/platforms`
- `POST /api/v1/influencers/{influencer_id}/platforms`
- `PATCH /api/v1/influencers/{influencer_id}/platforms/{platform_id}`
- `DELETE /api/v1/influencers/{influencer_id}/platforms/{platform_id}`
- `GET /api/v1/influencers/{influencer_id}/contacts`
- `POST /api/v1/influencers/{influencer_id}/contacts`
- `PATCH /api/v1/influencers/{influencer_id}/contacts/{contact_id}`
- `DELETE /api/v1/influencers/{influencer_id}/contacts/{contact_id}`
- `GET /api/v1/influencers/{influencer_id}/deals`

Keep ingestion APIs under:

- `POST /api/v1/influencers/imports/modash/preview`
- `POST /api/v1/influencers/imports/confirm`

## Backend Design

Files:

- Extend `backend/app/influencers/schemas.py`
- Extend `backend/app/services/influencers.py`
- Extend `backend/app/api/routes/influencers.py`
- Add tests in `backend/tests/test_influencers.py`

Repository additions:

- list with search, platform, country, city, archived filters.
- eager-load profile detail with platforms, contacts, recent deals.
- contact lookup by email is already present.
- platform lookup by normalized URL and platform username is already present.

Service rules:

- Archive influencer instead of hard delete.
- Deleting a platform/contact should not delete the influencer.
- Do not delete an influencer with historical deals by default; archive it.
- Normalize email/profile URL/username with existing ingestion normalization helpers.
- Platform uniqueness conflicts return structured errors.
- Contact email can appear on multiple influencers, but service should warn or expose conflict metadata rather than silently assume uniqueness.

## Response Shape

List response should be compact:

- influencer id/name/location.
- primary platform.
- follower count.
- primary contact.
- recent deal count.

Detail response can include:

- full influencer profile.
- platforms with latest metrics.
- contacts.
- historical deals grouped by campaign.
- audience snapshots only when requested or in a dedicated endpoint, to keep detail payload reasonable.

## Frontend Work

Add:

- Influencer Library route.
- Search/filter table.
- Influencer profile page or drawer.
- Platform/contact editors.
- Add-to-campaign action that calls Deal creation later.

## Tests

Backend:

- Create standalone influencer.
- List/search/filter.
- Read detail with platforms and contacts.
- Patch profile fields.
- Archive and exclude archived by default.
- Add/update/delete platform with normalization.
- Add/update/delete contact with email normalization.
- Duplicate platform URL/handle conflicts.
- Historical deals appear in profile.

## Done Criteria

- Full Influencer CRUD exists under `/api/v1/influencers`.
- Import confirm still reuses `InfluencerService` and `InfluencerBulkWriter`.
- Global influencer data stays cleanly separated from Deal data.
- `uv run pytest` and `uv run ruff check .` pass.
