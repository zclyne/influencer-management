# Email Context & Linking Plan

## Status

- `EmailThreadLink` model and repository exist.
- No `EmailAccount`, `EmailThreadMetadata`, connector, service, API, or frontend panel exists.

When this module is implemented and verified, move this file to `plan/completed/email-context-linking.md`.

## Notion Sources

- Product doc: Email Context & Linking is an MVP module.
- Email Context doc: MVP focuses on reliable recognition, hints, manual confirmation, and aggregation.
- Data model doc: EmailThreadLink can point to influencer, campaign, deal, and contact.

## Goal

Connect email threads to the right Influencer, Campaign, or Deal without assuming one email equals one creator or one deal.

## Scope

In scope:

- Manual link/unlink thread to influencer, campaign, or deal.
- Match known participant emails to InfluencerContact.
- Return candidate links for a thread.
- Show linked thread metadata on Deal and Influencer detail.
- Support thread inheritance for already linked external thread ids.

Out of scope:

- Full Gmail sync UI.
- Full email body storage/search.
- AI email summarization.
- Automatic semantic extraction of prices/deliverables.
- Follow-up automation.

## Data Model Additions

Current `EmailThreadLink` is enough for link records.

Add migration later for:

- `EmailAccount`
- `EmailThreadMetadata`

`EmailAccount` fields:

- id.
- provider.
- email.
- display_name.
- sync_status.
- last_synced_at.

`EmailThreadMetadata` fields:

- id.
- provider.
- external_thread_id.
- account_id.
- subject.
- participants_json.
- last_message_at.
- snippet.
- message_count.
- created_at.
- updated_at.

Do not store full email body in MVP unless a separate privacy decision is made.

## Backend API

Thread metadata:

- `GET /api/v1/email/threads`
- `GET /api/v1/email/threads/{provider}/{external_thread_id}`

Candidate matching:

- `POST /api/v1/email/threads/match`

Links:

- `GET /api/v1/email/thread-links`
- `POST /api/v1/email/thread-links`
- `PATCH /api/v1/email/thread-links/{link_id}`
- `DELETE /api/v1/email/thread-links/{link_id}`

Deal-scoped:

- `GET /api/v1/deals/{deal_id}/email-threads`

Influencer-scoped:

- `GET /api/v1/influencers/{influencer_id}/email-threads`

## Backend Design

Add:

- `backend/app/email_context/schemas.py`
- `backend/app/services/email_context.py`
- `backend/app/api/routes/email_context.py`
- tests in `backend/tests/test_email_context.py`

Connector boundary:

- `GmailConnector` or fake connector returns account/thread/message metadata.
- Connector does not decide ownership.
- `EmailContextService` performs matching and link decisions.

Service rules:

- Manual link has highest priority.
- If `provider + external_thread_id` already has a manual link, return it as inherited candidate.
- If participant email matches exactly one `InfluencerContact`, return influencer candidate.
- If that influencer has active or recent deals, return deal candidates.
- If participant email matches multiple influencers, return conflict candidates and do not auto-link.
- Unlink should remove or archive the link. If archive is not modeled, hard delete is acceptable for MVP with tests.
- New contact creation from thread participants should call Influencer contact service once it exists.

## Status Hint Rules

Do not silently update Deal status in MVP.

Return hints:

- If deal is `OUTREACHED` and matched thread has reply activity, suggest `RESPONDED`.
- If deal is already `NEGOTIATING` or later, do not suggest downgrade.

## Privacy Rules

- Store metadata and links only.
- Avoid storing message body in MVP.
- API errors should not expose email contents.
- Add future option to clear local email cache.

## Frontend Work

Add Email Context Panel:

- list candidate threads.
- show participant emails, subject, snippet, last activity.
- link/unlink controls.
- add participant email as contact.

Deal detail:

- linked threads list.
- recent thread count and last activity.

## Tests

Backend:

- Match unique known contact.
- Match email shared by multiple contacts returns conflict.
- Manual link and unlink.
- Thread inheritance from existing link.
- Link to deal validates campaign/influencer consistency when deal id is present.
- Deal email thread list.
- Status hint for `OUTREACHED` deal.

## Done Criteria

- User can manually link and unlink email threads.
- Known contacts produce safe candidates, not silent ownership.
- Deal detail can show linked email context.
- `uv run pytest` and `uv run ruff check .` pass.
