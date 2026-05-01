# Influencer Detail Page

## Summary

Implement the real frontend page for `/influencers/:influencerId`, replacing the current placeholder with a Penpot-aligned, API-backed global influencer profile page.

## Scope

- Render global influencer profile data from `GET /api/v1/influencers/{id}`.
- Support editing global profile fields through `PATCH /api/v1/influencers/{id}`.
- Support influencer archive through `DELETE /api/v1/influencers/{id}`.
- Support platform add/edit/delete through existing influencer platform APIs.
- Support contact add/edit/delete through existing influencer contact APIs.
- Show campaign deal summaries from the influencer response and link to deal detail pages.

## Out Of Scope

- Audience snapshots, because they are not exposed in the current frontend API contract.
- Bulk platform/contact delete, because backend only has single-item delete endpoints.
- Deal cost or platform usage in the influencer deal table, because `InfluencerDealSummary` does not expose those fields.

## Done Criteria

- `/influencers/:influencerId` routes to a real page.
- Influencer Library and campaign/deal profile links open the shared detail page.
- Platform tags reuse the shared platform color rule.
- The page passes frontend typecheck and production build.
- This plan is moved to `plan/completed/` after implementation and verification.
