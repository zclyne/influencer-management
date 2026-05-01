# Influencer Notes And Tags

## Goal

Make Influencer notes and tags first-class global profile data without mixing them into campaign-specific Deal labels.

## Backend Scope

- Add `tags_json` to the `influencers` table.
- Expose `tags` on influencer create, update, list, detail, and manual create API contracts.
- Normalize tags in `InfluencerService`:
  - trim outer whitespace.
  - collapse internal whitespace.
  - deduplicate case-insensitively while preserving first display casing.
  - allow Unicode letters/numbers, spaces, `-`, `_`, `/`, `.`, and `&`.
  - reject blank tags, more than 20 tags, and tags longer than 32 characters.
- Support exact case-insensitive list filtering with `GET /api/v1/influencers?tag=...`.

## Frontend Scope

- Rename visible `Global notes` language to `Notes`.
- Remove notes from the main profile edit modal.
- Add a standalone `Notes` card on Influencer Detail with its own edit modal.
- Add a standalone `Tags` card on Influencer Detail with its own edit modal.
- Show tags in Influencer Library rows.
- Add a tag filter to Influencer Library using available loaded tags.
- Allow manual influencer creation with multiple tags.

## Done Criteria

- Backend tests cover tag create, update, list/detail response, list filter, manual create, and validation failures.
- Frontend typecheck and build pass.
- This plan is moved to `plan/completed/` after implementation and verification.
