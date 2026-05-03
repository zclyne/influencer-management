# Gmail Label Email Module

## Summary

Implemented Email as a Gmail-backed read/link module. Gmail remains the source of truth for
threads, messages, and CRM mapping. Desktop IRM stores only one local Gmail OAuth credential
secret and uses Gmail labels to map threads to Campaigns and Deals.

## Backend

- Added Gmail OAuth status/start/callback/disconnect APIs under `/api/v1/email`.
- Added Gmail thread, label, thread detail, link, and unlink APIs under `/api/v1/email`.
- Added a local encrypted credential-file store for the single Gmail account MVP.
- Added Gmail connector/service code for live thread reads and label mutation.
- Removed local email business models, repositories, schemas, seed data, and link summaries.
- Added migration cleanup for old local email tables.

## Frontend

- Replaced the Email placeholder with a Gmail-like read/link page.
- Supports all-thread view, Gmail search, Gmail label filtering, Campaign filtering, and Deal filtering.
- Supports linking/unlinking the selected thread through Gmail labels.
- Campaign and Deal pages route to `/email` with `campaignId` and `dealId` query parameters.

## Verification

- Backend tests cover no local email tables, encrypted credential persistence, Gmail label linking,
  and campaign label filtering with a fake Gmail connector.
- Frontend type/build checks should cover the new Email page and API types.
